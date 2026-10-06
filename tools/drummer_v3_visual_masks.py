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


def _hue_distance(hue: np.ndarray, target_hue: int) -> np.ndarray:
    distance = np.abs(hue.astype(np.int16) - int(target_hue))
    return np.minimum(distance, 256 - distance)


def _rgb_hue(rgb: tuple[int, int, int]) -> int:
    return int(Image.new("RGB", (1, 1), rgb).convert("HSV").getpixel((0, 0))[0])


def refine_surface_to_source_art(
    source: Image.Image,
    authored_surface: Image.Image,
    target: str,
) -> Image.Image:
    """Extract the actual painted/wireframe pixels for one instrument.

    The pose-spec polygon is only a search window. The returned mask follows
    the colored source pixels inside that window, so a lit kick is the real red
    kick ring (plus its blue snowflake), a lit tom is the real green tom, etc.
    No polygon edge is ever shown as the component.
    """
    hsv = np.asarray(source.convert("RGB").convert("HSV"), dtype=np.uint8)
    hue = hsv[..., 0]
    sat = hsv[..., 1]
    val = hsv[..., 2]
    authored = np.asarray(authored_surface, dtype=np.uint8) > 0

    if target.endswith("_KICK"):
        # The canonical kick is a red/orange ring with a blue snowflake inside.
        # Preserve both source colors instead of painting a replacement circle.
        selected = authored & (sat >= 48) & (val >= 24)
    else:
        color = TARGET_OUTLINE_RGB.get(target)
        if color is None:
            return authored_surface.copy()
        target_hue = _rgb_hue(color)
        tolerance = 30 if "_TOM_" in target else 27
        if "CYMBAL" in target or target.endswith("_HI_HAT"):
            tolerance = 25
        selected = (
            authored
            & (_hue_distance(hue, target_hue) <= tolerance)
            & (sat >= 46)
            & (val >= 24)
        )

    count = int(np.count_nonzero(selected))
    minimum = max(8, int(np.count_nonzero(authored) * 0.018))
    if count < minimum:
        raise ValueError(f"Could not recover exact source pixels for {target}: {count} < {minimum}")

    return Image.fromarray(np.where(selected, 255, 0).astype(np.uint8), mode="L")


def refine_actuator_to_source_art(
    source: Image.Image,
    authored_actuator: Image.Image,
) -> Image.Image:
    """Keep the real arm/stick/foot pixels and discard its search polygon."""
    hsv = np.asarray(source.convert("RGB").convert("HSV"), dtype=np.uint8)
    sat = hsv[..., 1]
    val = hsv[..., 2]
    authored = np.asarray(authored_actuator, dtype=np.uint8) > 0

    # Arms are pale/white while sticks are gold/orange. Both are source artwork;
    # dark stage/grid pixels are not.
    selected = authored & (
        ((sat <= 70) & (val >= 72))
        | ((sat > 70) & (val >= 34))
    )
    count = int(np.count_nonzero(selected))
    minimum = max(5, int(np.count_nonzero(authored) * 0.012))
    if count < minimum:
        raise ValueError(f"Could not recover actuator source pixels: {count} < {minimum}")
    return Image.fromarray(np.where(selected, 255, 0).astype(np.uint8), mode="L")

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
    idle_brightness: float = 0.30,
    active_brightness: float = 1.78,
    halo_radius: float = 3.2,
) -> Image.Image:
    """Dim the canonical artwork, then brighten only its exact hit pixels.

    There are no synthetic outlines, circles, or painted polygons. Active
    components are literally the source artwork restored brighter, with a
    restrained bloom outside the exact pixels so the hit reads clearly.
    """
    source_rgba = source.convert("RGBA")
    source_rgb = source_rgba.convert("RGB")
    idle = ImageEnhance.Brightness(source_rgb).enhance(idle_brightness).convert("RGBA")

    active_set = set(active_targets)
    if not active_set:
        return idle

    union = Image.new("L", source_rgba.size, 0)
    for target in active_set:
        if target not in masks:
            raise ValueError(f"Unknown drummer target: {target}")
        union = ImageChops.lighter(union, masks[target])
    if union.getbbox() is None:
        return idle

    active_rgb = ImageEnhance.Brightness(source_rgb).enhance(active_brightness)
    active_rgb = ImageEnhance.Color(active_rgb).enhance(1.18)
    frame = Image.composite(active_rgb.convert("RGBA"), idle, union)

    # Soft source-colored bloom only; never draw an artificial edge. Each bloom
    # derives from the exact surface mask and cannot turn an arm into a scribble.
    for target in active_set:
        surface = masks.get(target_surface_key(target), masks[target])
        color = TARGET_OUTLINE_RGB.get(target)
        if color is None or surface.getbbox() is None:
            continue
        blurred = surface.filter(ImageFilter.GaussianBlur(max(0.1, float(halo_radius))))
        outside = ImageChops.subtract(blurred, surface)
        outside = outside.point(lambda value: int(value * 0.32))
        glow = Image.new("RGBA", source_rgba.size, (*color, 255))
        frame = Image.composite(glow, frame, outside)

    return frame

