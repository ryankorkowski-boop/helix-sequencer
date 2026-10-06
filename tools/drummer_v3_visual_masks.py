"""Shared high-fidelity Drummer V3 geometry and emissive rendering helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "fixtures" / "band_geometry" / "drummer_v3_pose_spec.json"
MODEL_NAME = "HX_SNOWMAN_DRUMMER_V3"

# Review/output colors are part of the physical drummer contract.  They match
# the actual prop artwork: red kick rim, magenta snare, gold metal, green toms.
# Actuators (arms/sticks/hi-hat foot) are never recolored; they are only restored
# from the source artwork so they continue to look like the photographed/drawn
# component instead of a generic white tracing.
TARGET_OUTLINE_RGB = {
    f"{MODEL_NAME}_KICK": (220, 45, 28),
    f"{MODEL_NAME}_SNARE": (214, 92, 190),
    f"{MODEL_NAME}_HI_HAT": (220, 164, 22),
    f"{MODEL_NAME}_TOM_HIGH": (44, 178, 66),
    f"{MODEL_NAME}_TOM_MID": (44, 178, 66),
    f"{MODEL_NAME}_TOM_FLOOR": (44, 178, 66),
    f"{MODEL_NAME}_CYMBAL_LEFT": (220, 164, 22),
    f"{MODEL_NAME}_CYMBAL_RIGHT": (220, 164, 22),
}


def target_surface_key(target: str) -> str:
    return f"__surface__:{target}"


def refine_surface_to_source_art(
    source: Image.Image,
    authored_surface: Image.Image,
    target: str,
) -> Image.Image:
    """Keep only source pixels that actually draw the colored instrument."""
    color = TARGET_OUTLINE_RGB.get(target)
    if color is None:
        return authored_surface.copy()

    hsv = np.asarray(source.convert("RGB").convert("HSV"), dtype=np.int16)
    target_h = int(Image.new("RGB", (1, 1), color).convert("HSV").getpixel((0, 0))[0])
    hue = hsv[..., 0]
    sat = hsv[..., 1]
    val = hsv[..., 2]
    distance = np.abs(hue - target_h)
    distance = np.minimum(distance, 256 - distance)

    if target.endswith("_KICK"):
        tolerance = 26
    elif "CYMBAL" in target or target.endswith("_HI_HAT"):
        tolerance = 24
    elif "_TOM_" in target:
        tolerance = 28
    else:
        tolerance = 30

    authored = np.asarray(authored_surface, dtype=np.uint8) > 0
    selected = authored & (distance <= tolerance) & (sat >= 48) & (val >= 24)
    count = int(np.count_nonzero(selected))
    minimum = max(6, int(np.count_nonzero(authored) * 0.025))
    if count < minimum:
        return authored_surface.copy()

    exact = Image.fromarray(np.where(selected, 255, 0).astype(np.uint8), mode="L")
    return ImageChops.darker(exact.filter(ImageFilter.MaxFilter(3)), authored_surface)


def refine_actuator_to_source_art(source: Image.Image, authored_actuator: Image.Image) -> Image.Image:
    """Remove black/background pixels from an arm/stick/foot search polygon."""
    hsv = np.asarray(source.convert("RGB").convert("HSV"), dtype=np.uint8)
    value = hsv[..., 2]
    authored = np.asarray(authored_actuator, dtype=np.uint8) > 0
    selected = authored & (value >= 38)
    if int(np.count_nonzero(selected)) < max(4, int(np.count_nonzero(authored) * 0.02)):
        return authored_actuator.copy()
    exact = Image.fromarray(np.where(selected, 255, 0).astype(np.uint8), mode="L")
    return ImageChops.darker(exact.filter(ImageFilter.MaxFilter(3)), authored_actuator)


def load_spec(path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Drummer V3 pose spec must be an object: {path}")
    if data.get("model_name") != MODEL_NAME:
        raise ValueError(f"Unexpected Drummer V3 model name: {data.get('model_name')!r}")
    return data


def _points(command: dict[str, Any], size: tuple[int, int]) -> list[tuple[int, int]]:
    raw = command.get("points")
    if not isinstance(raw, list) or len(raw) < 3:
        raise ValueError(f"Polygon command missing normalized points: {command!r}")
    width, height = size
    out: list[tuple[int, int]] = []
    for pair in raw:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"Invalid polygon point: {pair!r}")
        out.append((
            round(float(pair[0]) * (width - 1)),
            round(float(pair[1]) * (height - 1)),
        ))
    return out


def build_zone_mask(size: tuple[int, int], zone: dict[str, Any]) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    commands = zone.get("commands", [])
    if not isinstance(commands, list) or not commands:
        raise ValueError(f"Zone {zone.get('id')} has no draw commands")
    for command in commands:
        if not isinstance(command, dict):
            raise ValueError(f"Invalid command in {zone.get('id')}: {command!r}")
        if str(command.get("shape", "")) != "polygon":
            raise ValueError(f"Unsupported V3 geometry command shape: {command.get('shape')!r}")
        draw.polygon(_points(command, size), fill=255)
    return mask


def _union(masks: list[Image.Image], size: tuple[int, int]) -> Image.Image:
    result = Image.new("L", size, 0)
    for mask in masks:
        result = ImageChops.lighter(result, mask)
    return result


def build_geometry_masks(
    size: tuple[int, int],
    spec: dict[str, Any] | None = None,
) -> dict[str, dict[str, Image.Image]]:
    """Build isolated surfaces, actuator-only masks, and public hit targets.

    The same authored geometry is rasterized at both xmodel-grid resolution and
    full source-image resolution. This keeps one contract while avoiding the
    blockiness of enlarging a 96x72 mask for review video.
    """
    spec = spec or load_spec()
    zones = {
        str(zone["id"]): zone
        for zone in spec.get("zones", [])
        if isinstance(zone, dict) and zone.get("id")
    }
    raw = {name: build_zone_mask(size, zone) for name, zone in zones.items()}
    kinds = {name: str(zone.get("kind", "")) for name, zone in zones.items()}

    raw_surfaces = {name: mask for name, mask in raw.items() if kinds.get(name) == "surface"}
    if not raw_surfaces:
        raise ValueError("Drummer V3 pose spec has no surface zones")
    raw_surface_union = _union(list(raw_surfaces.values()), size)

    surfaces: dict[str, Image.Image] = {}
    for name, mask in raw_surfaces.items():
        others = _union([m for other, m in raw_surfaces.items() if other != name], size)
        exclusive = ImageChops.subtract(mask, others)
        if exclusive.getbbox() is None:
            raise ValueError(f"V3 surface lost all pixels after isolation: {name}")
        surfaces[name] = exclusive

    actuators: dict[str, Image.Image] = {}
    for name, mask in raw.items():
        if kinds.get(name) != "actuator":
            continue
        isolated = ImageChops.subtract(mask, raw_surface_union)
        if isolated.getbbox() is None:
            raise ValueError(f"V3 actuator lost all pixels after surface exclusion: {name}")
        actuators[name] = isolated

    targets: dict[str, Image.Image] = {}
    lighting_targets = spec.get("lighting_targets", [])
    if not isinstance(lighting_targets, list) or len(lighting_targets) != 8:
        raise ValueError("Expected exactly eight lighting targets")
    for target in lighting_targets:
        if not isinstance(target, dict):
            raise ValueError(f"Invalid lighting target: {target!r}")
        target_id = str(target["id"])
        surface_id = str(target["surface"])
        if surface_id not in surfaces:
            raise ValueError(f"{target_id} references missing surface {surface_id}")
        mask = surfaces[surface_id].copy()
        for actuator_id in target.get("actuators", []):
            actuator_id = str(actuator_id)
            if actuator_id not in actuators:
                raise ValueError(f"{target_id} references missing actuator {actuator_id}")
            mask = ImageChops.lighter(mask, actuators[actuator_id])
        if mask.getbbox() is None:
            raise ValueError(f"V3 target generated no pixels: {target_id}")
        targets[f"{MODEL_NAME}_{target_id}"] = mask

    return {"raw": raw, "surfaces": surfaces, "actuators": actuators, "targets": targets}


def compose_emissive(
    source: Image.Image,
    masks: dict[str, Image.Image],
    active_targets: list[str] | tuple[str, ...] | set[str],
    *,
    idle_brightness: float = 0.48,
    active_brightness: float = 1.30,
    outline_radius: int = 2,
    halo_radius: float = 4.0,
) -> Image.Image:
    """Illuminate the real component artwork, not a generic traced substitute.

    The complete drummerbg stays visible at a dim stage level.  Active targets
    restore the original source pixels at higher brightness.  Only the actual
    instrument surface gets a thin, component-colored edge/halo (red kick,
    green toms, gold metal, magenta snare).  Integrated arms/sticks/foot brighten
    in their own source colors and are deliberately *not* outlined.
    """
    source_rgba = source.convert("RGBA")
    source_rgb = source_rgba.convert("RGB")
    idle = ImageEnhance.Brightness(source_rgb).enhance(idle_brightness).convert("RGBA")

    union = Image.new("L", source_rgba.size, 0)
    ordered_targets = [target for target in masks if target in set(active_targets) and not target.startswith("__surface__:")]
    for target in active_targets:
        if target not in masks:
            raise ValueError(f"Unknown drummer target: {target}")
        union = ImageChops.lighter(union, masks[target])
    if union.getbbox() is None:
        return idle

    # First restore the exact source artwork for the complete integrated target.
    active_rgb = ImageEnhance.Brightness(source_rgb).enhance(active_brightness)
    active_rgb = ImageEnhance.Color(active_rgb).enhance(1.12)
    frame = Image.composite(active_rgb.convert("RGBA"), idle, union)

    # Then outline only the physical drum/cymbal surface.  This avoids the
    # Apple-II-looking white scribble around arms and sticks.
    radius = max(1, int(outline_radius))
    kernel = radius * 2 + 1
    for target in active_targets:
        surface = masks.get(target_surface_key(target), masks[target])
        color = TARGET_OUTLINE_RGB.get(target)
        if color is None or surface.getbbox() is None:
            continue
        dilated = surface.filter(ImageFilter.MaxFilter(kernel))
        eroded = surface.filter(ImageFilter.MinFilter(kernel))
        outer = ImageChops.subtract(dilated, surface)
        inner = ImageChops.subtract(surface, eroded)
        edge = ImageChops.lighter(outer, inner)

        halo = outer.filter(ImageFilter.GaussianBlur(max(0.1, float(halo_radius))))
        halo = halo.point(lambda value: int(value * 0.22))
        color_image = Image.new("RGBA", source_rgba.size, (*color, 255))
        frame = Image.composite(color_image, frame, halo)

        crisp = edge.point(lambda value: int(value * 0.78))
        frame = Image.composite(color_image, frame, crisp)

    return frame

