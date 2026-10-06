"""Shared high-fidelity Drummer V3 geometry and emissive rendering helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "fixtures" / "band_geometry" / "drummer_v3_pose_spec.json"
MODEL_NAME = "HX_SNOWMAN_DRUMMER_V3"


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
    idle_brightness: float = 0.42,
    active_brightness: float = 1.15,
    white_lift: float = 0.015,
    outline_radius: int = 3,
    halo_radius: float = 5.0,
) -> Image.Image:
    """Render the approved drummer artwork as a dim stage image plus hit outlines.

    The entire drummerbg remains continuously visible. A hit restores the
    component toward its source brightness, then adds a crisp warm-white outline
    and a restrained outer halo. The outline is derived from the exact target
    mask, so it follows the drum/cymbal and its integrated actuator rather than
    replacing the artwork with a painted blob.
    """
    source_rgba = source.convert("RGBA")
    source_rgb = source_rgba.convert("RGB")
    idle_rgb = ImageEnhance.Brightness(source_rgb).enhance(idle_brightness)
    idle = idle_rgb.convert("RGBA")

    union = Image.new("L", source_rgba.size, 0)
    for target in active_targets:
        if target not in masks:
            raise ValueError(f"Unknown drummer target: {target}")
        union = ImageChops.lighter(union, masks[target])
    if union.getbbox() is None:
        return idle

    active_rgb = ImageEnhance.Brightness(source_rgb).enhance(active_brightness)
    active_rgb = ImageEnhance.Color(active_rgb).enhance(1.08)
    if white_lift > 0:
        active_rgb = Image.blend(
            active_rgb,
            Image.new("RGB", source_rgba.size, (255, 255, 255)),
            white_lift,
        )
    frame = Image.composite(active_rgb.convert("RGBA"), idle, union)

    # Trace both sides of the component boundary. The outer band makes adjacent
    # drums distinct while the inner band keeps the outline attached to the
    # actual source artwork.
    radius = max(1, int(outline_radius))
    kernel = radius * 2 + 1
    dilated = union.filter(ImageFilter.MaxFilter(kernel))
    eroded = union.filter(ImageFilter.MinFilter(kernel))
    outer = ImageChops.subtract(dilated, union)
    inner = ImageChops.subtract(union, eroded)
    edge = ImageChops.lighter(outer, inner)

    # Soft halo first, then a crisp outline. Limit the halo so the background
    # remains visibly dim rather than turning into a global flash.
    halo = outer.filter(ImageFilter.GaussianBlur(max(0.1, float(halo_radius))))
    halo = halo.point(lambda value: int(value * 0.28))
    halo_color = Image.new("RGBA", source_rgba.size, (255, 196, 96, 255))
    frame = Image.composite(halo_color, frame, halo)

    crisp = edge.point(lambda value: int(value * 0.72))
    outline_color = Image.new("RGBA", source_rgba.size, (255, 246, 202, 255))
    frame = Image.composite(outline_color, frame, crisp)
    return frame
