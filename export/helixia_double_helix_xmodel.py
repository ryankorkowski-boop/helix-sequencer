from __future__ import annotations

import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from models.helixia_double_helix import DoubleHelixConfig, build_giant_double_helix


def _grid_index(value: float, lo: float, hi: float, size: int) -> int:
    if hi <= lo:
        return 0
    return max(0, min(size - 1, round((value - lo) / (hi - lo) * (size - 1))))


def build_xmodel(config: DoubleHelixConfig = DoubleHelixConfig()) -> ET.Element:
    model = build_giant_double_helix(config)
    points = model["strand_a"] + model["strand_b"]
    # xLights custom 3D models are represented as sparse nodes in a grid of layers.
    # Use a compact quantized spatial volume rather than flattening the helix to 2D.
    width = 49
    height = max(2, int(round(config.height_ft)) + 1)
    depth = 49
    xmin, xmax = -config.radius_ft, config.radius_ft
    zmin, zmax = -config.radius_ft, config.radius_ft

    nodes: list[tuple[int, int, int, int]] = []
    node_no = 1
    for p in points:
        col = _grid_index(p["world_x_ft"], xmin, xmax, width)
        row = _grid_index(p["world_y_ft"], config.base_y_ft, config.base_y_ft + config.height_ft, height)
        layer = _grid_index(p["world_z_ft"], zmin, zmax, depth)
        nodes.append((node_no, row, col, layer))
        node_no += 1

    # Rungs are represented by their midpoint nodes. They remain distinct output nodes
    # so the Helixia rung submodel can be addressed independently.
    for rung in model["rungs"]:
        col = _grid_index(rung["world_x_ft"], xmin, xmax, width)
        row = _grid_index(rung["world_y_ft"], config.base_y_ft, config.base_y_ft + config.height_ft, height)
        layer = _grid_index(rung["world_z_ft"], zmin, zmax, depth)
        nodes.append((node_no, row, col, layer))
        node_no += 1

    compressed = ";".join(f"{n},{r},{c},{d}" for n, r, c, d in nodes)
    attrs = {
        "name": "HELIXIA_GIANT_DOUBLE_HELIX",
        "parm1": str(width),
        "parm2": str(height),
        "Depth": str(depth),
        "DisplayAs": "Custom",
        "StringType": "RGB Nodes",
        "PixelSize": "2",
        "Transparency": "0",
        "Antialias": "1",
        "CustomStrings": "2",
        "String1": "1",
        "String2": str(config.nodes_per_strand + 1),
        "CustomModelCompressed": compressed,
        "SourceVersion": "Helixia-export-v1",
        "ModelBrightness": "0",
        "WorldPosX": "0",
        "WorldPosY": "0",
        "WorldPosZ": "0",
    }
    root = ET.Element("custommodel", attrs)
    ET.SubElement(root, "metadata", {
        "model_id": model["model_id"],
        "node_count": str(len(nodes)),
        "strand_a_nodes": str(len(model["strand_a"])),
        "strand_b_nodes": str(len(model["strand_b"])),
        "rung_count": str(len(model["rungs"])),
        "coordinate_system": "x-right,y-up,z-depth",
    })
    return root


def write_xmodel(path: Path) -> None:
    root = build_xmodel()
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the Helixia giant double helix as an xLights 3D custom model.")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write_xmodel(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
