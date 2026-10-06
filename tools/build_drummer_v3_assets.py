#!/usr/bin/env python3
"""Build the canonical Drummer V3 xmodel and review layers from one geometry source."""
from __future__ import annotations

import argparse
import base64
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_drummer_v3_png_layers import (
    DEFAULT_LAYERS_DIR,
    DEFAULT_MANIFEST,
    DEFAULT_PREVIEW_DIR,
    build as build_png_layers,
)
from tools.drummer_v3_visual_masks import build_geometry_masks

DEFAULT_SPEC = ROOT / "fixtures" / "band_geometry" / "drummer_v3_pose_spec.json"
MODEL_NAME = "HX_SNOWMAN_DRUMMER_V3"


def _repo_path(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def load_spec(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Drummer V3 pose spec must be an object: {path}")
    if data.get("model_name") != MODEL_NAME:
        raise ValueError(f"Unexpected Drummer V3 model name: {data.get('model_name')!r}")
    return data


def ensure_source_png(spec: dict[str, Any], *, overwrite: bool = False) -> tuple[Path, bool]:
    source = _repo_path(str(spec["source_image"]))
    if source.exists() and not overwrite:
        return source, False
    encoded = _repo_path(str(spec.get("source_image_b64", "")))
    if not encoded.exists():
        raise FileNotFoundError(f"Missing Drummer V3 source PNG and b64 fixture: {source}")
    payload = "".join(encoded.read_text(encoding="utf-8").split())
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(base64.b64decode(payload))
    return source, True


def _nodes_from_overlay(overlay: Image.Image, width: int, height: int) -> set[int]:
    alpha = overlay.convert("RGBA").getchannel("A")
    return {
        y * width + x + 1
        for y in range(height)
        for x in range(width)
        if alpha.getpixel((x, y)) > 0
    }


def _ranges(nodes: set[int]) -> str:
    if not nodes:
        raise ValueError("Cannot write an empty submodel range")
    ordered = sorted(nodes)
    chunks: list[str] = []
    start = previous = ordered[0]
    for node in ordered[1:]:
        if node == previous + 1:
            previous = node
            continue
        chunks.append(f"{start}-{previous}" if start != previous else str(start))
        start = previous = node
    chunks.append(f"{start}-{previous}" if start != previous else str(start))
    return ",".join(chunks)


def _dense_custom_model(width: int, height: int) -> str:
    return ";".join(
        ",".join(str(y * width + x + 1) for x in range(width))
        for y in range(height)
    )


def _prefixed(name: str) -> str:
    return f"{MODEL_NAME}_{name}"


def build_xmodel(spec: dict[str, Any], source_path: Path, xmodel_path: Path) -> dict[str, object]:
    grid = spec.get("grid", {})
    width = int(grid.get("width", 96))
    height = int(grid.get("height", 72))
    geometry = build_geometry_masks((width, height), spec)
    raw_masks = geometry["raw"]
    surface_masks = geometry["surfaces"]
    actuator_masks = geometry["actuators"]
    public_masks = geometry["targets"]

    zone_nodes = {
        name: _nodes_from_overlay(mask.convert("RGBA"), width, height)
        for name, mask in raw_masks.items()
    }
    surface_nodes = {
        name: _nodes_from_overlay(mask.convert("RGBA"), width, height)
        for name, mask in surface_masks.items()
    }
    actuator_nodes = {
        name: _nodes_from_overlay(mask.convert("RGBA"), width, height)
        for name, mask in actuator_masks.items()
    }
    target_nodes = {
        name.removeprefix(f"{MODEL_NAME}_"): _nodes_from_overlay(mask.convert("RGBA"), width, height)
        for name, mask in public_masks.items()
    }

    relative_background = "../source/drummerbg.png"
    root = ET.Element(
        "custommodel",
        {
            "name": MODEL_NAME,
            "parm1": str(width),
            "parm2": str(height),
            "Depth": "1",
            "StringType": "RGB Nodes",
            "Transparency": "0",
            "PixelSize": "2",
            "ModelBrightness": "0",
            "Antialias": "1",
            "CustomModel": _dense_custom_model(width, height),
            "CustomBkgImage": relative_background,
            "HelixVisualSource": relative_background,
            "HelixImplementationState": "drummer_v3_independent_component_lighting",
        },
    )
    ET.SubElement(root, "modelGroups")
    submodels = ET.SubElement(root, "subModels")

    # Surface-only aliases are the geometry truth used by spatial tests.
    for name, nodes in surface_nodes.items():
        ET.SubElement(
            submodels, "subModel",
            {"name": _prefixed(name), "layout": "ranges", "type": "ranges", "line0": _ranges(nodes)},
        )

    # Actuator geometry is exported for review/debug but is never sequenced
    # independently by the eight-lane public contract.
    for name, nodes in actuator_nodes.items():
        ET.SubElement(
            submodels, "subModel",
            {"name": _prefixed(name), "layout": "ranges", "type": "ranges", "line0": _ranges(nodes)},
        )

    # Public hit targets contain the physical surface plus its required
    # arm/stick or foot pixels.
    for target_id, nodes in target_nodes.items():
        ET.SubElement(
            submodels, "subModel",
            {"name": _prefixed(target_id), "layout": "ranges", "type": "ranges", "line0": _ranges(nodes)},
        )

    xmodel_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(xmodel_path, encoding="UTF-8", xml_declaration=True)
    return {
        "xmodel": str(xmodel_path.relative_to(ROOT)),
        "model_name": MODEL_NAME,
        "grid": {"width": width, "height": height},
        "surface_count": len(surface_nodes),
        "actuator_count": len(actuator_nodes),
        "target_count": len(target_nodes),
        "submodel_count": len(list(submodels)),
    }


def build_assets(
    *,
    spec_path: Path = DEFAULT_SPEC,
    layer_manifest: Path = DEFAULT_MANIFEST,
    layers_dir: Path = DEFAULT_LAYERS_DIR,
    preview_dir: Path = DEFAULT_PREVIEW_DIR,
    overwrite: bool = False,
) -> dict[str, Any]:
    spec = load_spec(spec_path)
    source, decoded_source = ensure_source_png(spec, overwrite=overwrite)
    with Image.open(source) as image:
        if image.width < 128 or image.height < 128:
            raise ValueError(f"Drummer V3 source image is too small: {image.size}")
        source_size = image.size

    xmodel_path = _repo_path(str(spec["xmodel_path"]))
    xmodel = build_xmodel(spec, source, xmodel_path)
    layers = build_png_layers(
        source, layer_manifest, layers_dir, preview_dir, overwrite, xmodel_path=xmodel_path
    )
    return {
        "schema": "helix.drummer_v3_asset_build.v2",
        "spec": str(spec_path.relative_to(ROOT)),
        "source_image": str(source.relative_to(ROOT)),
        "source_decoded": decoded_source,
        "source_size": {"width": source_size[0], "height": source_size[1]},
        "pose_sheet": str(_repo_path(str(spec["pose_sheet"])).relative_to(ROOT)),
        "layers": layers,
        "xmodel": xmodel,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--layer-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--layers-dir", type=Path, default=DEFAULT_LAYERS_DIR)
    parser.add_argument("--preview-dir", type=Path, default=DEFAULT_PREVIEW_DIR)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = build_assets(
            spec_path=args.spec,
            layer_manifest=args.layer_manifest,
            layers_dir=args.layers_dir,
            preview_dir=args.preview_dir,
            overwrite=args.overwrite,
        )
    except Exception as exc:
        print(f"Drummer V3 asset build failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
