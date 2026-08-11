#!/usr/bin/env python3
"""Build Drummer v3 source-image assets and side-by-side xLights model.

Drummer v3 is asset-first: ``drummerbg.png`` is the visual source of truth. This
builder may decode the repo-safe ``drummerbg.png.b64`` fixture, creates the pose
sheet/layers with the PNG overlay builder, materializes the preview backdrop and
idle layer required by the preview contract, and exports a V3 xmodel whose named
zones are derived from the same authored pose spec.
"""

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
    build_overlay,
)


DEFAULT_SPEC = ROOT / "fixtures" / "band_geometry" / "drummer_v3_pose_spec.json"
MODEL_NAME = "HX_SNOWMAN_DRUMMER_V3"
PREVIEW_BACKDROP = "drummerbg_preview_backdrop.png"
IDLE_LAYER = "drummer_idle_ready.png"


def _repo_path(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def load_spec(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Drummer v3 pose spec must be a JSON object: {path}")
    if data.get("model_name") != MODEL_NAME:
        raise ValueError(f"Unexpected Drummer v3 model name: {data.get('model_name')!r}")
    return data


def ensure_source_png(spec: dict[str, Any], *, overwrite: bool = False) -> tuple[Path, bool]:
    source = _repo_path(str(spec["source_image"]))
    if source.exists() and not overwrite:
        return source, False

    encoded = _repo_path(str(spec.get("source_image_b64", "")))
    if not encoded.exists():
        raise FileNotFoundError(f"Missing Drummer v3 source PNG and b64 fixture: {source}")
    payload = "".join(encoded.read_text(encoding="utf-8").split())
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(base64.b64decode(payload))
    return source, True


def ensure_preview_contract_assets(source: Path, layers_dir: Path, overwrite: bool) -> list[str]:
    """Materialize deterministic preview-only derivatives required by the V3 contract.

    The approved source image remains the visual source of truth. The backdrop is
    an exact copy of that source, while the idle layer is intentionally transparent:
    it represents the absence of a hit without inventing replacement artwork.
    """
    written: list[str] = []
    backdrop = source.parent / PREVIEW_BACKDROP
    if overwrite or not backdrop.exists():
        backdrop.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            image.convert("RGBA").save(backdrop, "PNG")
        written.append(str(backdrop.relative_to(ROOT)))

    idle = layers_dir / IDLE_LAYER
    if overwrite or not idle.exists():
        layers_dir.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            transparent = Image.new("RGBA", image.size, (0, 0, 0, 0))
        transparent.save(idle, "PNG")
        written.append(str(idle.relative_to(ROOT)))
    return written


def _nodes_from_overlay(overlay: Image.Image, width: int, height: int) -> set[int]:
    alpha = overlay.convert("RGBA").getchannel("A")
    nodes: set[int] = set()
    for y in range(height):
        for x in range(width):
            if alpha.getpixel((x, y)) > 0:
                nodes.add(y * width + x + 1)
    return nodes


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


def _prefixed(name: str) -> str:
    return f"{MODEL_NAME}_{name}"


def build_xmodel(spec: dict[str, Any], source_path: Path, xmodel_path: Path) -> dict[str, object]:
    grid = spec.get("grid", {})
    width = int(grid.get("width", 96))
    height = int(grid.get("height", 72))
    zone_nodes: dict[str, set[int]] = {}

    for zone in spec.get("zones", []):
        if not isinstance(zone, dict):
            raise ValueError(f"Invalid V3 zone entry: {zone!r}")
        zone_id = str(zone["id"])
        overlay = build_overlay((width, height), zone)
        nodes = _nodes_from_overlay(overlay, width, height)
        if not nodes:
            raise ValueError(f"V3 zone generated no xmodel nodes: {zone_id}")
        zone_nodes[zone_id] = nodes

    composite_nodes: dict[str, set[int]] = {}
    for composite in spec.get("composites", []):
        if not isinstance(composite, dict):
            raise ValueError(f"Invalid V3 composite entry: {composite!r}")
        composite_id = str(composite["id"])
        nodes: set[int] = set()
        for member in composite.get("members", []):
            member_nodes = zone_nodes.get(str(member))
            if not member_nodes:
                raise ValueError(f"Composite {composite_id} references unknown member: {member}")
            nodes.update(member_nodes)
        composite_nodes[composite_id] = nodes

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
            "HelixImplementationState": "drummer_v3_asset_first_side_by_side",
            "HelixVisualSource": str(source_path.relative_to(ROOT)),
            "CustomBkgImage": str(source_path.resolve()),
        },
    )
    ET.SubElement(root, "modelGroups")
    submodels = ET.SubElement(root, "subModels")
    for zone_id in zone_nodes:
        ET.SubElement(
            submodels,
            "subModel",
            {"name": _prefixed(zone_id), "layout": "ranges", "type": "ranges", "line0": _ranges(zone_nodes[zone_id])},
        )
    for composite_id in composite_nodes:
        ET.SubElement(
            submodels,
            "subModel",
            {
                "name": _prefixed(composite_id),
                "layout": "ranges",
                "type": "ranges",
                "line0": _ranges(composite_nodes[composite_id]),
            },
        )

    xmodel_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(xmodel_path, encoding="UTF-8", xml_declaration=True)
    return {
        "xmodel": str(xmodel_path.relative_to(ROOT)),
        "model_name": MODEL_NAME,
        "grid": {"width": width, "height": height},
        "zone_count": len(zone_nodes),
        "composite_count": len(composite_nodes),
        "submodel_count": len(zone_nodes) + len(composite_nodes),
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
            raise ValueError(f"Drummer v3 source image is too small: {image.size}")
        source_size = image.size

    layers = build_png_layers(source, layer_manifest, layers_dir, preview_dir, overwrite)
    materialized = ensure_preview_contract_assets(source, layers_dir, overwrite)
    xmodel_path = _repo_path(str(spec["xmodel_path"]))
    xmodel = build_xmodel(spec, source, xmodel_path)
    layers["materialized_contract_assets"] = materialized
    return {
        "schema": "helix.drummer_v3_asset_build.v1",
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
        print(f"Drummer v3 asset build failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
