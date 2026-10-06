from __future__ import annotations

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

from tools.drummer_v3_visual_masks import (
    exact_geometry,
    compose_emissive,
    load_spec,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures/band_geometry/source/drummerbg.png"
XMODEL = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"

TARGETS = (
    "HX_SNOWMAN_DRUMMER_V3_KICK",
    "HX_SNOWMAN_DRUMMER_V3_SNARE",
    "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH",
    "HX_SNOWMAN_DRUMMER_V3_TOM_MID",
    "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
)
LABELS = {
    TARGETS[0]: "KICK",
    TARGETS[1]: "SNARE",
    TARGETS[2]: "HI-HAT",
    TARGETS[3]: "TOM HIGH",
    TARGETS[4]: "TOM MID",
    TARGETS[5]: "TOM FLOOR",
    TARGETS[6]: "CRASH L",
    TARGETS[7]: "CRASH R",
}


def _expand_ranges(text: str) -> set[int]:
    nodes: set[int] = set()
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            start, end = int(a), int(b)
            if start > end:
                raise ValueError(f"Invalid xmodel node range: {token}")
            nodes.update(range(start, end + 1))
        else:
            nodes.add(int(token))
    return nodes


def validate_xmodel_targets(xmodel_path: Path = XMODEL) -> None:
    root = ET.parse(xmodel_path).getroot()
    width = int(root.get("parm1", "0"))
    height = int(root.get("parm2", "0"))
    if width <= 0 or height <= 0:
        raise ValueError("xmodel has invalid grid dimensions")
    maximum = width * height
    submodels = {sm.get("name", ""): sm.get("line0", "") for sm in root.findall("./subModels/subModel")}
    missing = set(TARGETS) - set(submodels)
    if missing:
        raise ValueError(f"xmodel missing canonical drummer submodels: {sorted(missing)}")
    for name in TARGETS:
        nodes = _expand_ranges(submodels[name])
        if not nodes:
            raise ValueError(f"xmodel submodel has no nodes: {name}")
        if min(nodes) < 1 or max(nodes) > maximum:
            raise ValueError(f"xmodel submodel has out-of-range nodes: {name}")


def load_component_masks(
    source_path: Path = SOURCE,
    xmodel_path: Path = XMODEL,
) -> tuple[Image.Image, dict[str, Image.Image]]:
    """Load full-resolution masks from the same authored spec that builds the xmodel."""
    if not source_path.exists():
        raise ValueError(f"canonical drummer source image missing: {source_path}")
    if not xmodel_path.exists():
        raise ValueError(f"canonical drummer xmodel missing: {xmodel_path}")
    validate_xmodel_targets(xmodel_path)
    source = Image.open(source_path).convert("RGBA")
    spec = load_spec()
    masks = exact_geometry(source, spec)["masks"]
    return source, masks


def compose_lighting(
    source: Image.Image,
    masks: dict[str, Image.Image],
    active_targets: tuple[str, ...] | list[str] | set[str],
) -> Image.Image:
    return compose_emissive(source, masks, active_targets)


def _content_crop(source: Image.Image) -> tuple[int, int, int, int]:
    gray = np.asarray(source.convert("L"))
    dark = gray < 90
    rows = np.flatnonzero(dark.sum(axis=1) > source.width * 0.35)
    cols = np.flatnonzero(dark.sum(axis=0) > source.height * 0.35)
    if len(rows) and len(cols):
        return int(cols[0]), int(rows[0]), int(cols[-1] + 1), int(rows[-1] + 1)
    bbox = source.convert("L").point(lambda v: 255 if v < 110 else 0).getbbox()
    return bbox or (0, 0, source.width, source.height)


def parse_effects(xsq: Path) -> list[tuple[int, int, str]]:
    root = ET.parse(xsq).getroot()
    out: list[tuple[int, int, str]] = []
    for element in root.findall("./ElementEffects/Element"):
        name = element.get("name", "")
        if name not in TARGETS:
            continue
        for layer in element.findall("EffectLayer"):
            for effect in layer.findall("Effect"):
                out.append((
                    int(float(effect.get("startTime", "0"))),
                    int(float(effect.get("endTime", "0"))),
                    name,
                ))
    return sorted(out)


def _frame_time_ms(start_ms: int, frame_index: int, fps: int) -> float:
    return float(start_ms) + (float(frame_index) * 1000.0 / float(fps))


def _active_targets_for_frame(
    effects: list[tuple[int, int, str]],
    frame_time_ms: float,
    fps: int,
) -> set[str]:
    """Sample effect intervals at the nearest video frame, not only after them."""
    half_frame_ms = 500.0 / float(fps)
    return {
        name
        for start, end, name in effects
        if start < frame_time_ms + half_frame_ms
        and end > frame_time_ms - half_frame_ms
    }


def draw_frame(
    source: Image.Image,
    masks: dict[str, Image.Image],
    active: set[str],
    width: int,
    height: int,
    t_ms: int,
    duration_ms: int,
    font: ImageFont.ImageFont,
    art_cache: dict[tuple[str, ...], Image.Image] | None = None,
) -> Image.Image:
    max_w, max_h = width - 250, height - 108
    key = tuple(target for target in TARGETS if target in active)
    art = art_cache.get(key) if art_cache is not None else None
    if art is None:
        lit = compose_lighting(source, masks, active)
        art = lit.crop(_content_crop(source))
        scale = min(max_w / art.width, max_h / art.height)
        size = (max(1, round(art.width * scale)), max(1, round(art.height * scale)))
        art = art.resize(size, Image.Resampling.LANCZOS)
        if art_cache is not None:
            art_cache[key] = art

    canvas = Image.new("RGBA", (width, height), (4, 7, 12, 255))
    x = (width - art.width) // 2
    y = 100 + max(0, (max_h - art.height) // 2)
    canvas.alpha_composite(art, (x, y))

    draw = ImageDraw.Draw(canvas)
    draw.text((24, 24), "HELIX — DRUMMER V3 COMPONENT LIGHTING", font=font, fill=(245, 248, 255, 255))
    hit_labels = [LABELS[target] for target in TARGETS if target in active]
    draw.text((24, 56), "HITS: " + (", ".join(hit_labels) if hit_labels else "IDLE"), font=font, fill=(255, 216, 150, 255))
    draw.text((width - 180, 24), f"{t_ms / 1000:.2f}s / {duration_ms / 1000:.2f}s", font=font, fill=(230, 235, 245, 255))
    return canvas.convert("RGB")


def _audio_duration_ms(audio: Path) -> int:
    try:
        info = sf.info(str(audio))
        if info.frames > 0 and info.samplerate > 0:
            return int(round((float(info.frames) / float(info.samplerate)) * 1000.0))
    except Exception:
        pass
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    probe = subprocess.run([ffmpeg, "-i", str(audio)], capture_output=True, text=True)
    line = next((line for line in probe.stderr.splitlines() if "Duration:" in line), None)
    if not line:
        raise RuntimeError(f"Unable to determine audio duration for {audio}")
    value = line.split("Duration:", 1)[1].split(",", 1)[0].strip()
    h, m, s = value.split(":")
    return int(round((int(h) * 3600 + int(m) * 60 + float(s)) * 1000))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("xsq", type=Path)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--duration", type=float, default=0.0)
    parser.add_argument("--start", type=float, default=0.0, help="First source-audio second to render")
    parser.add_argument("--require-all-targets", action="store_true")
    args = parser.parse_args()

    source, masks = load_component_masks()
    effects = parse_effects(args.xsq)
    if not effects:
        raise SystemExit("FAIL: no canonical HX_SNOWMAN_DRUMMER_V3 effects found")
    found = {event[2] for event in effects}
    missing = set(TARGETS) - found
    if args.require_all_targets and missing:
        raise SystemExit(f"FAIL: XSQ missing canonical drummer targets: {sorted(missing)}")

    audio_duration_ms = _audio_duration_ms(args.audio)
    start_ms = int(round(args.start * 1000))
    if args.fps <= 0 or start_ms < 0 or start_ms >= audio_duration_ms or args.duration < 0:
        raise SystemExit("Invalid fps/start/duration for audio")
    remaining_ms = audio_duration_ms - start_ms
    duration_ms = remaining_ms if args.duration == 0 else min(int(args.duration * 1000), remaining_ms)

    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    silent = output.with_suffix(".silent.mp4")
    font = ImageFont.load_default()
    writer = imageio.get_writer(silent, fps=args.fps, codec="libx264", quality=8, macro_block_size=None)
    art_cache: dict[tuple[str, ...], Image.Image] = {}
    try:
        frame_count = int(round(duration_ms / 1000 * args.fps))
        for index in range(frame_count):
            frame_time_ms = _frame_time_ms(start_ms, index, args.fps)
            active = _active_targets_for_frame(effects, frame_time_ms, args.fps)
            t_ms = int(round(frame_time_ms))
            writer.append_data(np.asarray(draw_frame(
                source, masks, active, 960, 540, t_ms, start_ms + duration_ms, font, art_cache
            )))
    finally:
        writer.close()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [ffmpeg, "-y", "-i", str(silent), "-ss", str(args.start), "-i", str(args.audio), "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(output)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr[-4000:])
    silent.unlink(missing_ok=True)
    if not output.exists() or output.stat().st_size < 10000:
        raise SystemExit("FAIL: canonical drummer MP4 missing/empty")
    print(
        f"PASS: full-resolution component lighting effects={len(effects)} "
        f"targets_seen={len(found)} duration_ms={duration_ms} fps={args.fps}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
