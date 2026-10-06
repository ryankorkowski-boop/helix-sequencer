from __future__ import annotations

import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures/band_geometry/source/drummerbg.png"
XMODEL = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
MANIFEST = ROOT / "fixtures/band_geometry/drummer_v3_png_layer_manifest.json"

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
    "HX_SNOWMAN_DRUMMER_V3_KICK": "KICK",
    "HX_SNOWMAN_DRUMMER_V3_SNARE": "SNARE",
    "HX_SNOWMAN_DRUMMER_V3_HI_HAT": "HI-HAT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH": "TOM HIGH",
    "HX_SNOWMAN_DRUMMER_V3_TOM_MID": "TOM MID",
    "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR": "TOM FLOOR",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT": "CRASH L",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT": "CRASH R",
}


def _expand_ranges(text: str) -> set[int]:
    nodes: set[int] = set()
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            nodes.update(range(int(a), int(b) + 1))
        else:
            nodes.add(int(token))
    return nodes


def load_xmodel_masks() -> tuple[Image.Image, dict[str, Image.Image]]:
    if not SOURCE.exists():
        raise SystemExit(f"FAIL: canonical drummer source image missing: {SOURCE}")
    if not XMODEL.exists():
        raise SystemExit(f"FAIL: canonical drummer xmodel missing: {XMODEL}")

    source = Image.open(SOURCE).convert("RGBA")
    root = ET.parse(XMODEL).getroot()
    width = int(root.get("parm1", "96"))
    height = int(root.get("parm2", "72"))
    masks: dict[str, Image.Image] = {}

    for submodel in root.findall("./subModels/subModel"):
        name = submodel.get("name", "")
        if name not in TARGETS:
            continue
        nodes = _expand_ranges(submodel.get("line0", ""))
        mask = Image.new("L", (width, height), 0)
        px = mask.load()
        for node in nodes:
            # build_drummer_v3_assets.py defines node IDs as y*width+x+1.
            zero = node - 1
            if 0 <= zero < width * height:
                x = zero % width
                y = zero // width
                px[x, y] = 255
        masks[name] = mask

    missing = set(TARGETS) - set(masks)
    if missing:
        raise SystemExit(f"FAIL: xmodel missing canonical drummer submodels: {sorted(missing)}")
    if source.width <= 0 or source.height <= 0:
        raise SystemExit("FAIL: canonical drummer source image has invalid dimensions")
    return source, masks


def parse_effects(xsq: Path):
    root = ET.parse(xsq).getroot()
    out = []
    for element in root.findall("./ElementEffects/Element"):
        name = element.get("name", "")
        if name not in TARGETS:
            continue
        for layer in element.findall("EffectLayer"):
            for fx in layer.findall("Effect"):
                out.append((
                    int(float(fx.get("startTime", "0"))),
                    int(float(fx.get("endTime", "0"))),
                    name,
                    fx.get("sourcePoseSubmodel", ""),
                ))
    return sorted(out)


def _mask_to_source(mask: Image.Image, source_size: tuple[int, int]) -> Image.Image:
    return mask.resize(source_size, Image.Resampling.NEAREST)


def draw_frame(source, masks, active, width, height, t_ms, duration_ms, font):
    base = source.copy()
    base.thumbnail((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (width, height), (4, 7, 12, 255))
    x = (width - base.width) // 2
    y = (height - base.height) // 2
    canvas.alpha_composite(base, (x, y))

    for target, intensity in active.items():
        if intensity <= 0.02:
            continue
        mask = _mask_to_source(masks[target], base.size)
        # The xmodel mask is the authoritative physical component geometry. Draw
        # the hit directly on those nodes; do not use the old illustrative/skeleton
        # PNG overlays, which can be visually offset from the actual xmodel zones.
        glow = mask.filter(ImageFilter.GaussianBlur(max(2, base.width // 180)))
        glow_alpha = glow.point(lambda a: int(a * min(1.0, intensity) * 0.72))
        glow_layer = Image.new("RGBA", base.size, (255, 225, 70, 0))
        glow_layer.putalpha(glow_alpha)
        canvas.alpha_composite(glow_layer, (x, y))

        hit_alpha = mask.point(lambda a: int(a * min(1.0, intensity)))
        hit_layer = Image.new("RGBA", base.size, (255, 250, 135, 0))
        hit_layer.putalpha(hit_alpha)
        canvas.alpha_composite(hit_layer, (x, y))

    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((18, 16, width - 18, 88), radius=12, fill=(5, 9, 16, 205), outline=(120, 140, 170, 210), width=2)
    active_names = [LABELS.get(t, t) for t, v in active.items() if v > 0.02]
    d.text((34, 30), "HELIX — CANONICAL DRUMMER V3 / XMODEL", font=font, fill=(245, 248, 255, 255))
    d.text((34, 53), "ACTIVE: " + (", ".join(active_names) if active_names else "idle"), font=font, fill=(255, 215, 150, 255))
    d.text((width - 190, 30), f"{t_ms/1000:.2f}s / {duration_ms/1000:.2f}s", font=font, fill=(190, 210, 235, 255))
    return canvas.convert("RGB")


def _audio_duration_ms(audio: Path) -> int:
    try:
        info = sf.info(str(audio))
        duration = float(info.frames) / float(info.samplerate)
        if duration > 0:
            return int(round(duration * 1000.0))
    except Exception as exc:
        raise RuntimeError(f"Unable to determine audio duration for {audio}: {exc}") from exc
    raise RuntimeError(f"Unable to determine audio duration for {audio}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq", type=Path)
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--duration", type=float, default=0.0)
    args = ap.parse_args()

    source, masks = load_xmodel_masks()
    effects = parse_effects(args.xsq)
    if not effects:
        raise SystemExit("FAIL: no canonical HX_SNOWMAN_DRUMMER_V3 submodel effects found")
    found = {e[2] for e in effects}
    missing_targets = set(TARGETS) - found
    if missing_targets:
        raise SystemExit(f"FAIL: XSQ missing canonical drummer targets: {sorted(missing_targets)}")

    audio_duration_ms = _audio_duration_ms(args.audio)
    effect_end_ms = max(e[1] for e in effects)
    if effect_end_ms < int(audio_duration_ms * 0.95):
        raise SystemExit(f"FAIL: drummer XSQ ends at {effect_end_ms} ms, but audio is {audio_duration_ms} ms")
    duration_ms = audio_duration_ms if args.duration <= 0 else min(int(args.duration * 1000), audio_duration_ms)
    print(f"XMODEL-GEOMETRY MODE: xmodel={XMODEL} effects={len(effects)} targets={sorted(found)} audio_duration_ms={audio_duration_ms}")

    out = args.output
    silent = out.with_suffix(".silent.mp4")
    font = ImageFont.load_default()
    writer = imageio.get_writer(silent, fps=args.fps, codec="libx264", quality=8, macro_block_size=None)
    try:
        for i in range(int(duration_ms / 1000 * args.fps)):
            t = int(i * 1000 / args.fps)
            active = {name: 0.0 for name in TARGETS}
            for start, end, name, _pose in effects:
                if start <= t < end:
                    active[name] = max(active[name], 1.0)
            writer.append_data(np.asarray(draw_frame(source, masks, active, 960, 540, t, duration_ms, font)))
    finally:
        writer.close()

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.run([ff, "-y", "-i", str(silent), "-i", str(args.audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-4000:])
    silent.unlink(missing_ok=True)
    if not out.exists() or out.stat().st_size < 10000:
        raise SystemExit("FAIL: canonical drummer MP4 missing/empty")
    print(f"PASS: canonical drummer V3 MP4 rendered from xmodel geometry; effects={len(effects)} duration_ms={duration_ms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
