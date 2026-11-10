from __future__ import annotations

import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures/band_geometry/source/drummerbg.png"
XMODEL = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
POSE_SPEC = ROOT / "fixtures/band_geometry/drummer_v3_pose_spec.json"

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
TARGET_TO_ZONE = {
    "HX_SNOWMAN_DRUMMER_V3_KICK": "KICK",
    "HX_SNOWMAN_DRUMMER_V3_SNARE": "SNARE",
    "HX_SNOWMAN_DRUMMER_V3_HI_HAT": "HI_HAT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH": "TOM_HIGH",
    "HX_SNOWMAN_DRUMMER_V3_TOM_MID": "TOM_MID",
    "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR": "TOM_FLOOR",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT": "CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT": "CYMBAL_RIGHT",
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


def _scaled_width(command, size):
    return max(1, round(float(command.get("width", 0.01)) * min(size)))


def _zone_mask(size: tuple[int, int], zone: dict) -> Image.Image:
    """Build a filled lighting mask from the canonical authored component zone.

    The pose spec is the same source used to author the V3 xmodel zones. We use
    it only as a mask over the real drummer background -- never as replacement
    artwork or a skeleton overlay.
    """
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for command in zone.get("commands", []):
        shape = command.get("shape")
        alpha = int(command.get("rgba", [255, 255, 255, 220])[3])
        if shape == "ellipse":
            box = tuple(round(float(v) * (width if i % 2 == 0 else height)) for i, v in enumerate(command["box"]))
            draw.ellipse(box, fill=alpha)
        elif shape == "ellipse_outline":
            box = tuple(round(float(v) * (width if i % 2 == 0 else height)) for i, v in enumerate(command["box"]))
            # Cymbals/hats are authored as outlines; fill the actual component
            # interior at low strength so the hardware itself lights, not a ring.
            draw.ellipse(box, fill=max(70, alpha // 3))
            draw.ellipse(box, outline=alpha, width=max(3, _scaled_width(command, size) * 4))
        elif shape == "rectangle_outline":
            box = tuple(round(float(v) * (width if i % 2 == 0 else height)) for i, v in enumerate(command["box"]))
            draw.rectangle(box, fill=max(50, alpha // 4), outline=alpha, width=max(3, _scaled_width(command, size) * 3))
        elif shape == "line":
            pts = command["points"]
            xy = [round(float(pts[i]) * (width if i % 2 == 0 else height)) for i in range(4)]
            draw.line(tuple(xy), fill=alpha, width=max(3, _scaled_width(command, size) * 4))
    return mask


def load_component_masks() -> tuple[Image.Image, dict[str, Image.Image]]:
    if not SOURCE.exists():
        raise SystemExit(f"FAIL: canonical drummer source image missing: {SOURCE}")
    if not XMODEL.exists():
        raise SystemExit(f"FAIL: canonical drummer xmodel missing: {XMODEL}")
    if not POSE_SPEC.exists():
        raise SystemExit(f"FAIL: canonical V3 pose spec missing: {POSE_SPEC}")

    source = Image.open(SOURCE).convert("RGBA")
    root = ET.parse(XMODEL).getroot()
    xmodel_names = {sm.get("name", "") for sm in root.findall("./subModels/subModel")}
    missing = set(TARGETS) - xmodel_names
    if missing:
        raise SystemExit(f"FAIL: xmodel missing canonical drummer submodels: {sorted(missing)}")

    spec = json.loads(POSE_SPEC.read_text(encoding="utf-8"))
    zones = {str(z["id"]): z for z in spec.get("zones", [])}
    masks = {}
    for target, zone_id in TARGET_TO_ZONE.items():
        if zone_id not in zones:
            raise SystemExit(f"FAIL: canonical V3 pose zone missing: {zone_id}")
        masks[target] = _zone_mask(source.size, zones[zone_id])
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
                ))
    return sorted(out)


def light_component(base: Image.Image, mask: Image.Image, intensity: float) -> Image.Image:
    if intensity <= 0.02:
        return base
    intensity = max(0.0, min(1.0, intensity))
    core = mask.point(lambda a: int(a * intensity))
    glow = core.filter(ImageFilter.GaussianBlur(max(4, base.width // 160)))

    # Illuminate the actual pixels of the canonical drummer. This is deliberately
    # not an outline/skeleton overlay. The component gets a bloom plus a bright
    # core while the underlying artwork remains visible.
    bloom = Image.new("RGBA", base.size, (255, 220, 75, 0))
    bloom.putalpha(glow.point(lambda a: int(a * 0.55)))
    out = Image.alpha_composite(base, bloom)

    bright = ImageEnhance.Brightness(out.convert("RGB")).enhance(1.0 + 0.75 * intensity)
    out = bright.convert("RGBA")
    core_layer = Image.new("RGBA", base.size, (255, 250, 150, 0))
    core_layer.putalpha(core.point(lambda a: int(a * 0.70)))
    return Image.alpha_composite(out, core_layer)


def draw_frame(source, masks, active, width, height, t_ms, duration_ms, font):
    # Keep the source aspect ratio. Previous versions resized a 96x72 xmodel mask
    # independently of the source artwork, causing component highlights to drift.
    scale = min(width / source.width, height / source.height)
    size = (max(1, round(source.width * scale)), max(1, round(source.height * scale)))
    base = source.resize(size, Image.Resampling.LANCZOS)

    for target, intensity in active.items():
        if intensity <= 0.02:
            continue
        mask = masks[target].resize(size, Image.Resampling.BILINEAR)
        base = light_component(base, mask, intensity)

    canvas = Image.new("RGBA", (width, height), (4, 7, 12, 255))
    x = (width - base.width) // 2
    y = (height - base.height) // 2
    canvas.alpha_composite(base, (x, y))

    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((18, 16, width - 18, 88), radius=12, fill=(5, 9, 16, 205), outline=(120, 140, 170, 210), width=2)
    active_names = [LABELS.get(t, t) for t, v in active.items() if v > 0.02]
    d.text((34, 30), "HELIX — CANONICAL DRUMMER V3", font=font, fill=(245, 248, 255, 255))
    d.text((34, 53), "LIGHTING: " + (", ".join(active_names) if active_names else "idle"), font=font, fill=(255, 215, 150, 255))
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

    source, masks = load_component_masks()
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
    print(f"CANONICAL-COMPONENT-LIGHT MODE: source={SOURCE} effects={len(effects)} targets={sorted(found)} audio_duration_ms={audio_duration_ms}")

    out = args.output
    silent = out.with_suffix(".silent.mp4")
    font = ImageFont.load_default()
    writer = imageio.get_writer(silent, fps=args.fps, codec="libx264", quality=8, macro_block_size=None)
    try:
        for i in range(int(duration_ms / 1000 * args.fps)):
            t = int(i * 1000 / args.fps)
            active = {name: 0.0 for name in TARGETS}
            for start, end, name in effects:
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
    print(f"PASS: canonical component-light MP4 effects={len(effects)} duration_ms={duration_ms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
