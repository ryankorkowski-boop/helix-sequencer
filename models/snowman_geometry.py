from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from models.grid_canvas import Coord, DrawableModelTemplate, GridCanvas, PixelRegion, SubmodelTemplate
from models.mouth_templates import default_mouth_box, generate_mouth_library, place_mouth_shape


STANDARD_CANVAS_SIZES = (32, 48, 64)


ROLE_METADATA = {
    "singer": {"display_name": "Lead Singer Snowman", "mouth_scale": 1.10, "mouth_offset": (0, 0)},
    "guitarist": {"display_name": "Guitarist Snowman", "mouth_scale": 0.82, "mouth_offset": (0, 0)},
    "bassist": {"display_name": "Upright Bass Snowman", "mouth_scale": 0.82, "mouth_offset": (-1, 0)},
    "drummer": {"display_name": "Drummer Snowman", "mouth_scale": 0.90, "mouth_offset": (0, 0)},
}


def _scale(value: float, canvas_size: int) -> int:
    return int(round(value * canvas_size / 64.0))


def circle(cx: int, cy: int, radius: int) -> set[Coord]:
    out: set[Coord] = set()
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius**2:
                out.add((x, y))
    return out


def ellipse(cx: int, cy: int, rx: int, ry: int) -> set[Coord]:
    out: set[Coord] = set()
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if ((x - cx) / max(rx, 1)) ** 2 + ((y - cy) / max(ry, 1)) ** 2 <= 1.0:
                out.add((x, y))
    return out


def rect(x0: int, y0: int, x1: int, y1: int) -> set[Coord]:
    return {(x, y) for y in range(min(y0, y1), max(y0, y1) + 1) for x in range(min(x0, x1), max(x0, x1) + 1)}


def line(x0: int, y0: int, x1: int, y1: int, thickness: int = 1) -> set[Coord]:
    out: set[Coord] = set()
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    r = max(0, thickness // 2)
    for idx in range(steps + 1):
        t = idx / steps
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        for yy in range(y - r, y + r + 1):
            for xx in range(x - r, x + r + 1):
                out.add((xx, yy))
    return out


def _base_regions(role: str, canvas: GridCanvas) -> dict[str, PixelRegion]:
    s = canvas.width
    cx = s // 2
    head_center = (cx, _scale(18, s))
    head_radius = max(5, _scale(10, s))
    body_top_center = (cx, _scale(39, s))
    body_bottom_center = (cx, _scale(51, s))
    body_top_rx = max(7, _scale(13, s))
    body_bottom_rx = max(9, _scale(17, s))
    regions = {
        "head": PixelRegion.from_coords("head", "body", circle(*head_center, head_radius), canvas, tags=["snowman", "face_zone"]),
        "mouth_area": PixelRegion.from_coords(
            "mouth_area",
            "face_container",
            rect(cx - _scale(11, s), head_center[1], cx + _scale(11, s), head_center[1] + _scale(7, s)),
            canvas,
            tags=["face", "mouth_container", "artist_override_ok"],
        ),
        "left_arm": PixelRegion.from_coords("left_arm", "limb", line(cx - _scale(10, s), _scale(34, s), cx - _scale(24, s), _scale(26, s), max(1, _scale(2, s))), canvas, tags=["motion", "body"]),
        "right_arm": PixelRegion.from_coords("right_arm", "limb", line(cx + _scale(10, s), _scale(34, s), cx + _scale(24, s), _scale(26, s), max(1, _scale(2, s))), canvas, tags=["motion", "body"]),
        "body_top": PixelRegion.from_coords("body_top", "body", ellipse(*body_top_center, body_top_rx, max(8, _scale(12, s))), canvas, tags=["body"]),
        "body_bottom": PixelRegion.from_coords("body_bottom", "body", ellipse(*body_bottom_center, body_bottom_rx, max(9, _scale(13, s))), canvas, tags=["body", "bass_energy"]),
    }
    if role == "singer":
        regions.update(
            {
                "mic_stand": PixelRegion.from_coords("mic_stand", "instrument", line(cx + _scale(16, s), _scale(22, s), cx + _scale(16, s), _scale(55, s), 1), canvas, tags=["vocals", "prop"]),
                "mic_head": PixelRegion.from_coords("mic_head", "instrument", circle(cx + _scale(14, s), _scale(21, s), max(1, _scale(2, s))), canvas, tags=["vocals", "prop"]),
                "scarf": PixelRegion.from_coords("scarf", "costume", rect(cx - _scale(7, s), _scale(27, s), cx + _scale(7, s), _scale(29, s)), canvas, tags=["costume"]),
            }
        )
    elif role == "guitarist":
        regions.update(
            {
                "guitar_body": PixelRegion.from_coords("guitar_body", "instrument", ellipse(cx + _scale(9, s), _scale(39, s), max(4, _scale(6, s)), max(5, _scale(8, s))), canvas, tags=["guitar", "stem_other"]),
                "guitar_neck": PixelRegion.from_coords("guitar_neck", "instrument", line(cx + _scale(12, s), _scale(33, s), cx + _scale(28, s), _scale(25, s), max(1, _scale(2, s))), canvas, tags=["guitar", "fret"]),
                "guitar_headstock": PixelRegion.from_coords("guitar_headstock", "instrument", rect(cx + _scale(27, s), _scale(22, s), cx + _scale(30, s), _scale(26, s)), canvas, tags=["guitar"]),
                "strum_zone": PixelRegion.from_coords("strum_zone", "instrument_target", ellipse(cx + _scale(8, s), _scale(39, s), max(2, _scale(3, s)), max(2, _scale(4, s))), canvas, tags=["strum", "timing_target"]),
                "fret_zone": PixelRegion.from_coords("fret_zone", "instrument_target", rect(cx + _scale(17, s), _scale(27, s), cx + _scale(24, s), _scale(31, s)), canvas, tags=["fret", "timing_target"]),
            }
        )
    elif role == "bassist":
        regions.update(
            {
                "bass_body": PixelRegion.from_coords("bass_body", "instrument", ellipse(cx + _scale(11, s), _scale(42, s), max(5, _scale(7, s)), max(10, _scale(15, s))), canvas, tags=["bass", "stem_bass"]),
                "bass_neck": PixelRegion.from_coords("bass_neck", "instrument", line(cx + _scale(12, s), _scale(17, s), cx + _scale(12, s), _scale(33, s), max(1, _scale(2, s))), canvas, tags=["bass", "neck"]),
                "bass_scroll": PixelRegion.from_coords("bass_scroll", "instrument", circle(cx + _scale(12, s), _scale(14, s), max(1, _scale(3, s))), canvas, tags=["bass"]),
                "pluck_zone": PixelRegion.from_coords("pluck_zone", "instrument_target", ellipse(cx + _scale(8, s), _scale(39, s), max(2, _scale(3, s)), max(2, _scale(4, s))), canvas, tags=["pluck", "timing_target"]),
                "neck_zone": PixelRegion.from_coords("neck_zone", "instrument_target", rect(cx + _scale(9, s), _scale(21, s), cx + _scale(15, s), _scale(31, s)), canvas, tags=["neck_hand", "timing_target"]),
            }
        )
    elif role == "drummer":
        regions.update(
            {
                "kick": PixelRegion.from_coords("kick", "drum", circle(cx, _scale(49, s), max(5, _scale(7, s))), canvas, tags=["drums", "kick"]),
                "snare": PixelRegion.from_coords("snare", "drum", ellipse(cx - _scale(12, s), _scale(39, s), max(3, _scale(5, s)), max(2, _scale(3, s))), canvas, tags=["drums", "snare"]),
                "tom": PixelRegion.from_coords("tom", "drum", ellipse(cx + _scale(11, s), _scale(38, s), max(3, _scale(5, s)), max(2, _scale(3, s))), canvas, tags=["drums", "tom"]),
                "cymbal": PixelRegion.from_coords("cymbal", "drum", ellipse(cx + _scale(19, s), _scale(29, s), max(4, _scale(7, s)), max(1, _scale(2, s))), canvas, tags=["drums", "cymbal"]),
                "hi_hat": PixelRegion.from_coords("hi_hat", "drum", ellipse(cx - _scale(21, s), _scale(30, s), max(4, _scale(6, s)), max(1, _scale(2, s))), canvas, tags=["drums", "hihat"]),
                "left_stick": PixelRegion.from_coords("left_stick", "drumstick", line(cx - _scale(10, s), _scale(28, s), cx - _scale(22, s), _scale(18, s), 1), canvas, tags=["drums", "stick"]),
                "right_stick": PixelRegion.from_coords("right_stick", "drumstick", line(cx + _scale(10, s), _scale(28, s), cx + _scale(22, s), _scale(18, s), 1), canvas, tags=["drums", "stick"]),
            }
        )
    return regions


def _mouth_anchor(canvas_size: int, role: str) -> Coord:
    meta = ROLE_METADATA[role]
    ox, oy = meta["mouth_offset"]
    return (canvas_size // 2 + _scale(ox, canvas_size), _scale(21, canvas_size) + _scale(oy, canvas_size))


def validate_mouth_inside_head(model: DrawableModelTemplate) -> list[str]:
    head = set(model.base_regions["head"].coordinates)
    issues: list[str] = []
    for name, region in model.mouth_regions.items():
        outside = [coord for coord in region.coordinates if coord not in head]
        if outside:
            issues.append(f"{model.id}:{name} has {len(outside)} pixels outside head")
    return issues


def _mouth_regions(role: str, canvas: GridCanvas) -> dict[str, PixelRegion]:
    scale = float(ROLE_METADATA[role]["mouth_scale"])
    box_w, box_h = default_mouth_box(canvas.width, scale)
    library = generate_mouth_library(canvas.width, scale)
    anchor = _mouth_anchor(canvas.width, role)
    regions = {}
    for name, shape in library.items():
        coords = place_mouth_shape(shape, anchor=anchor, box_width=box_w, box_height=box_h)
        regions[name] = PixelRegion.from_coords(name, "mouth", coords, canvas, tags=["singing_face", "phoneme", *shape.style_tags])
    return regions


def _collect_coords(regions: dict[str, PixelRegion], names: Iterable[str]) -> list[Coord]:
    coords: set[Coord] = set()
    for name in names:
        region = regions.get(name)
        if region:
            coords.update(region.coordinates)
    return sorted(coords)


def _submodel(name: str, category: str, regions: dict[str, PixelRegion], included: list[str], sequencing: list[str], stems: list[str]) -> SubmodelTemplate:
    coords = _collect_coords(regions, included)
    return SubmodelTemplate(
        name=name,
        category=category,
        included_regions=included,
        included_coordinates=coords,
        sequencing_tags=sequencing,
        audio_stem_tags=stems,
        export_grouping_metadata={
            "xlights_hint": "submodel_node_ranges",
            "intended_as_submodel": True,
            "may_export_as_node_ranges": True,
            "likely_timing_target": bool({"mouth", "instrument", "drum"} & set(sequencing + stems)),
        },
    )


def generate_submodels(role: str, regions: dict[str, PixelRegion]) -> dict[str, SubmodelTemplate]:
    submodels: dict[str, SubmodelTemplate] = {}
    base_names = ["head", "mouth_area", "left_arm", "right_arm", "body_top", "body_bottom"]
    for name in ["head", "left_arm", "right_arm", "body_top", "body_bottom"]:
        submodels[name] = _submodel(name, "body", regions, [name], ["body"], [])
    for mouth in ["mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP"]:
        submodels[mouth] = _submodel(mouth, "mouth", regions, [mouth], ["mouth", "singing_face"], ["vocals"])
    role_specific = {
        "singer": ["mic_stand", "mic_head"],
        "guitarist": ["guitar_body", "guitar_neck", "guitar_headstock", "strum_zone", "fret_zone"],
        "bassist": ["bass_body", "bass_neck", "bass_scroll", "pluck_zone", "neck_zone"],
        "drummer": ["kick", "snare", "tom", "cymbal", "hi_hat", "left_stick", "right_stick"],
    }[role]
    for name in role_specific:
        category = "drum" if role == "drummer" else "instrument"
        stems = ["drums"] if role == "drummer" else ["bass"] if role == "bassist" else ["vocals"] if role == "singer" else ["other"]
        submodels[name] = _submodel(name, category, regions, [name], [category, "timing_target"], stems)
    submodels["mouth_all"] = _submodel("mouth_all", "composite", regions, ["mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP"], ["mouth", "face_definition"], ["vocals"])
    instrument_regions = [name for name in role_specific if name not in {"left_stick", "right_stick"}]
    if role == "drummer":
        submodels["drumkit_all"] = _submodel("drumkit_all", "composite", regions, instrument_regions, ["drumkit"], ["drums"])
    else:
        submodels["instrument_all"] = _submodel("instrument_all", "composite", regions, instrument_regions, ["instrument"], ["vocals" if role == "singer" else "bass" if role == "bassist" else "other"])
    submodels["band_body_core"] = _submodel("band_body_core", "composite", regions, base_names, ["body_core"], [])
    return submodels


def build_snowman_template(role: str, canvas_size: int = 64) -> DrawableModelTemplate:
    if role not in ROLE_METADATA:
        raise ValueError(f"Unknown snowman role: {role}")
    if canvas_size not in STANDARD_CANVAS_SIZES:
        raise ValueError(f"Unsupported canvas size {canvas_size}; expected one of {STANDARD_CANVAS_SIZES}")
    canvas = GridCanvas(canvas_size, canvas_size)
    base_regions = _base_regions(role, canvas)
    mouth_regions = _mouth_regions(role, canvas)
    all_regions = {**base_regions, **mouth_regions}
    submodels = generate_submodels(role, all_regions)
    return DrawableModelTemplate(
        id=f"snowman_band_{role}_{canvas_size}",
        display_name=str(ROLE_METADATA[role]["display_name"]),
        canvas=canvas,
        base_regions=base_regions,
        mouth_regions=mouth_regions,
        submodels=submodels,
        overlay_rules=[
            {"source": "phoneme_timing_track", "targets": ["mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP"], "mode": "exclusive_mouth_shape"},
            {"source": "stem_reactivity", "targets": ["instrument_all" if role != "drummer" else "drumkit_all"], "mode": "additive_submodel"},
        ],
        export_metadata={
            "schema": "helix.drawable_model_template.v1",
            "xlights_target": "custom_model_with_submodels",
            "recommended_canvas": canvas_size,
            "supported_canvases": list(STANDARD_CANVAS_SIZES),
            "scaling_note": "High-detail faces may not scale cleanly below 48x48; preserve simplified mouth mode for 32x32.",
            "mapping_hints": {
                "mouth_regions": "xLights Faces effect targets, preferably Matrix or Node Ranges",
                "body_instruments": "xLights custom model submodels",
                "node_order": "row_major_top_left_1_based",
                "manual_refinement": "User may refine generated xModel art/submodel ranges inside xLights.",
            },
        },
    )


def build_band_templates(canvas_size: int = 64) -> dict[str, DrawableModelTemplate]:
    return {role: build_snowman_template(role, canvas_size) for role in ("singer", "guitarist", "bassist", "drummer")}


def model_summary(model: DrawableModelTemplate) -> dict[str, object]:
    return {
        "id": model.id,
        "display_name": model.display_name,
        "canvas": asdict(model.canvas),
        "region_count": len(model.all_regions()),
        "mouth_region_counts": {name: len(region.coordinates) for name, region in model.mouth_regions.items()},
        "submodels": sorted(model.submodels),
        "mouth_placement": {
            "mouth_area_bbox": model.base_regions["mouth_area"].bounding_box,
            "head_center": model.base_regions["head"].center_point,
        },
    }
