#!/usr/bin/env python3
"""Composite Helix layout-bench sequences into labeled multi-panel videos.

Each panel is drawn from an FSEQ rendered by xLights --headless. Node colors are
the rendered channel values, not a timing-only approximation. Audio is muxed
once per comparison. Videos are artifacts and are not committed.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.layout_bench.xlights_fseq import (  # noqa: E402
    build_node_drawlist,
    load_fseq,
    model_channel_report,
    render_sequence_to_fseq,
)


MANIFEST_PATH = ROOT / "fixtures" / "layout_bench" / "manifest.json"
PANEL_W = 480
PANEL_H = 270
HEADER_H = 36


def load_manifest() -> dict[str, dict]:
    rows = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {row["id"]: row for row in rows}


def find_xsq(run_root: Path, layout_id: str, audio_stem: str) -> Path:
    folder = run_root / layout_id
    matches = [path for path in folder.glob(f"{audio_stem},*.xsq") if "orchestrated" not in path.name]
    if not matches:
        raise FileNotFoundError(f"No canonical XSQ for {layout_id} / {audio_stem} under {folder}")
    matches.sort(key=lambda path: (path.name.count("("), len(path.name), path.name))
    return matches[0]


def raster_layout(layout_path: Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Paint each leaf model into a label image and a matching RGB color table."""
    layout = parse_models(layout_path)
    labels = np.full((PANEL_H, PANEL_W), -1, dtype=np.int16)
    names = sorted(layout.leaf_models)
    if not names:
        colors = np.zeros((1, 3), dtype=np.uint8)
        return labels, colors, names
    min_x, min_y, max_x, max_y = layout.bounds
    span_x = max(1.0, max_x - min_x)
    span_y = max(1.0, max_y - min_y)
    margin = 8
    draw_w = PANEL_W - margin * 2
    draw_h = PANEL_H - HEADER_H - margin
    scale = min(draw_w / span_x, draw_h / span_y)
    offset_x = margin + (draw_w - span_x * scale) / 2.0
    offset_y = HEADER_H + (draw_h - span_y * scale) / 2.0

    def project(x: float, y: float) -> tuple[int, int]:
        px = int(round(offset_x + (x - min_x) * scale))
        py = int(round(offset_y + (max_y - y) * scale))
        return px, py

    colors = np.zeros((len(names), 3), dtype=np.uint8)
    for index, name in enumerate(names):
        geom = layout.leaf_models[name]
        colors[index] = np.array(geom.color, dtype=np.uint8)
        points = [project(x, y) for x, y in geom.points]
        if len(points) < 2:
            points = points * 2
        stamp_polyline(labels, points, index, radius=2 if len(points) > 8 else 3)
    return labels, colors, names


def stamp_polyline(labels: np.ndarray, points: list[tuple[int, int]], index: int, radius: int) -> None:
    height, width = labels.shape
    disks = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius + 0.2:
                disks.append((dx, dy))
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for step in range(steps + 1):
            x = int(round(x1 + (x2 - x1) * step / steps))
            y = int(round(y1 + (y2 - y1) * step / steps))
            for dx, dy in disks:
                xx = x + dx
                yy = y + dy
                if 0 <= xx < width and 0 <= yy < height:
                    labels[yy, xx] = index


def render_panel_frame(
    labels: np.ndarray,
    colors: np.ndarray,
    intensity: np.ndarray,
    title: str,
    subtitle: str,
) -> np.ndarray:
    frame = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
    frame[:, :] = (8, 14, 28)
    active = labels >= 0
    if colors.size and np.any(active):
        chosen = labels[active]
        level = np.clip(intensity[chosen], 0.0, 1.0)
        base = colors[chosen].astype(np.float32)
        dim = base * 0.10
        lit = dim + (base * (0.35 + 0.65 * level[:, None]) + np.array([30, 40, 55]) * level[:, None])
        frame[active] = np.clip(lit, 0, 255).astype(np.uint8)
    image = Image.fromarray(frame, mode="RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, PANEL_W, HEADER_H), fill=(6, 10, 18))
    draw.text((8, 4), title, fill=(245, 248, 255))
    draw.text((8, 18), subtitle, fill=(150, 196, 230))
    return np.asarray(image)



def grid_shape(count: int) -> tuple[int, int]:
    if count == 16:
        return 4, 4
    if count == 12:
        return 4, 3
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    return cols, rows


def _ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def _stamp(image: np.ndarray, x: int, y: int, color: tuple[int, int, int], radius: int) -> None:
    height, width = image.shape[:2]
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > radius * radius:
                continue
            xx = x + dx
            yy = y + dy
            if 0 <= xx < width and 0 <= yy < height:
                image[yy, xx] = color


def _blend(level: int, color: tuple[int, int, int]) -> tuple[int, int, int]:
    if level <= 0:
        return (18, 22, 32)
    scale = level / 255.0
    return tuple(min(255, int(channel * scale)) for channel in color)  # type: ignore[return-value]


def paint_fseq_frame(drawlist: dict, row: np.ndarray, sparse_start: int, title: str, subtitle: str) -> np.ndarray:
    image = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
    image[:, :] = (8, 14, 28)
    for _name, points, color, origin in drawlist["strands"]:
        channel = origin - sparse_start
        level = int(row[channel]) if 0 <= channel < row.shape[0] else 0
        rgb = _blend(level, color)
        radius = 3 if level else 1
        for x, y in points:
            _stamp(image, x, y, rgb, radius)
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            for step in range(steps + 1):
                x = int(round(x1 + (x2 - x1) * step / steps))
                y = int(round(y1 + (y2 - y1) * step / steps))
                _stamp(image, x, y, rgb, radius)
    for (x, y), channel, is_rgb, color in zip(drawlist["xy"], drawlist["ch"], drawlist["rgb"], drawlist["color"]):
        index = channel - sparse_start
        if is_rgb:
            if index < 0 or index + 2 >= row.shape[0]:
                continue
            rgb = (int(row[index]), int(row[index + 1]), int(row[index + 2]))
            if rgb == (0, 0, 0):
                rgb = (18, 22, 32)
            radius = 2 if max(rgb) > 30 else 1
        else:
            if index < 0 or index >= row.shape[0]:
                continue
            level = int(row[index])
            rgb = _blend(level, color)
            radius = 2 if level else 1
        _stamp(image, x, y, rgb, radius)
    picture = Image.fromarray(image, mode="RGB")
    draw = ImageDraw.Draw(picture)
    draw.rectangle((0, 0, PANEL_W, HEADER_H), fill=(6, 10, 18))
    draw.text((8, 4), title, fill=(245, 248, 255))
    draw.text((8, 18), subtitle, fill=(150, 210, 170))
    return np.asarray(picture)


def write_panel_mp4(panel: dict, out_path: Path) -> dict:
    fseq = load_fseq(panel["fseq"])
    report = model_channel_report(panel["layout"], fseq)
    if out_path.exists() and out_path.stat().st_size > 10000:
        return {"fps": fseq.fps(), "report": report}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    drawlist = build_node_drawlist(panel["layout"], PANEL_W, PANEL_H, HEADER_H)
    silent = out_path.with_suffix(".silent.mp4")
    cmd = [
        _ffmpeg(),
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{PANEL_W}x{PANEL_H}",
        "-r", str(fseq.fps()),
        "-i", "-",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        str(silent),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    subtitle = f"{panel['channels']} ch · xLights FSEQ {fseq.step_ms} ms"
    try:
        for frame_idx in range(fseq.frames):
            frame = paint_fseq_frame(drawlist, fseq.samples[frame_idx], fseq.sparse_start, panel["title"], subtitle)
            proc.stdin.write(frame.tobytes())
    finally:
        proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"panel encode failed for {out_path.name}: {stderr[-600:]}")
    silent.replace(out_path)
    return {"fps": fseq.fps(), "report": report}


def stitch_panels(panel_paths: list[Path], audio_path: Path, out_path: Path, title: str, description: str) -> None:
    cols, _rows = grid_shape(len(panel_paths))
    width = cols * PANEL_W
    banner = Image.new("RGB", (width, 48), (4, 8, 16))
    draw = ImageDraw.Draw(banner)
    draw.text((12, 4), title, fill=(245, 248, 255))
    draw.text((12, 24), description[:180], fill=(160, 190, 220))
    banner_path = out_path.with_suffix(".banner.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    banner.save(banner_path)
    layout_expr = "|".join(f"{(index % cols) * PANEL_W}_{(index // cols) * PANEL_H}" for index in range(len(panel_paths)))
    cmd = [_ffmpeg(), "-y", "-i", str(banner_path)]
    for path in panel_paths:
        cmd.extend(["-i", str(path)])
    cmd.extend(["-i", str(audio_path)])
    stack = "".join(f"[{index + 1}:v]" for index in range(len(panel_paths)))
    audio_index = len(panel_paths) + 1
    filter_complex = (
        f"{stack}xstack=inputs={len(panel_paths)}:layout={layout_expr}[grid];"
        f"[0:v][grid]vstack=inputs=2[v]"
    )
    cmd.extend(
        [
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", f"{audio_index}:a:0",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "20",
            "-c:a", "aac",
            "-shortest",
            str(out_path),
        ]
    )
    completed = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace")[-800:])
    banner_path.unlink(missing_ok=True)


SONG_META = {
    "north_pole_overdrive": ("NPO", "North Pole Overdrive"),
    "wub_wub_wonderland": ("WWW", "Wub Wub Wonderland"),
    "candy_cane_chaos": ("CCC", "Candy Cane Chaos"),
    "clip_b": ("CLB", "Untitled clip B"),
    "clip_c": ("CLC", "Untitled clip C"),
    "clip_f": ("CLF", "Untitled clip F"),
    "clip_g": ("CLG", "Untitled clip G"),
}

ALL16 = [
    "ac16_lor", "ac32_house", "ac64_yard",
    "pixel_starter", "pixel_classic", "pixel_driveway", "pixel_windows", "pixel_corner",
    "band_stage",
    "wow_spirals", "wow_helix", "wow_tunnel", "wow_spinners", "wow_moire", "wow_mirror", "wow_showcase",
]
SIMPLE12 = [
    "ac16_lor", "ac32_house", "ac64_yard",
    "pixel_starter", "pixel_classic", "pixel_driveway", "pixel_windows", "pixel_corner",
    "band_stage",
    "wow_spirals", "wow_helix", "wow_tunnel",
]
WOW12 = [
    "ac16_lor", "ac32_house", "ac64_yard",
    "band_stage", "pixel_classic",
    "wow_spirals", "wow_helix", "wow_tunnel", "wow_spinners", "wow_moire", "wow_mirror", "wow_showcase",
]


def song_catalog(audio_dir: Path) -> dict[str, dict]:
    found = {}
    for path in audio_dir.glob("*.mp3"):
        if path.stem in SONG_META:
            code, label = SONG_META[path.stem]
            found[path.stem] = {"path": path, "stem": path.stem, "code": code, "label": label}
    return found


def variant_plan(songs: dict[str, dict]) -> list[dict]:
    """Distinct comparison videos. Every grid includes the AC yards and the band stage."""
    specs = [
        ("V01-NPO-ALL16", "north_pole_overdrive", "ALL16", "16-panel grid of every layout", ALL16),
        ("V02-WWW-ALL16", "wub_wub_wonderland", "ALL16", "16-panel grid of every layout", ALL16),
        ("V03-CCC-ALL16", "candy_cane_chaos", "ALL16", "16-panel grid of every layout", ALL16),
        ("V04-CLB-ALL16", "clip_b", "ALL16", "16-panel grid of every layout", ALL16),
        ("V05-CLC-SIMPLE12", "clip_c", "SIMPLE12", "12-panel simple-to-mid grid plus the first wow props", SIMPLE12),
        ("V06-CLF-WOW12", "clip_f", "WOW12", "12-panel wow grid with the AC yards and the band stage", WOW12),
        ("V07-CLG-ALL16", "clip_g", "ALL16", "16-panel grid of every layout", ALL16),
        ("V08-NPO-SIMPLE12", "north_pole_overdrive", "SIMPLE12", "12-panel simple-to-mid grid plus the first wow props", SIMPLE12),
        ("V09-WWW-WOW12", "wub_wub_wonderland", "WOW12", "12-panel wow grid with the AC yards and the band stage", WOW12),
        ("V10-CCC-SIMPLE12", "candy_cane_chaos", "SIMPLE12", "12-panel simple-to-mid grid plus the first wow props", SIMPLE12),
    ]
    plans = []
    for variant_id, stem, _code, grid_desc, layout_ids in specs:
        song = songs[stem]
        plans.append(
            {
                "id": variant_id,
                "description": f"{song['label']}: {grid_desc}, synced to the same audio.",
                "song": song,
                "layout_ids": layout_ids,
            }
        )
    return plans


def _fseq_path(run_root: Path, layout_id: str, stem: str) -> Path:
    return run_root / "fseq" / layout_id / f"{stem}.fseq"


def ensure_fseq(run_root: Path, layout_id: str, layout_xml: Path, xsq: Path, media: Path) -> str:
    fseq = _fseq_path(run_root, layout_id, media.stem)
    show = run_root / "xlights_show" / layout_id / media.stem
    print(f"xLights FSEQ {layout_id} {media.stem}", flush=True)
    version = render_sequence_to_fseq(
        layout_xml=layout_xml,
        xsq_path=xsq,
        media_path=media,
        fseq_path=fseq,
        show_dir=show,
    )
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description="Render xLights FSEQ comparison videos for the layout bench.")
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=ROOT / "test_runs" / "layout_bench")
    parser.add_argument("--output-dir", type=Path, default=Path("/opt/cursor/artifacts/layout_bench_rendered"))
    parser.add_argument("--only", nargs="*", help="Variant ids to render.")
    args = parser.parse_args()
    manifest = load_manifest()
    songs = song_catalog(args.audio_dir)
    plans = variant_plan(songs)
    if args.only:
        wanted = set(args.only)
        plans = [plan for plan in plans if plan["id"] in wanted]
    needed: list[tuple[str, Path]] = []
    seen: set[tuple[str, str]] = set()
    for plan in plans:
        for layout_id in plan["layout_ids"]:
            key = (layout_id, plan["song"]["stem"])
            if key in seen:
                continue
            seen.add(key)
            needed.append((layout_id, plan["song"]["path"]))
    versions: set[str] = set()
    for layout_id, media in needed:
        entry = manifest[layout_id]
        xsq = find_xsq(args.run_root, layout_id, media.stem)
        version = ensure_fseq(args.run_root, layout_id, ROOT / entry["layout"], xsq, media)
        if version != "cached":
            versions.add(version)
    panel_dir = args.run_root / "panels_fseq"
    catalog = []
    sanity: dict[str, list[dict]] = {}
    for plan in plans:
        panel_paths = []
        for layout_id in plan["layout_ids"]:
            entry = manifest[layout_id]
            panel = {
                "layout_id": layout_id,
                "title": entry["title"],
                "channels": entry["channels"],
                "pixels": entry["pixels"],
                "layout": ROOT / entry["layout"],
                "xsq": find_xsq(args.run_root, layout_id, plan["song"]["stem"]),
                "fseq": _fseq_path(args.run_root, layout_id, plan["song"]["stem"]),
            }
            panel_path = panel_dir / f"{layout_id}__{plan['song']['stem']}.mp4"
            print(f"Panel {layout_id} {plan['song']['stem']}", flush=True)
            painted = write_panel_mp4(panel, panel_path)
            sanity.setdefault(layout_id, [])
            if painted["report"] and not sanity[layout_id]:
                sanity[layout_id] = painted["report"]
            panel_paths.append(panel_path)
        out_path = args.output_dir / f"{plan['id'].lower().replace('-', '_')}.mp4"
        banner = f"{plan['id']}  {plan['song']['label']}  ·  xLights FSEQ render"
        print(f"Stitching {plan['id']} -> {out_path}", flush=True)
        stitch_panels(panel_paths, plan["song"]["path"], out_path, banner, plan["description"])
        catalog.append(
            {
                "id": plan["id"],
                "description": plan["description"] + " Drawn from xLights FSEQ channel data.",
                "path": str(out_path),
                "layouts": plan["layout_ids"],
                "song": plan["song"]["label"],
                "source": "xlights-fseq",
            }
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "variants.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "xlights_version.txt").write_text("\n".join(sorted(versions)) + "\n", encoding="utf-8")
    (args.run_root / "fseq_model_report.json").write_text(json.dumps(sanity, indent=2) + "\n", encoding="utf-8")
    repo_catalog = ROOT / "fixtures" / "layout_bench" / "variants.json"
    repo_rows = [{key: value for key, value in row.items() if key != "path"} for row in catalog]
    repo_catalog.write_text(json.dumps(repo_rows, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
