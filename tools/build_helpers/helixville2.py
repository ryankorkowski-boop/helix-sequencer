from __future__ import annotations

import copy
import json
import re
import shutil
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GP_LAYOUT = ROOT / "xlights_rgbeffects.xml"
DEFAULT_GP_XBKP = ROOT / "xlights_rgbeffects.xbkp"
DEFAULT_NEIGHBOR_LAYOUT = ROOT / "allmodels" / "xlights_rgbeffects.xml"
FEET_TO_WORLD_UNITS = 10.0

_NORTH_CANE_RE = re.compile(r"^north candy cane (\d+)$", re.IGNORECASE)
_SOUTH_CANE_RE = re.compile(r"^south candy cane (\d+)$", re.IGNORECASE)
_LINE_TREE_RE = re.compile(r"^line tree (?:green|red|white) (\d+)$", re.IGNORECASE)
_STAR_RE = re.compile(r"^star\s*(\d+)$", re.IGNORECASE)
_SF_RE = re.compile(r"^sf\s*(\d+)$", re.IGNORECASE)


def _norm(value: str | None) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"\s+", " ", text)


def _parse_float(value: str | None, fallback: float = 0.0) -> float:
    try:
        return float(value if value is not None else fallback)
    except Exception:
        return fallback


def _to_world(value_feet: float) -> float:
    return float(value_feet) * FEET_TO_WORLD_UNITS


def _set_world_pos(model: ET.Element, x_feet: float, y_feet: float, z_feet: float) -> None:
    model.attrib["WorldPosX"] = f"{_to_world(x_feet):.4f}"
    model.attrib["WorldPosY"] = f"{_to_world(y_feet):.4f}"
    model.attrib["WorldPosZ"] = f"{_to_world(z_feet):.4f}"


def _gp_world_bounds(models: list[ET.Element]) -> dict[str, float]:
    xs = [_parse_float(model.attrib.get("WorldPosX"), 0.0) for model in models]
    ys = [_parse_float(model.attrib.get("WorldPosY"), 0.0) for model in models]
    return {
        "x_min": min(xs) if xs else 0.0,
        "x_max": max(xs) if xs else 1.0,
        "y_min": min(ys) if ys else 0.0,
        "y_max": max(ys) if ys else 1.0,
    }


def _default_gp_z_feet(name: str, display_as: str) -> float:
    lowered = _norm(name)
    display = _norm(display_as)
    if lowered.startswith("roof") or "icicle" in lowered:
        return 12.0
    if lowered.startswith("sf") or "snowflake" in lowered:
        return 16.0
    if lowered.startswith("star") or "bethlehem star" in lowered:
        return 18.0
    if lowered.startswith("wreath"):
        return 9.0
    if lowered.startswith("arch"):
        return 2.0
    if "candy cane" in lowered:
        return 1.0
    if lowered.startswith("line tree"):
        return 4.0
    if lowered.startswith("mega tree"):
        return 6.0
    if "blvd" in lowered or "linden" in lowered or lowered.startswith("left tree"):
        return 8.0
    if lowered.startswith("garage trees"):
        return 6.0
    if "flood" in lowered:
        return 2.0
    if display in {"star", "spinner", "sphere"}:
        return 11.0
    if display in {"single line", "poly line"}:
        return 2.0
    return 5.0


def _snowflake_reverse_c_map() -> dict[int, tuple[float, float, float]]:
    # Reverse-C on house face, one floor up.
    points = [
        (18.0, 102.0, 16.0),
        (12.0, 102.0, 16.0),
        (6.0, 102.0, 16.0),
        (0.0, 102.0, 16.0),
        (-6.0, 102.0, 16.0),
        (18.0, 98.0, 16.0),
        (18.0, 94.0, 16.0),
        (18.0, 90.0, 16.0),
        (18.0, 86.0, 16.0),
        (12.0, 86.0, 16.0),
        (6.0, 86.0, 16.0),
        (0.0, 86.0, 16.0),
        (-6.0, 86.0, 16.0),
    ]
    indices = list(range(2, 15))
    return {idx: point for idx, point in zip(indices, points)}


def _explicit_gp_pos_feet(model_name: str) -> tuple[float, float, float] | None:
    name = _norm(model_name)

    match = _NORTH_CANE_RE.match(name)
    if match:
        index = int(match.group(1))
        return (-48.0, 5.0 + ((index - 1) * 6.0), 0.0)

    match = _SOUTH_CANE_RE.match(name)
    if match:
        index = int(match.group(1))
        return (48.0, 5.0 + ((index - 1) * 6.0), 0.0)

    match = _LINE_TREE_RE.match(name)
    if match:
        index = int(match.group(1))
        return (34.0, 20.0 + ((index - 1) * 6.0), 4.0)

    if name.startswith("mega tree"):
        return (24.0, 54.0, 6.0)

    if name.startswith("left tree"):
        return (-62.0, 58.0, 8.0)
    if name.startswith("left blvd"):
        return (-62.0, -8.0, 8.0)
    if name.startswith("center blvd"):
        return (0.0, -8.0, 8.0)
    if name.startswith("right blvd"):
        return (24.0, -8.0, 8.0)
    if name.startswith("right linden"):
        return (70.0, 82.0, 8.0)

    if name.startswith("garage trees"):
        return (30.0, 70.0, 6.0)
    if name == "big snowflake roof":
        return (18.0, 104.0, 15.0)
    if name == "big snowflake garage":
        return (36.0, 92.0, 13.0)
    if "bethlehem star" in name:
        return (4.0, 106.0, 18.0)
    if name == "star":
        return (23.0, 94.0, 17.0)

    star_match = _STAR_RE.match(name)
    if star_match:
        star_index = int(star_match.group(1))
        if 1 <= star_index <= 15:
            # 15 shooting stars at ~20ft, phone pole (left) to roof peak (right).
            t = float(star_index - 1) / 14.0
            x = -96.0 + (116.0 * t)
            y = 82.0 + (10.0 * t)
            return (x, y, 20.0)

    snowflake_match = _SF_RE.match(name)
    if snowflake_match:
        sf_index = int(snowflake_match.group(1))
        snowflake_map = _snowflake_reverse_c_map()
        if sf_index in snowflake_map:
            return snowflake_map[sf_index]
        if sf_index == 1:
            return (22.0, 98.0, 15.5)
    return None


def _default_gp_pos_feet(model: ET.Element, bounds: dict[str, float]) -> tuple[float, float, float]:
    x = _parse_float(model.attrib.get("WorldPosX"), 0.0)
    y = _parse_float(model.attrib.get("WorldPosY"), 0.0)
    x_mid = (bounds["x_min"] + bounds["x_max"]) * 0.5
    x_span = max(1.0, bounds["x_max"] - bounds["x_min"])
    y_span = max(1.0, bounds["y_max"] - bounds["y_min"])

    x_feet = ((x - x_mid) / x_span) * 130.0
    y_feet = (((y - bounds["y_min"]) / y_span) * 78.0) + 10.0
    z_feet = _default_gp_z_feet(model.attrib.get("name", ""), model.attrib.get("DisplayAs", ""))
    return (x_feet, y_feet, z_feet)


def _neighbor_side(model_name: str) -> str | None:
    if model_name.startswith("NBH_LEFT_"):
        return "left"
    if model_name.startswith("NBH_RIGHT_") or model_name.startswith("NBH_WORD_"):
        return "right"
    return None


def _neighbor_z_feet(model: ET.Element) -> float:
    display = _norm(model.attrib.get("DisplayAs", ""))
    if display in {"tree 360"}:
        return 10.0
    if display in {"spinner", "sphere", "star"}:
        return 14.0
    if display in {"horiz matrix", "window frame", "image", "custom"}:
        return 8.0
    if display in {"arches", "candy canes", "poly line", "single line", "circle"}:
        return 2.5
    return 6.0


def _source_neighbor_centers(models: list[ET.Element]) -> dict[str, tuple[float, float]]:
    accum: dict[str, list[tuple[float, float]]] = {"left": [], "right": []}
    for model in models:
        name = str(model.attrib.get("name", ""))
        side = _neighbor_side(name)
        if side is None:
            continue
        accum[side].append(
            (
                _parse_float(model.attrib.get("WorldPosX"), 0.0),
                _parse_float(model.attrib.get("WorldPosY"), 0.0),
            )
        )
    out: dict[str, tuple[float, float]] = {}
    for side, points in accum.items():
        if not points:
            out[side] = (0.0, 0.0)
            continue
        out[side] = (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        )
    return out


def _neighbor_target_center_feet(side: str) -> tuple[float, float]:
    if side == "left":
        return (-185.0, 44.0)
    return (185.0, 44.0)


def _upsert_model_group(root: ET.Element, name: str, model_names: list[str]) -> None:
    if not model_names:
        return
    model_groups = root.find("modelGroups")
    if model_groups is None:
        model_groups = ET.SubElement(root, "modelGroups")
    existing = None
    for group in model_groups.findall("modelGroup"):
        if group.attrib.get("name") == name:
            existing = group
            break
    payload = ",".join(model_names)
    attrs = {
        "name": name,
        "layout": "minimalGrid",
        "GridSize": "400",
        "LayoutGroup": "All Previews",
        "models": payload,
    }
    if existing is None:
        ET.SubElement(model_groups, "modelGroup", attrs)
        return
    existing.attrib.update(attrs)


def build_helixville2_layout(
    *,
    source_layout: Path = DEFAULT_GP_LAYOUT,
    neighbor_layout: Path = DEFAULT_NEIGHBOR_LAYOUT,
    output_dir: Path | None = None,
) -> dict[str, object]:
    source_layout = source_layout.resolve()
    neighbor_layout = neighbor_layout.resolve()
    output_dir = (output_dir or (ROOT / "helixville2")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_tree = ET.parse(source_layout)
    source_root = source_tree.getroot()
    models_parent = source_root.find("models")
    if models_parent is None:
        raise ValueError("Source GP layout is missing <models> section.")

    gp_models = list(models_parent.findall("model"))
    gp_bounds = _gp_world_bounds(gp_models)
    explicit_placements = 0

    gp_model_names: list[str] = []
    for model in gp_models:
        model_name = str(model.attrib.get("name", ""))
        gp_model_names.append(model_name)
        explicit = _explicit_gp_pos_feet(model_name)
        if explicit is not None:
            explicit_placements += 1
            _set_world_pos(model, *explicit)
        else:
            _set_world_pos(model, *_default_gp_pos_feet(model, gp_bounds))

    neighbor_tree = ET.parse(neighbor_layout)
    neighbor_root = neighbor_tree.getroot()
    neighbor_models_source = [
        model
        for model in neighbor_root.findall(".//model")
        if _neighbor_side(str(model.attrib.get("name", ""))) is not None
    ]

    source_neighbor_centers = _source_neighbor_centers(neighbor_models_source)
    neighbor_imported: list[str] = []
    side_counts: Counter[str] = Counter()

    for model in neighbor_models_source:
        model_name = str(model.attrib.get("name", ""))
        side = _neighbor_side(model_name)
        if side is None:
            continue
        copied = copy.deepcopy(model)
        src_center_x, src_center_y = source_neighbor_centers[side]
        src_x = _parse_float(copied.attrib.get("WorldPosX"), 0.0)
        src_y = _parse_float(copied.attrib.get("WorldPosY"), 0.0)
        target_center_x_ft, target_center_y_ft = _neighbor_target_center_feet(side)
        x_feet = target_center_x_ft + ((src_x - src_center_x) * 0.08)
        y_feet = target_center_y_ft + ((src_y - src_center_y) * 0.08)
        z_feet = _neighbor_z_feet(copied)
        _set_world_pos(copied, x_feet, y_feet, z_feet)
        models_parent.append(copied)
        neighbor_imported.append(model_name)
        side_counts[side] += 1

    left_neighbor_names = [name for name in neighbor_imported if name.startswith("NBH_LEFT_")]
    right_neighbor_names = [
        name
        for name in neighbor_imported
        if name.startswith("NBH_RIGHT_") or name.startswith("NBH_WORD_")
    ]
    aerial_names = []
    for name in gp_model_names:
        normalized = _norm(name)
        if _STAR_RE.match(normalized) or (_SF_RE.match(normalized) and normalized != "sf1"):
            aerial_names.append(name)
        elif normalized in {"star", "big snowflake roof", "big snowflake garage"}:
            aerial_names.append(name)

    _upsert_model_group(source_root, "HV2_GP_AERIAL", aerial_names)
    _upsert_model_group(source_root, "HV2_NEIGHBOR_LEFT_COMMON", left_neighbor_names)
    _upsert_model_group(source_root, "HV2_NEIGHBOR_RIGHT_COMMON", right_neighbor_names)
    _upsert_model_group(
        source_root,
        "HV2_GP_CORE_LANDMARKS",
        [
            "Left Tree White",
            "Left Tree Red",
            "Left Tree Green",
            "Left Blvd Red",
            "Left Blvd Green",
            "Left Blvd White",
            "Center Blvd Green",
            "Center Blvd Red",
            "Center Blvd White",
            "Right Blvd Red",
            "Right Blvd Green",
            "Right Blvd White",
            "Right Linden White",
            "Right Linden Red",
            "Right Linden Green",
        ],
    )

    layout_out = output_dir / "xlights_rgbeffects.xml"
    backup_out = output_dir / "xlights_rgbeffects.source_backup.xml"
    xbkp_out = output_dir / "xlights_rgbeffects.xbkp"
    manifest_out = output_dir / "helixville2_manifest.json"
    notes_out = output_dir / "HELIXVILLE2_LAYOUT_NOTES.txt"

    source_tree.write(layout_out, encoding="utf-8", xml_declaration=True)
    shutil.copy2(source_layout, backup_out)
    if DEFAULT_GP_XBKP.exists():
        shutil.copy2(DEFAULT_GP_XBKP, xbkp_out)

    final_models = source_root.findall(".//model")
    z_values = [_parse_float(model.attrib.get("WorldPosZ"), 0.0) for model in final_models]
    manifest = {
        "layout_name": "helixville2",
        "source_layout": str(source_layout),
        "neighbor_layout": str(neighbor_layout),
        "output_layout": str(layout_out),
        "source_backup": str(backup_out),
        "output_xbkp": str(xbkp_out) if xbkp_out.exists() else "",
        "gp_model_count": len(gp_models),
        "neighbor_imported_count": len(neighbor_imported),
        "neighbor_import_counts": dict(side_counts),
        "total_model_count": len(final_models),
        "explicit_gp_placements": explicit_placements,
        "z_world_range": {
            "min": round(min(z_values), 4) if z_values else 0.0,
            "max": round(max(z_values), 4) if z_values else 0.0,
        },
        "placement_notes": [
            "Orientation uses left driveway edge as North and right driveway edge as South.",
            "North/South candy canes are spaced 6ft apart in physical mapping coordinates.",
            "15 shooting stars are mapped 20ft high from left phone-pole anchor to house peak.",
            "sf2..sf14 map to a reverse-C second-story snowflake arc.",
            "Neighbor districts import legal in-workspace NBH models from allmodels for prop coverage tests.",
        ],
    }
    manifest_out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    notes = [
        "HELIXVILLE2 3D TEST LAYOUT",
        "",
        f"Source GP layout: {source_layout}",
        f"Neighbor source layout: {neighbor_layout}",
        f"Output layout: {layout_out}",
        "",
        "Physical intent:",
        "- Preserve GP's original 256 channel map as the base model list.",
        "- Convert to a structured 3D yard orientation (North=left driveway side, South=right driveway side).",
        "- Place GP landmark zones from user sketch: Left Tree, Left/Center/Right Blvd, Right Linden, Line Trees, Mega Tree.",
        "- Map aerial details: 15 shooting stars and reverse-C snowflake set.",
        "- Import a broad common-prop neighbor pack (arches, matrices, trees, canes, stars, spinners, spheres, images/custom).",
        "",
        "Quick model-group handles:",
        "- HV2_GP_AERIAL",
        "- HV2_GP_CORE_LANDMARKS",
        "- HV2_NEIGHBOR_LEFT_COMMON",
        "- HV2_NEIGHBOR_RIGHT_COMMON",
    ]
    notes_out.write_text("\n".join(notes) + "\n", encoding="utf-8")
    return manifest
