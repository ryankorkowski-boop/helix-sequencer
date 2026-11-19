"""Diagnostic drummer cue preview helpers.

These helpers parse drummer cues out of an XSQ and light flat component masks
for a quick visual check. They are a custom diagnostic visualization: nothing
here is native xLights output, and nothing here is evidence of a native render.

The source-art drummer renderer lives in ``tools.render_drummer_v3_preview``;
this module holds the dependency-free cue timing and compositing helpers.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from mapping.drum_mapper import DRUMMER_COMPONENTS, DRUMMER_V3_MODEL

TARGETS = tuple(DRUMMER_COMPONENTS)
SNARE = f"{DRUMMER_V3_MODEL}_SNARE"
LABELS = {target: target.removeprefix(DRUMMER_V3_MODEL + "_").replace("_", " ") for target in TARGETS}
_HAND_CODE = {"L": "L", "R": "R", "left": "L", "right": "R"}


def canonical_target(name: str) -> str:
    """Accept physical component names exported without the V3 infix."""
    legacy_prefix = "HX_SNOWMAN_DRUMMER_"
    if name.startswith(legacy_prefix) and not name.startswith(DRUMMER_V3_MODEL + "_"):
        return name.replace(legacy_prefix, DRUMMER_V3_MODEL + "_", 1)
    return name


def parse_effects(xsq: Path, *, include_hands: bool = False) -> list[tuple[int, int, str]]:
    root = ET.parse(xsq).getroot()
    out: list[tuple[int, int, str]] = []
    for element in root.findall("./ElementEffects/Element"):
        name = canonical_target(element.get("name", ""))
        if name not in TARGETS:
            continue
        for layer in element.findall("EffectLayer"):
            for fx in layer.findall("Effect"):
                start = int(float(fx.get("startTime", "0")))
                end = int(float(fx.get("endTime", "0")))
                out.append((start, end, name))
                hand = _HAND_CODE.get(fx.get("sourceHand", ""))
                if include_hands and name == SNARE and hand:
                    out.append((start, end, "SNARE_HAND_" + hand))
    return sorted(out)


def strike_intensity(start_ms: int, end_ms: int, time_ms: int) -> float:
    """Immediate contact illumination followed by a bounded quadratic decay."""
    if not start_ms <= time_ms < end_ms:
        return 0.0
    progress = (time_ms - start_ms) / max(1, end_ms - start_ms)
    return (1.0 - progress) ** 2


def light_component(base: Image.Image, mask: Image.Image, intensity: float) -> Image.Image:
    """Illuminate the masked pixels of the artwork; never touch remote pixels."""
    if intensity <= 0.02:
        return base
    intensity = max(0.0, min(1.0, intensity))
    core = mask.point(lambda a: int(a * intensity))
    glow = core.filter(ImageFilter.GaussianBlur(max(4, base.width // 160)))
    bloom = Image.new("RGBA", base.size, (255, 220, 75, 0))
    bloom.putalpha(glow.point(lambda a: int(a * 0.55)))
    out = Image.alpha_composite(base, bloom)
    bright = ImageEnhance.Brightness(out.convert("RGB")).enhance(1.0 + 0.75 * intensity)
    out = Image.composite(bright.convert("RGBA"), out, core)
    core_layer = Image.new("RGBA", base.size, (255, 250, 150, 0))
    core_layer.putalpha(core.point(lambda a: int(a * 0.70)))
    return Image.alpha_composite(out, core_layer)


def active_frames(effects, times, targets):
    """Sweep sorted event starts once; retain only currently active intervals."""
    ordered = sorted(effects)
    pending = 0
    live: list[tuple[int, int, str]] = []
    for t in times:
        live = [event for event in live if event[1] > t]
        while pending < len(ordered) and ordered[pending][0] <= t:
            event = ordered[pending]
            pending += 1
            if event[1] > t:
                live.append(event)
        active = dict.fromkeys(targets, 0.0)
        for start, end, name in live:
            if name in active:
                active[name] = max(active[name], strike_intensity(start, end, t))
        yield t, active


def prepare_frame_assets(source, masks, width, height):
    """Scale artwork and masks together so highlights cannot drift off the art."""
    scale = min(width / source.width, height / source.height)
    size = (max(1, round(source.width * scale)), max(1, round(source.height * scale)))
    return source.resize(size, Image.Resampling.LANCZOS), {
        name: mask.resize(size, Image.Resampling.BILINEAR) for name, mask in masks.items()
    }


def draw_frame(source, masks, active, width, height, t_ms, duration_ms, font, *, prepared=None):
    base, scaled_masks = prepared if prepared is not None else prepare_frame_assets(source, masks, width, height)
    for target, intensity in active.items():
        if intensity > 0.02:
            base = light_component(base, scaled_masks[target], intensity)
    canvas = Image.new("RGBA", (width, height), (4, 7, 12, 255))
    canvas.alpha_composite(base, ((width - base.width) // 2, (height - base.height) // 2))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((18, 16, width - 18, 88), radius=12, fill=(5, 9, 16, 205), outline=(120, 140, 170, 210), width=2)
    active_names = [LABELS.get(t, t) for t, v in active.items() if v > 0.02]
    d.text((34, 30), "HELIX DIAGNOSTIC (NOT NATIVE XLIGHTS) - DRUMMER CUES", font=font, fill=(245, 248, 255, 255))
    d.text((34, 53), "LIGHTING: " + (", ".join(active_names) if active_names else "idle"), font=font, fill=(255, 215, 150, 255))
    d.text((width - 190, 30), f"{t_ms/1000:.2f}s / {duration_ms/1000:.2f}s", font=font, fill=(190, 210, 235, 255))
    return canvas.convert("RGB")
