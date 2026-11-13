#!/usr/bin/env python3
"""Render showcase12 comparison videos from real xLights FSEQ data."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.showcase12.xlights_fseq import (
    build_node_drawlist,
    load_fseq,
    render_sequence_to_fseq,
)

MANIFEST = ROOT / "fixtures" / "showcase12" / "manifest.json"
PANEL_W = 400
PANEL_H = 288
HEADER_H = 28
COLS = 4


SONGS = {
    "north_pole_overdrive": ("S1-NPO", "North Pole Overdrive"),
    "candy_cane_chaos": ("S2-CCC", "Candy Cane Chaos"),
    "wub_wub_wonderland": ("S3-WWW", "Wub Wub Wonderland"),
    "clip_b": ("S4-CLB", "Untitled clip B"),
}


def find_xsq(run_root: Path, layout_id: str, stem: str) -> Path:
    folder = run_root / layout_id
    matches = [path for path in folder.glob(f"{stem},*.xsq") if "orchestrated" not in path.name]
    if not matches:
        raise FileNotFoundError(f"No XSQ for {layout_id} / {stem}")
    matches.sort(key=lambda path: (path.name.count("("), len(path.name), path.name))
    return matches[0]


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


_HOUSE_FILL = {
    "ground": (14, 22, 18),
    "drive": (18, 20, 24),
    "wall": (28, 32, 40),
    "roof": (18, 20, 28),
    "opening": (10, 12, 18),
    "stage": (32, 28, 26),
}


def paint_frame(drawlist, row, sparse_start, title) -> np.ndarray:
    image = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
    image[:, :] = (6, 10, 18)
    picture = Image.fromarray(image, mode="RGB")
    draw = ImageDraw.Draw(picture)
    for kind, pts in drawlist.get("house", []):
        if len(pts) >= 3:
            draw.polygon(pts, fill=_HOUSE_FILL.get(kind, _HOUSE_FILL["wall"]))
    image = np.array(picture)

    def stamp(x, y, rgb, radius):
        for dy in range(-radius, radius + 1):
            yy = y + dy
            if yy < HEADER_H or yy >= PANEL_H:
                continue
            for dx in range(-radius, radius + 1):
                xx = x + dx
                if 0 <= xx < PANEL_W:
                    image[yy, xx] = rgb
    for (x, y), channel, is_rgb, color in zip(drawlist["xy"], drawlist["ch"], drawlist["rgb"], drawlist["color"]):
        index = channel - sparse_start
        if is_rgb:
            if index < 0 or index + 2 >= row.shape[0]:
                continue
            rgb = (int(row[index]), int(row[index + 1]), int(row[index + 2]))
            if rgb == (0, 0, 0):
                rgb = (16, 20, 28)
            radius = 2 if max(rgb) > 28 else 1
        else:
            if index < 0 or index >= row.shape[0]:
                continue
            level = int(row[index])
            scale = level / 255.0
            rgb = tuple(int(channel * scale) for channel in color)
            if rgb == (0, 0, 0):
                rgb = (16, 20, 28)
            radius = 2 if level else 1
        stamp(x, y, rgb, radius)
    for name, points, color, origin in drawlist["strands"]:
        del name
        if not points:
            continue
        level = int(row[origin - sparse_start]) if 0 <= origin - sparse_start < row.shape[0] else 0
        scale = level / 255.0
        rgb = tuple(int(channel * scale) for channel in color) if level else (16, 20, 28)
        for x, y in points:
            stamp(x, y, rgb, 2)
    picture = Image.fromarray(image, mode="RGB")
    draw = ImageDraw.Draw(picture)
    draw.rectangle((0, 0, PANEL_W, HEADER_H), fill=(6, 10, 18))
    draw.text((6, 6), title[:42], fill=(236, 242, 255))
    return np.asarray(picture)


def write_panel(panel: dict, out_path: Path) -> None:
    if out_path.exists() and out_path.stat().st_size > 8000:
        return
    fseq = load_fseq(panel["fseq"])
    drawlist = build_node_drawlist(panel["layout"], PANEL_W, PANEL_H, HEADER_H)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    silent = out_path.with_suffix(".silent.mp4")
    cmd = [
        _ffmpeg(), "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{PANEL_W}x{PANEL_H}", "-r", str(fseq.fps()),
        "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28",
        str(silent),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for frame_idx in range(fseq.frames):
            frame = paint_frame(drawlist, fseq.samples[frame_idx], fseq.sparse_start, panel["title"])
            proc.stdin.write(frame.tobytes())
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        code = proc.wait()
    if code != 0:
        raise RuntimeError(err[-500:])
    silent.replace(out_path)


def stitch(panel_paths, audio, out_path, title, description) -> None:
    width = COLS * PANEL_W
    banner = Image.new("RGB", (width, 36), (4, 8, 16))
    draw = ImageDraw.Draw(banner)
    draw.text((8, 2), title, fill=(245, 248, 255))
    draw.text((8, 18), description[:110], fill=(170, 198, 220))
    banner_path = out_path.with_suffix(".banner.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    banner.save(banner_path)
    layout_expr = "|".join(f"{(i % COLS) * PANEL_W}_{(i // COLS) * PANEL_H}" for i in range(len(panel_paths)))
    cmd = [_ffmpeg(), "-y", "-i", str(banner_path)]
    for path in panel_paths:
        cmd.extend(["-i", str(path)])
    cmd.extend(["-i", str(audio)])
    stack = "".join(f"[{i + 1}:v]" for i in range(len(panel_paths)))
    audio_index = len(panel_paths) + 1
    filt = f"{stack}xstack=inputs={len(panel_paths)}:layout={layout_expr}[grid];[0:v][grid]vstack=inputs=2[v]"
    cmd.extend([
        "-filter_complex", filt,
        "-map", "[v]", "-map", f"{audio_index}:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28",
        "-c:a", "aac", "-b:a", "96k", "-shortest",
        str(out_path),
    ])
    completed = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace")[-800:])
    banner_path.unlink(missing_ok=True)


def palette_diversity(xsq_path: Path) -> dict:
    root = ET.parse(xsq_path).getroot()
    tables = []
    for element in root.iter():
        if str(element.tag).endswith("ColorPalettes"):
            tables = [child.text or "" for child in list(element)]
            break
    used = set()
    for effect in root.iter("Effect"):
        palette = (effect.attrib.get("palette") or "").strip()
        if palette.isdigit() and int(palette) < len(tables):
            used.add(tables[int(palette)])
    return {"palette_rows": len(tables), "used_rows": len(used)}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=ROOT / "test_runs" / "showcase12")
    parser.add_argument("--output-dir", type=Path, default=Path("/opt/cursor/artifacts/showcase12"))
    args = parser.parse_args()
    os.environ.setdefault("XLIGHTS_BIN", "/tmp/xlights/squashfs-root/AppRun")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in manifest}
    order = [entry["id"] for entry in manifest]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for stem, (variant_id, label) in SONGS.items():
        audio = args.audio_dir / f"{stem}.wav"
        if not audio.exists():
            print(f"skip missing {audio}")
            continue
        panel_paths = []
        for layout_id in order:
            entry = by_id[layout_id]
            xsq = find_xsq(args.run_root, layout_id, stem)
            fseq = args.run_root / "fseq" / layout_id / f"{stem}.fseq"
            show = args.run_root / "xlights_show" / layout_id / stem
            print(f"FSEQ {variant_id} {layout_id}", flush=True)
            render_sequence_to_fseq(
                layout_xml=ROOT / entry["layout"],
                xsq_path=xsq,
                media_path=audio,
                fseq_path=fseq,
                show_dir=show,
            )
            panel = {
                "title": entry["title"],
                "layout": ROOT / entry["layout"],
                "fseq": fseq,
            }
            panel_path = args.run_root / "panels" / f"{layout_id}__{stem}.mp4"
            print(f"Panel {layout_id}", flush=True)
            write_panel(panel, panel_path)
            panel_paths.append(panel_path)
        out = args.output_dir / f"{variant_id.lower().replace('-', '_')}.mp4"
        print(f"Stitch {variant_id} -> {out}", flush=True)
        stitch(
            panel_paths,
            audio,
            out,
            f"{variant_id}  {label}",
            "12 panels, simplest LOR yard through the snowman band. Real xLights FSEQ.",
        )
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
