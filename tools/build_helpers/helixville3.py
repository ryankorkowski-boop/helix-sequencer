from __future__ import annotations

import copy
import json
import re
import shutil
from collections import Counter, defaultdict
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

_SUPPLEMENTAL_DISPLAY_ALLOW = {
    "Arches",
    "Custom",
    "Horiz Matrix",
    "Image",
    "Sphere",
    "Spinner",
    "Star",
    "Tree 360",
    "Window Frame",
}
_SUPPLEMENTAL_LIMIT_PER_DISPLAY = 4


def _norm(value: str | None) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
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


def _snowflake_reverse_c_map() -> dict[int, tuple[float, float, float]]:
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


def _is_gp_aerial(model_name: str) -> bool:
    name = _norm(model_name)
    if _STAR_RE.match(name):
        return True
    if _SF_RE.match(name):
        return True
    return name in {"star", "big snowflake roof", "big snowflake garage"}


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
        return (34.0, 20.0 + ((index - 1) * 6.0), 0.0)

    if name.startswith("mega tree"):
        return (24.0, 54.0, 0.0)

    if name.startswith("left tree"):
        return (-62.0, 58.0, 0.0)
    if name.startswith("left blvd"):
        return (-62.0, -8.0, 0.0)
    if name.startswith("center blvd"):
        return (0.0, -8.0, 0.0)
    if name.startswith("right blvd"):
        return (24.0, -8.0, 0.0)
    if name.startswith("right linden"):
        return (70.0, 82.0, 0.0)

    if name.startswith("garage trees"):
        return (30.0, 70.0, 0.0)
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
    z_feet = 0.0
    return (x_feet, y_feet, z_feet)


def _neighbor_side(model_name: str, fallback: str = "right") -> str:
    if model_name.startswith("NBH_LEFT_"):
        return "left"
    if model_name.startswith("NBH_RIGHT_") or model_name.startswith("NBH_WORD_"):
        return "right"
    return fallback


def _neighbor_category(model: ET.Element) -> str:
    name = _norm(model.attrib.get("name", ""))
    display = _norm(model.attrib.get("DisplayAs", ""))
    if "singing face" in name:
        return "face"
    if "word" in name:
        return "word"
    if "mega" in name:
        return "mega"
    if display in {"horiz matrix", "vert matrix", "matrix"}:
        return "matrix"
    if display in {"arches"}:
        return "arch"
    if display in {"candy canes"}:
        return "cane"
    if display in {"spinner"}:
        return "spinner"
    if display in {"sphere"}:
        return "sphere"
    if display in {"star"}:
        return "star"
    if display in {"tree 360", "tree flat"}:
        return "tree"
    if display in {"window frame"}:
        return "window"
    if display in {"image"}:
        return "image"
    if display in {"custom"}:
        return "custom"
    if display in {"single line", "poly line"}:
        return "line"
    return "misc"


def _neighbor_z_feet(category: str) -> float:
    if category in {"matrix", "face", "window", "word", "image", "custom"}:
        return 8.0
    if category in {"star", "spinner", "sphere"}:
        return 4.0
    return 0.0


def _sanitize_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:56] if len(cleaned) > 56 else cleaned


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
        "GridSize": "480",
        "LayoutGroup": "All Previews",
        "models": payload,
    }
    if existing is None:
        ET.SubElement(model_groups, "modelGroup", attrs)
    else:
        existing.attrib.update(attrs)


def _iter_neighbor_source_models(
    *,
    neighbor_root: ET.Element,
    gp_names: set[str],
) -> list[ET.Element]:
    selected: list[ET.Element] = []
    supplemental_counts: Counter[str] = Counter()
    for model in neighbor_root.findall(".//model"):
        name = str(model.attrib.get("name", "")).strip()
        if not name:
            continue
        if name.startswith("NBH_LEFT_") or name.startswith("NBH_RIGHT_") or name.startswith("NBH_WORD_"):
            selected.append(copy.deepcopy(model))
            continue
        if name in gp_names:
            continue
        display = str(model.attrib.get("DisplayAs", "")).strip()
        if display not in _SUPPLEMENTAL_DISPLAY_ALLOW:
            continue
        if supplemental_counts[display] >= _SUPPLEMENTAL_LIMIT_PER_DISPLAY:
            continue
        copied = copy.deepcopy(model)
        copied.attrib["name"] = f"HV3_IMPORT_{_sanitize_name(name)}"
        selected.append(copied)
        supplemental_counts[display] += 1
    return selected


def build_helixville3_layout(
    *,
    source_layout: Path = DEFAULT_GP_LAYOUT,
    neighbor_layout: Path = DEFAULT_NEIGHBOR_LAYOUT,
    output_dir: Path | None = None,
) -> dict[str, object]:
    source_layout = source_layout.resolve()
    neighbor_layout = neighbor_layout.resolve()
    output_dir = (output_dir or (ROOT / "helixville3")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_tree = ET.parse(source_layout)
    source_root = source_tree.getroot()
    models_parent = source_root.find("models")
    if models_parent is None:
        raise ValueError("Source GP layout is missing <models> section.")

    gp_models = list(models_parent.findall("model"))
    gp_model_names: list[str] = []
    gp_name_set: set[str] = set()
    gp_bounds = _gp_world_bounds(gp_models)
    gp_explicit_placements = 0
    gp_ground_aligned = 0
    gp_aerial_aligned = 0

    for model in gp_models:
        model_name = str(model.attrib.get("name", ""))
        gp_model_names.append(model_name)
        gp_name_set.add(model_name)
        explicit = _explicit_gp_pos_feet(model_name)
        if explicit is not None:
            gp_explicit_placements += 1
            x_feet, y_feet, z_feet = explicit
        else:
            x_feet, y_feet, z_feet = _default_gp_pos_feet(model, gp_bounds)
        if not _is_gp_aerial(model_name):
            z_feet = 0.0
            gp_ground_aligned += 1
        else:
            gp_aerial_aligned += 1
        _set_world_pos(model, x_feet, y_feet, z_feet)

    neighbor_tree = ET.parse(neighbor_layout)
    neighbor_root = neighbor_tree.getroot()
    neighbor_models = _iter_neighbor_source_models(neighbor_root=neighbor_root, gp_names=gp_name_set)

    category_rows = [
        "word",
        "face",
        "matrix",
        "image",
        "custom",
        "mega",
        "tree",
        "arch",
        "cane",
        "spinner",
        "sphere",
        "star",
        "window",
        "line",
        "misc",
    ]
    row_index = {category: idx for idx, category in enumerate(category_rows)}
    side_x_start = {"left": -360.0, "right": 160.0}
    side_fallback = {"left": 0, "right": 0}
    side_col_count = defaultdict(int)
    category_counts = Counter()
    side_counts = Counter()
    imported_names: list[str] = []
    imported_by_side: dict[str, list[str]] = {"left": [], "right": []}
    imported_by_category: dict[str, list[str]] = defaultdict(list)
    existing_names = set(gp_name_set)

    # Place each imported model into deterministic side/category rows.
    for model in neighbor_models:
        model_name = str(model.attrib.get("name", "")).strip()
        category = _neighbor_category(model)
        preferred_side = _neighbor_side(model_name, fallback="right" if category in {"face", "matrix", "image", "custom", "word"} else "left")
        side = preferred_side if preferred_side in {"left", "right"} else ("left" if side_fallback["left"] <= side_fallback["right"] else "right")
        side_fallback[side] += 1

        unique_name = model_name
        dedupe_idx = 2
        while unique_name in existing_names:
            unique_name = f"{model_name}_HV3_{dedupe_idx}"
            dedupe_idx += 1
        model.attrib["name"] = unique_name
        existing_names.add(unique_name)

        count = side_col_count[(side, category)]
        base_row = row_index.get(category, row_index["misc"])
        row = base_row + (count // 8)
        col = count % 8
        side_col_count[(side, category)] += 1

        x_feet = side_x_start[side] + (col * 24.0)
        y_feet = 4.0 + (row * 14.0)
        z_feet = _neighbor_z_feet(category)
        _set_world_pos(model, x_feet, y_feet, z_feet)
        models_parent.append(model)

        imported_names.append(unique_name)
        imported_by_side[side].append(unique_name)
        imported_by_category[category].append(unique_name)
        category_counts[category] += 1
        side_counts[side] += 1

    gp_aerial = [name for name in gp_model_names if _is_gp_aerial(name)]
    singing_faces = sorted(imported_by_category.get("face", []), key=lambda value: _norm(value))
    lyric_marquee = (
        sorted(imported_by_category.get("matrix", []), key=lambda value: _norm(value))[:10]
        + sorted(imported_by_category.get("word", []), key=lambda value: _norm(value))
        + sorted(imported_by_category.get("image", []), key=lambda value: _norm(value))[:2]
    )
    lyric_marquee = list(dict.fromkeys(lyric_marquee))

    _upsert_model_group(source_root, "HV3_GP_AERIAL", gp_aerial)
    _upsert_model_group(source_root, "HV3_NEIGHBOR_LEFT_COMMON", imported_by_side["left"])
    _upsert_model_group(source_root, "HV3_NEIGHBOR_RIGHT_COMMON", imported_by_side["right"])
    _upsert_model_group(source_root, "HV3_SINGING_FACES", singing_faces)
    _upsert_model_group(source_root, "HV3_LYRIC_MARQUEE", lyric_marquee)
    _upsert_model_group(source_root, "HV3_ALL_IMPORTED", imported_names)
    _upsert_model_group(
        source_root,
        "HV3_GP_CORE_LANDMARKS",
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
            "Mega Tree Red 1",
            "Mega Tree Green 1",
            "Mega Tree White 1",
            "Line Tree Red 1",
            "Line Tree Green 1",
            "Line Tree White 1",
        ],
    )

    layout_out = output_dir / "xlights_rgbeffects.xml"
    backup_out = output_dir / "xlights_rgbeffects.source_backup.xml"
    xbkp_out = output_dir / "xlights_rgbeffects.xbkp"
    manifest_out = output_dir / "helixville3_manifest.json"
    notes_out = output_dir / "HELIXVILLE3_LAYOUT_NOTES.txt"

    source_tree.write(layout_out, encoding="utf-8", xml_declaration=True)
    shutil.copy2(source_layout, backup_out)
    if DEFAULT_GP_XBKP.exists():
        shutil.copy2(DEFAULT_GP_XBKP, xbkp_out)

    final_models = source_root.findall(".//model")
    z_values = [_parse_float(model.attrib.get("WorldPosZ"), 0.0) for model in final_models]

    manifest = {
        "layout_name": "helixville3",
        "source_layout": str(source_layout),
        "neighbor_layout": str(neighbor_layout),
        "output_layout": str(layout_out),
        "source_backup": str(backup_out),
        "output_xbkp": str(xbkp_out) if xbkp_out.exists() else "",
        "gp_model_count": len(gp_models),
        "gp_explicit_placements": gp_explicit_placements,
        "gp_ground_aligned_count": gp_ground_aligned,
        "gp_aerial_aligned_count": gp_aerial_aligned,
        "neighbor_imported_count": len(imported_names),
        "neighbor_import_counts_by_side": dict(side_counts),
        "neighbor_import_counts_by_category": dict(sorted(category_counts.items(), key=lambda item: item[0])),
        "lyric_marquee_models": lyric_marquee,
        "singing_face_models": singing_faces,
        "total_model_count": len(final_models),
        "z_world_range": {
            "min": round(min(z_values), 4) if z_values else 0.0,
            "max": round(max(z_values), 4) if z_values else 0.0,
        },
        "placement_notes": [
            "GP legacy 256-channel house remains the baseline and is remapped onto a coherent 3D yard frame.",
            "Ground props are aligned to ground-level (Z=0) except explicit aerial shooting stars and snowflake roof arc.",
            "Neighbor districts import legal in-workspace allmodels/NBH assets for broad common-prop coverage.",
            "Dedicated singing-face and lyric-marquee groups are provided for lyric sync testing.",
        ],
    }
    manifest_out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    notes = [
        "HELIXVILLE3 3D TEST LAYOUT",
        "",
        f"Source GP layout: {source_layout}",
        f"Neighbor source layout: {neighbor_layout}",
        f"Output layout: {layout_out}",
        "",
        "Intent:",
        "- Base on GP legacy 256-channel layout and keep naming/channel continuity.",
        "- Align ground props to the ground plane for clean 3D sanity checks.",
        "- Import broad common props from allmodels/NBH districts (trees, arches, canes, stars, matrices, spinners, faces, custom/image).",
        "- Add explicit lyric routing groups for marquee text + singing faces.",
        "",
        "Quick model groups:",
        "- HV3_GP_AERIAL",
        "- HV3_NEIGHBOR_LEFT_COMMON",
        "- HV3_NEIGHBOR_RIGHT_COMMON",
        "- HV3_SINGING_FACES",
        "- HV3_LYRIC_MARQUEE",
        "- HV3_ALL_IMPORTED",
        "",
        "Sequencing hint:",
        "- For lyric text routing, run with --sync-lyrics-heads and target HV3_LYRIC_MARQUEE/HV3_SINGING_FACES groups.",
    ]
    notes_out.write_text("\n".join(notes) + "\n", encoding="utf-8")
    return manifest
