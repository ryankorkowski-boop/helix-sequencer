# Helixia Spatial Refactor v2 – xLights Builder Alignment

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

DISPLAY_BY_MODEL_TYPE = {
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


def _float(v: object, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _model_attrs(name: str, model_type: str, x: float, y: float, z: float, start_channel: int) -> dict[str, str]:
    return {
        "name": name,
        "DisplayAs": DISPLAY_BY_MODEL_TYPE.get(model_type, "Custom"),
        "WorldPosX": f"{x:.3f}",
        "WorldPosY": f"{y:.3f}",
        "WorldPosZ": f"{z:.3f}",
        "StartChannel": str(start_channel),
        "StringType": "RGB Nodes",
    }


def build_helixia_xlights_layout(payload: dict[str, Any], output_dir: str | Path) -> dict[str, object]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    root = ET.Element("xrgb")
    models_el = ET.SubElement(root, "models")
    groups_el = ET.SubElement(root, "modelGroups")

    all_models = []
    house_models = []
    special_models = []
    start_channel = 1

    def add(name: str, model_type: str, x: float, y: float, z: float, bucket: list[str]):
        nonlocal start_channel
        ET.SubElement(models_el, "model", _model_attrs(name, model_type, x, y, z, start_channel))
        start_channel += 100
        all_models.append(name)
        bucket.append(name)

    # Houses
    for house in payload.get("houses", []):
        base_x = _float(house.get("world_x_ft"))
        base_y = _float(house.get("world_y_ft"))
        name = f"HX_{house.get('lot_id')}"
        add(name, "matrix", base_x, base_y, 0.0, house_models)

    # Fibonacci Trees
    for tree in payload.get("fibonacci_trees", []):
        add(f"HX_{tree.get('tree_id')}", "tree", _float(tree.get("world_x_ft")), _float(tree.get("world_y_ft")), 8.0, special_models)

    # Helix Tower
    for segment in payload.get("helix_tower", []):
        add(f"HX_{segment.get('segment_id')}", "line", _float(segment.get("world_x_ft")), _float(segment.get("world_y_ft")), _float(segment.get("world_z_ft")), special_models)

    # Special Lots
    for lot in payload.get("special_lots", []):
        add(f"HX_{lot.get('lot_id')}", "custom", _float(lot.get("world_x_ft")), _float(lot.get("world_y_ft")), 0.0, special_models)

    # Groups
    ET.SubElement(groups_el, "modelGroup", {"name": "HELIXIA_ALL", "models": ",".join(all_models)})
    ET.SubElement(groups_el, "modelGroup", {"name": "HELIXIA_HOUSES", "models": ",".join(house_models)})
    ET.SubElement(groups_el, "modelGroup", {"name": "HELIXIA_SPECIAL_LOTS", "models": ",".join(special_models)})

    layout_path = out_dir / "xlights_rgbeffects.xml"
    ET.ElementTree(root).write(layout_path, encoding="utf-8", xml_declaration=True)

    return {
        "output_layout": str(layout_path),
        "model_count": len(all_models),
        "group_count": 3,
    }
