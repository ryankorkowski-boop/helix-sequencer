from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from models.helixia_props import build_all_helixia_props_export_catalog


DISPLAY_BY_MODEL_TYPE: dict[str, str] = {
    "arch": "Arches",
    "tree": "Tree 360",
    "matrix": "Horiz Matrix",
    "line": "Single Line",
    "candy_cane": "Candy Canes",
    "circle": "Circle",
    "sphere": "Sphere",
    "star": "Star",
    "spinner": "Spinner",
    "icicles": "Icicles",
    "window_frame": "Window Frame",
    "dmx": "DmxGeneral",
    "custom": "Custom",
}

DEFAULT_LAYOUT_GROUP = "Default"
DEFAULT_CONTROLLER = "No Controller"


def _slug(value: object) -> str:
    raw = str(value or "").strip().upper()
    out = []
    previous_underscore = False
    for char in raw:
        if char.isalnum():
            out.append(char)
            previous_underscore = False
        elif not previous_underscore:
            out.append("_")
            previous_underscore = True
    return "".join(out).strip("_") or "ITEM"


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _model_attrs(
    *,
    name: str,
    model_type: str,
    x: float,
    y: float,
    z: float,
    width: float = 24.0,
    height: float = 18.0,
    start_channel: int,
) -> dict[str, str]:
    display = DISPLAY_BY_MODEL_TYPE.get(model_type, "Custom")
    attrs = {
        "name": name,
        "DisplayAs": display,
        "LayoutGroup": DEFAULT_LAYOUT_GROUP,
        "Controller": DEFAULT_CONTROLLER,
        "WorldPosX": f"{x:.3f}",
        "WorldPosY": f"{y:.3f}",
        "WorldPosZ": f"{z:.3f}",
        "X2": f"{width:.3f}",
        "Y2": f"{height:.3f}",
        "Z2": "0.000",
        "RotateX": "0.00000000",
        "RotateY": "0.00000000",
        "RotateZ": "0.00000000",
        "StartChannel": str(start_channel),
        "StringType": "RGB Nodes",
        "StartSide": "B",
        "Dir": "L",
        "Antialias": "1",
        "PixelSize": "2",
        "Transparency": "0",
        "parm1": "1",
        "parm2": "24",
        "parm3": "1",
        "versionNumber": "7",
    }
    if model_type == "matrix":
        attrs.update({"parm1": "24", "parm2": "16", "NumStrings": "24", "NodesPerString": "16"})
    elif model_type == "tree":
        attrs.update({"parm1": "16", "parm2": "50", "NumStrings": "16", "NodesPerString": "50"})
    elif model_type == "arch":
        attrs.update({"parm1": "1", "parm2": "50", "NumArches": "1", "NodesPerArch": "50"})
    elif model_type == "candy_cane":
        attrs.update({"parm1": "1", "parm2": "24", "NumCanes": "1", "NodesPerCane": "24"})
    elif model_type == "spinner":
        attrs.update({"parm1": "8", "parm2": "18", "NumStrings": "8", "NodesPerArm": "18"})
    elif model_type in {"circle", "sphere", "star"}:
        attrs.update({"parm1": "1", "parm2": "48", "NodesPerString": "48"})
    elif model_type == "icicles":
        attrs.update({"parm1": "8", "parm2": "10", "NumStrings": "8", "LightsPerString": "10"})
    elif model_type == "window_frame":
        attrs.update({"parm1": "4", "parm2": "20", "NumStrings": "4", "NodesPerString": "20"})
    elif model_type == "dmx":
        attrs.update({"StringType": "Single Color", "parm1": "1", "parm2": "1"})
    elif model_type == "custom":
        attrs.update({"parm1": "12", "parm2": "12", "CustomWidth": "12", "CustomHeight": "12"})
    return attrs


def _add_submodels(model_el: ET.Element, names: list[str]) -> None:
    for idx, name in enumerate(names, start=1):
        start = ((idx - 1) * 4) + 1
        end = start + 3
        ET.SubElement(model_el, "subModel", {"name": name, "line0": f"{start}-{end}"})


def _default_submodels_for_type(model_type: str) -> list[str]:
    if model_type == "matrix":
        return ["TOP", "CENTER", "BOTTOM", "LEFT", "RIGHT", "BORDER"]
    if model_type == "tree":
        return ["TOP", "MID", "BOTTOM", "LEFT", "RIGHT", "SPIRAL"]
    if model_type == "spinner":
        return ["ARM_01", "ARM_02", "ARM_03", "ARM_04", "INNER", "OUTER"]
    if model_type in {"star", "circle", "sphere"}:
        return ["INNER", "OUTER", "TOP", "BOTTOM"]
    if model_type == "custom":
        return ["HEAD", "BODY", "LEFT", "RIGHT", "CENTER"]
    return []


def _add_model(
    models_el: ET.Element,
    *,
    name: str,
    model_type: str,
    x: float,
    y: float,
    z: float,
    start_channel: int,
    submodels: list[str] | None = None,
) -> str:
    submodel_names = submodels if submodels is not None else _default_submodels_for_type(model_type)
    model_el = ET.SubElement(
        models_el,
        "model",
        _model_attrs(
            name=name,
            model_type=model_type,
            x=x,
            y=y,
            z=z,
            start_channel=start_channel,
        ),
    )
    if submodel_names:
        _add_submodels(model_el, submodel_names)
    ET.SubElement(model_el, "ControllerConnection")
    return name


def _add_group(groups_el: ET.Element, name: str, members: list[str], *, x: float = 0.0, y: float = 0.0) -> None:
    unique = list(dict.fromkeys(member for member in members if member))
    ET.SubElement(
        groups_el,
        "modelGroup",
        {
            "name": name,
            "selected": "0",
            "layout": "minimalGrid",
            "GridSize": "400",
            "LayoutGroup": DEFAULT_LAYOUT_GROUP,
            "models": ",".join(unique),
            "centrex": f"{x:.3f}",
            "centrey": f"{y:.3f}",
        },
    )


def _add_default_preview_sections(root: ET.Element) -> None:
    view_objects_el = ET.SubElement(root, "view_objects")
    ET.SubElement(
        view_objects_el,
        "view_object",
        {
            "DisplayAs": "Gridlines",
            "LayoutGroup": DEFAULT_LAYOUT_GROUP,
            "name": "Gridlines",
            "GridLineSpacing": "50",
            "GridWidth": "1200.0",
            "GridHeight": "900.0",
            "Active": "1",
            "WorldPosX": "0.0000",
            "WorldPosY": "0.0000",
            "WorldPosZ": "0.0000",
            "ScaleX": "1.0000",
            "ScaleY": "1.0000",
            "ScaleZ": "1.0000",
            "RotateX": "-90.00000000",
            "RotateY": "-0.00000000",
            "RotateZ": "0.00000000",
            "versionNumber": "7",
        },
    )
    ET.SubElement(root, "effects", {"version": "0007"})
    ET.SubElement(root, "views")
    ET.SubElement(root, "palettes")


def build_helixia_xlights_layout(payload: dict[str, Any], output_dir: str | Path) -> dict[str, object]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    root = ET.Element("xrgb")
    models_el = ET.SubElement(root, "models")

    all_models: list[str] = []
    house_models: list[str] = []
    special_models: list[str] = []
    stage_models: list[str] = []
    family_groups: dict[str, list[str]] = defaultdict(list)
    lot_groups: dict[str, list[str]] = defaultdict(list)
    start_channel = 1

    def add(
        *,
        name: str,
        model_type: str,
        x: float,
        y: float,
        z: float = 0.0,
        lot_id: str,
        bucket: list[str],
        submodels: list[str] | None = None,
    ) -> None:
        nonlocal start_channel
        added = _add_model(
            models_el,
            name=name,
            model_type=model_type,
            x=x,
            y=y,
            z=z,
            start_channel=start_channel,
            submodels=submodels,
        )
        start_channel += 100
        all_models.append(added)
        bucket.append(added)
        family_groups[model_type].append(added)
        lot_groups[lot_id].append(added)

    for house in payload.get("village_grid", {}).get("houses", []) or []:
        lot_id = str(house.get("lot_id", "house"))
        base_x = _float(house.get("world_x_ft"))
        base_y = _float(house.get("world_y_ft"))
        for idx, model_type in enumerate(list(house.get("model_types", []) or [])):
            offset = (idx - 1) * 24.0
            add(
                name=f"HX_{_slug(lot_id)}_{_slug(model_type)}",
                model_type=str(model_type),
                x=base_x + offset,
                y=base_y,
                lot_id=lot_id,
                bucket=house_models,
            )

    for tree in payload.get("fibonacci_tree_lot", {}).get("trees", []) or []:
        add(
            name=f"HX_FIB_{_slug(tree.get('tree_id'))}",
            model_type="tree",
            x=_float(tree.get("world_x_ft")),
            y=_float(tree.get("world_y_ft")),
            z=8.0,
            lot_id="fibonacci_tree_lot",
            bucket=special_models,
        )

    for lot in payload.get("special_lots", []) or []:
        lot_id = str(lot.get("lot_id", "special"))
        base_x = _float(lot.get("world_x_ft"))
        base_y = _float(lot.get("world_y_ft"))
        bucket = stage_models if "stage" in lot_id or "dj" in lot_id else special_models
        for idx, model_type in enumerate(list(lot.get("model_types", []) or [])):
            add(
                name=f"HX_{_slug(lot_id)}_{_slug(model_type)}",
                model_type=str(model_type),
                x=base_x + ((idx - 1) * 22.0),
                y=base_y,
                z=4.0,
                lot_id=lot_id,
                bucket=bucket,
            )

    props_catalog = build_all_helixia_props_export_catalog()
    prop_x = 250.0
    prop_y = -52.0
    for prop_idx, prop in enumerate(props_catalog["props"]):
        prop_name = str(prop.get("name", "HX_PROP"))
        for model_idx, model in enumerate(prop.get("models", []) or []):
            model_name = str(model.get("name", "HX_PROP_MODEL"))
            category = str(model.get("category", "custom"))
            model_type = "custom"
            if category == "keyboard":
                model_type = "matrix"
            elif category in {"legs", "arms"}:
                model_type = "line"
            submodels = [str(name).removeprefix(f"{model_name}_") for name in list(model.get("submodels", []) or [])]
            add(
                name=model_name,
                model_type=model_type,
                x=prop_x + (prop_idx * 24.0) + (model_idx * 10.0),
                y=prop_y - (prop_idx * 8.0),
                z=12.0,
                lot_id=prop_name,
                bucket=stage_models,
                submodels=submodels,
            )

    _add_default_preview_sections(root)
    groups_el = ET.SubElement(root, "modelGroups")
    _add_group(groups_el, "HELIXIA_ALL", all_models)
    _add_group(groups_el, "HELIXIA_HOUSES", house_models)
    _add_group(groups_el, "HELIXIA_SPECIAL_LOTS", special_models)
    _add_group(groups_el, "HELIXIA_STAGE", stage_models)
    for lot_id, members in sorted(lot_groups.items()):
        _add_group(groups_el, f"HX_LOT_{_slug(lot_id)}", members)
    for model_type, members in sorted(family_groups.items()):
        _add_group(groups_el, f"HX_FAMILY_{_slug(model_type)}", members)
    ET.SubElement(root, "layoutGroups")

    layout_path = out_dir / "xlights_rgbeffects.xml"
    ET.ElementTree(root).write(layout_path, encoding="utf-8", xml_declaration=True)
    return {
        "output_layout": str(layout_path),
        "model_count": len(all_models),
        "group_count": len(root.findall(".//modelGroup")),
        "house_model_count": len(house_models),
        "special_model_count": len(special_models),
        "stage_model_count": len(stage_models),
        "family_count": len(family_groups),
    }
