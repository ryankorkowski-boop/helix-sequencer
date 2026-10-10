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


def target_art_key(target: str) -> str:
    return f"__art__:{target}"


def target_actuator_key(target: str) -> str:
    return f"__actuator__:{target}"


def target_variant_key(target: str, hand: str) -> str:
    return f"__variant__:{target}:{hand}"


def idle_art_key() -> str:
    return "__idle_art__"


def snare_shell_mask(size: tuple[int, int], outline: dict) -> Image.Image:
    """Complete the snare shell hidden by the photographed foreground kick."""
    scale = (size[0] - 1, size[1] - 1)
    top, bottom = [tuple(round(v * scale[i % 2]) for i, v in enumerate(outline[key]))
                   for key in ("top_bbox", "bottom_bbox")]
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    width = max(1, round(float(outline["width"]) * scale[0]))
    draw.ellipse(top, outline=255, width=width)
    draw.arc(bottom, 0, 180, fill=255, width=width)
    for x in (top[0], top[2]):
        draw.line((x, (top[1]+top[3])//2, x, (bottom[1]+bottom[3])//2), fill=255, width=width)
    return mask


def resting_stick_mask(source: Image.Image, spec: dict) -> Image.Image:
    hsv = np.asarray(source.convert("HSV"))
    gold = Image.fromarray(np.where(
        (_hue_distance(hsv[..., 0], _rgb_hue((220, 164, 22))) <= 25)
        & (hsv[..., 1] >= 46) & (hsv[..., 2] >= 24), 255, 0).astype(np.uint8))
    zones = [build_zone_mask(source.size, {"commands": [{"shape": "polygon", "points": points}]})
             for points in spec.get("idle_stick_polygons", [])]
    return ImageChops.multiply(_union(zones, source.size), gold)


def resting_actuator_mask(source: Image.Image, spec: dict, surfaces: dict) -> Image.Image:
    """Erase only resting arm/shaft artwork; retain the head, scarf and kit."""
    masks = []
    hsv = np.asarray(source.convert("HSV"))
    neutral = Image.fromarray(np.where((hsv[..., 1] <= 90) & (hsv[..., 2] >= 24), 255, 0).astype(np.uint8))
    gold = Image.fromarray(np.where(
        (_hue_distance(hsv[..., 0], _rgb_hue((220, 164, 22))) <= 25)
        & (hsv[..., 1] >= 46) & (hsv[..., 2] >= 24), 255, 0).astype(np.uint8))
    removable_color = ImageChops.lighter(neutral, gold)
    for zone in spec["zones"]:
        if zone["kind"] != "actuator" or zone["id"] == "HI_HAT_FOOT":
            continue
        arm = build_zone_mask(source.size, zone)
        masks.append(ImageChops.multiply(arm, removable_color))
        shaft = zone.get("strike", {}).get("source_stick")
        if shaft:
            masks.append(refine_actuator_to_source_art(source, build_zone_mask(source.size, shaft)))
    for points in spec.get("idle_extra_stick_polygons", []):
        masks.append(ImageChops.multiply(build_zone_mask(source.size, {
            "commands": [{"shape": "polygon", "points": points}]}), removable_color))
    removed = _union(masks, source.size).filter(ImageFilter.MaxFilter(3))
    return ImageChops.lighter(
        ImageChops.subtract(removed, _union(list(surfaces.values()), source.size)),
        resting_stick_mask(source, spec).filter(ImageFilter.MaxFilter(3)))


def strike_transform(strike: dict, size: tuple[int, int]) -> tuple[float, ...]:
    """Inverse similarity transform: source shaft grip/tip to wrist/contact.

    Only source-art pixels are resampled; no replacement line is painted.
    Coordinates use the same normalized image space as the instrument surfaces.
    """
    scale = np.array(size, dtype=float) - 1
    a, b, c, d = (np.asarray(strike[k]) * scale for k in
                  ("source_grip", "source_tip", "grip", "contact"))
    u, v = b - a, d - c
    if np.linalg.norm(u) < 1 or np.linalg.norm(v) < 1:
        raise ValueError("Degenerate strike shaft")
    real = float(np.dot(u, v) / np.dot(u, u))
    imag = float((u[0]*v[1] - u[1]*v[0]) / np.dot(u, u))
    inverse = np.linalg.inv(np.array([[real, -imag], [imag, real]]))
    offset = a - inverse @ c
    return (*inverse[0], offset[0], *inverse[1], offset[1])


def exact_actuator_art(
    source: Image.Image,
    zone: dict,
    excluded: Image.Image,
    source_surfaces: Image.Image | None = None,
    *,
    allow_front_overlap: bool = False,
) -> Image.Image:
    """Source-colored arm/shaft art, optionally allowed to pass in front of drums.

    Preview and native assets preserve front overlap so an arm or shaft stays
    continuous when it crosses another instrument. False is available only
    for regression comparison against the previous clipped geometry.
    """
    arm_mask = refine_actuator_to_source_art(source, build_zone_mask(source.size, zone))
    if zone.get("strike") and source_surfaces is not None:
        arm_mask = ImageChops.subtract(arm_mask, source_surfaces)
        # The arm is neutral wire artwork. Do not carry neighboring scarf or
        # face pixels into a reposed arm merely because the search window grazes them.
        hsv = np.asarray(source.convert("HSV"))
        neutral = Image.fromarray(np.where(hsv[..., 1] <= 90, 255, 0).astype(np.uint8))
        arm_mask = ImageChops.multiply(arm_mask, neutral)
    arm = source.convert("RGBA").copy()
    arm.putalpha(arm_mask)
    strike = zone.get("strike")
    # Ready and strike poses share the revised torso shoulder anchors. Keep
    # wrist/contact coordinates fixed and resample the original wire artwork.
    arm_transform = (strike or {}).get("arm_transform", zone.get("arm_transform"))
    if arm_transform:
        arm = arm.transform(source.size, Image.Transform.AFFINE,
                            strike_transform(arm_transform, source.size),
                            Image.Resampling.BICUBIC)
    if strike:
        shaft_mask = refine_actuator_to_source_art(
            source, build_zone_mask(source.size, strike["source_stick"]))
        shaft = source.convert("RGBA").copy()
        shaft.putalpha(shaft_mask)
        shaft = shaft.transform(source.size, Image.Transform.AFFINE,
                                strike_transform(strike, source.size), Image.Resampling.BICUBIC)
        arm = Image.alpha_composite(arm, shaft)
    if not allow_front_overlap:
        arm.putalpha(ImageChops.subtract(arm.getchannel("A"), excluded))
    return arm


def exact_geometry(
    source: Image.Image,
    spec: dict | None = None,
    *,
    preview_front_overlap: bool = True,
) -> dict:
    """One source-art extraction path for preview, layers and xmodel projection.

    Full-resolution review art and native projection use complete front strikes.
    Instrument surfaces themselves remain independently assigned.
    """
    spec = spec or load_spec()
    geometry = build_geometry_masks(source.size, spec)
    surfaces = {item["surface"]: refine_surface_to_source_art(
        source, geometry["surfaces"][item["surface"]], f"{MODEL_NAME}_{item['id']}")
        for item in spec["lighting_targets"]}
    if spec.get("idle_remove_raised_actuators"):
        sticks = resting_stick_mask(source, spec)
        for name in ("CYMBAL_LEFT_SURFACE", "CYMBAL_RIGHT_SURFACE"):
            # Gold resting shafts crossing a cymbal search window are not part
            # of the cymbal itself. Remove these before independent lighting.
            surfaces[name] = ImageChops.subtract(surfaces[name], sticks)
    surface_art = source.convert("RGBA").copy()
    for zone in spec["zones"]:
        if zone.get("shell_outline"):
            shell = snare_shell_mask(source.size, zone["shell_outline"])
            surfaces[zone["id"]] = ImageChops.lighter(surfaces[zone["id"]], shell)
            surface_art = Image.composite(
                Image.new("RGBA", source.size, (*TARGET_OUTLINE_RGB[f"{MODEL_NAME}_SNARE"], 255)),
                surface_art, shell)
    # The kick's photographed search window includes part of the purple snare.
    # Keep the kick independent; the completed snare is visible through it.
    surfaces["KICK_SURFACE"] = ImageChops.subtract(surfaces["KICK_SURFACE"], surfaces["SNARE_SURFACE"])
    # Exclude actual instrument pixels, not their search windows: sticks may
    # approach the head through otherwise empty background within the window.
    exclusion = _union(list(surfaces.values()), source.size)
    arts = {}
    for zone in spec["zones"]:
        if zone["kind"] != "actuator":
            continue
        own_surface = zone.get("strike", {}).get("instrument_surface")
        excluded = _union([mask for name, mask in surfaces.items() if name != own_surface], source.size)
        arts[zone["id"]] = exact_actuator_art(
            source,
            zone,
            excluded,
            exclusion,
            allow_front_overlap=preview_front_overlap,
        )
    masks = {}
    idle = source.convert("RGBA").copy()
    if spec.get("idle_remove_raised_actuators"):
        removed = resting_actuator_mask(source, spec, surfaces)
        idle = Image.composite(Image.new("RGBA", source.size, (0, 0, 0, 255)), idle, removed)
        masks["__idle_removed__"] = removed
    masks[idle_art_key()] = idle
    if spec.get("torso_shoulders"):
        # A short upper-torso contour connects the lowered arm roots to the
        # body below the scarf. It is body keepalive, never a strike actuator.
        shoulder_mask = build_zone_mask(source.size, spec["torso_shoulders"])
        shoulder_art = Image.new("RGBA", source.size,
                                 (*spec["torso_shoulders"]["rgb"], 255))
        shoulder_art.putalpha(shoulder_mask)
        masks[idle_art_key()] = Image.alpha_composite(idle, shoulder_art)
        masks["__torso_shoulders__"] = shoulder_mask
    for item in spec["lighting_targets"]:
        name = f"{MODEL_NAME}_{item['id']}"
        variants = item.get("actuator_variants", {"left": item["actuators"]})
        for hand, actuators in variants.items():
            mask = surfaces[item["surface"]].copy()
            actuator_mask = Image.new("L", source.size, 0)
            art = surface_art.copy()
            for actuator in actuators:
                overlay = arts[actuator]
                art = Image.alpha_composite(art, overlay)
                alpha = overlay.getchannel("A").point(
                    lambda value: round(value * item.get("actuator_intensity", 1.0)))
                mask = ImageChops.lighter(mask, alpha)
                actuator_mask = ImageChops.lighter(actuator_mask, alpha)
            key = name if hand == "left" else target_variant_key(name, hand)
            masks[key] = mask
            masks[target_art_key(key)] = art
            masks[target_actuator_key(key)] = actuator_mask
        masks[target_surface_key(name)] = surfaces[item["surface"]]
    return {"surfaces": surfaces, "actuators": arts, "masks": masks}


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
        red = (_hue_distance(hue, _rgb_hue((220, 45, 28))) <= 20)
        blue = (_hue_distance(hue, _rgb_hue((35, 135, 210))) <= 24)
        selected = authored & (sat >= 48) & (val >= 24) & (red | blue)
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
        ((sat <= 90) & (val >= 24))
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
    for name, zone in zones.items():
        strike = zone.get("strike")
        arm = raw[name]
        arm_transform = (strike or {}).get("arm_transform", zone.get("arm_transform"))
        if arm_transform:
            arm = arm.transform(size, Image.Transform.AFFINE,
                                strike_transform(arm_transform, size))
        raw[name] = arm
        if not strike:
            continue
        shaft = build_zone_mask(size, strike["source_stick"]).transform(
            size, Image.Transform.AFFINE, strike_transform(strike, size))
        raw[name] = ImageChops.lighter(arm, shaft)
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
    active_brightness: float = 1.45,
    halo_radius: float = 3.2,
    idle_overlay_mask: Image.Image | None = None,
    idle_overlay_brightness: float = 0.42,
    snare_hand: str = "left",
    cymbal_levels: dict[str, float] | None = None,
) -> Image.Image:
    """Dim the canonical artwork, then brighten only its exact hit pixels.

    Components use the source artwork, with the explicitly authored completion
    of the snare shell hidden by the kick. A restrained bloom makes hits clear.
    """
    source_rgba = source.convert("RGBA")
    source_rgb = masks.get(idle_art_key(), source_rgba).convert("RGB")
    idle = ImageEnhance.Brightness(source_rgb).enhance(idle_brightness).convert("RGBA")
    if idle_overlay_mask is not None and idle_overlay_mask.getbbox() is not None:
        keepalive = ImageEnhance.Brightness(source_rgb).enhance(
            idle_overlay_brightness
        ).convert("RGBA")
        idle = Image.composite(keepalive, idle, idle_overlay_mask)

    active_set = set(active_targets)
    ringing = {target for target, level in (cymbal_levels or {}).items() if level > 0}
    render_set = active_set | ringing
    if not render_set:
        return idle

    union = Image.new("L", source_rgba.size, 0)
    for target in render_set:
        if target not in masks:
            raise ValueError(f"Unknown drummer target: {target}")
        key = target_variant_key(target, snare_hand) if target.endswith("_SNARE") and snare_hand != "left" else target
        union = ImageChops.lighter(union, masks[key])
    if union.getbbox() is None:
        return idle

    # Compose each posed source independently, then take a pixelwise maximum.
    # Shared arms retain one brightness even when several targets coincide.
    frame_array = np.asarray(idle).copy()
    for target in sorted(render_set):
        key = target_variant_key(target, snare_hand) if target.endswith("_SNARE") and snare_hand != "left" else target
        art = masks.get(target_art_key(key), source_rgba).convert("RGB")
        active_rgb = ImageEnhance.Brightness(art).enhance(active_brightness)
        active_rgb = ImageEnhance.Color(active_rgb).enhance(1.18)
        surface = masks.get(target_surface_key(target), masks[target])
        gain = 1.0
        if cymbal_levels is not None and target.endswith(("_CYMBAL_LEFT", "_CYMBAL_RIGHT")):
            gain = max(0.0, min(1.0, cymbal_levels.get(target, 0.0)))
            # The surface rings; the strike pose only follows the original hit.
            actuator = masks.get(target_actuator_key(key), ImageChops.subtract(masks[key], surface))
            # Keep the full posed artwork at contact pixels, including its
            # antialiasing already composited over the source instrument.
            contact = ImageChops.multiply(surface, actuator.point(lambda value: 255 if value else 0))
            arm_mask = ImageChops.lighter(actuator, contact)
            surface_rgb = ImageEnhance.Brightness(source_rgba.convert("RGB")).enhance(active_brightness)
            surface_rgb = ImageEnhance.Color(surface_rgb).enhance(1.18)
            fading_mask = surface.point(lambda value: round(value * gain))
            surface_lit = Image.composite(surface_rgb.convert("RGBA"), idle, fading_mask)
            lit = Image.composite(active_rgb.convert("RGBA"), surface_lit, arm_mask) if target in active_set else surface_lit
        else:
            lit = Image.composite(active_rgb.convert("RGBA"), idle, masks[key])
        color = TARGET_OUTLINE_RGB.get(target)
        if color is not None and surface.getbbox() is not None:
            blurred = surface.filter(ImageFilter.GaussianBlur(max(0.1, float(halo_radius))))
            outside = ImageChops.subtract(blurred, surface).point(lambda value: int(value * 0.32 * gain))
            glow = Image.new("RGBA", source_rgba.size, (*color, 255))
            lit = Image.composite(glow, lit, outside)
        frame_array = np.maximum(frame_array, np.asarray(lit))
    frame = Image.fromarray(frame_array)

    return frame
