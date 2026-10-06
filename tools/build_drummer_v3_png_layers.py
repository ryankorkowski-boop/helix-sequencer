#!/usr/bin/env python3
"""Build Drummer V3 review layers from the same xmodel nodes used by the renderer."""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "fixtures" / "band_geometry" / "source" / "drummerbg.png"
DEFAULT_MANIFEST = ROOT / "fixtures" / "band_geometry" / "drummer_v3_png_layer_manifest.json"
DEFAULT_XMODEL = ROOT / "fixtures" / "band_geometry" / "models" / "HX_SNOWMAN_DRUMMER_V3.xmodel"
DEFAULT_LAYERS_DIR = ROOT / "fixtures" / "band_geometry" / "layers"
DEFAULT_PREVIEW_DIR = ROOT / "fixtures" / "band_geometry" / "previews"


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Manifest did not parse as an object: {path}")
    return data


def _rgba(command: dict[str, Any]) -> tuple[int, int, int, int]:
    values = command.get("rgba", [255, 255, 255, 255])
    if not isinstance(values, list) or len(values) != 4:
        raise ValueError(f"Invalid rgba value in command: {command!r}")
    return tuple(int(v) for v in values)  # type: ignore[return-value]


def _xy_pairs(command: dict[str, Any], size: tuple[int, int]) -> list[tuple[int, int]]:
    raw = command.get("points")
    if not isinstance(raw, list) or len(raw) < 3:
        raise ValueError(f"Polygon command missing normalized points: {command!r}")
    width, height = size
    points: list[tuple[int, int]] = []
    for pair in raw:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"Invalid polygon point: {pair!r}")
        points.append((round(float(pair[0]) * (width - 1)), round(float(pair[1]) * (height - 1))))
    return points


def draw_command(draw: ImageDraw.ImageDraw, command: dict[str, Any], size: tuple[int, int]) -> None:
    shape = str(command.get("shape", ""))
    if shape == "polygon":
        draw.polygon(_xy_pairs(command, size), fill=_rgba(command))
        return
    raise ValueError(f"Unsupported V3 geometry command shape: {shape}")


def build_overlay(size: tuple[int, int], zone: dict[str, Any]) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    commands = zone.get("commands", [])
    if not isinstance(commands, list) or not commands:
        raise ValueError(f"Zone {zone.get('id')} has no draw commands")
    for command in commands:
        if not isinstance(command, dict):
            raise ValueError(f"Invalid command in {zone.get('id')}: {command!r}")
        draw_command(draw, command, size)
    return overlay


def _expand_ranges(text: str) -> set[int]:
    nodes: set[int] = set()
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            start, end = int(a), int(b)
            if start > end:
                raise ValueError(f"Invalid node range: {token}")
            nodes.update(range(start, end + 1))
        else:
            nodes.add(int(token))
    return nodes


def load_xmodel_masks(xmodel_path: Path, source_size: tuple[int, int]) -> dict[str, Image.Image]:
    root = ET.parse(xmodel_path).getroot()
    width = int(root.get("parm1", "0"))
    height = int(root.get("parm2", "0"))
    if width <= 0 or height <= 0:
        raise ValueError("xmodel has invalid grid dimensions")
    max_node = width * height
    masks: dict[str, Image.Image] = {}
    for submodel in root.findall("./subModels/subModel"):
        name = submodel.get("name", "")
        nodes = _expand_ranges(submodel.get("line0", ""))
        if not nodes:
            raise ValueError(f"xmodel submodel is empty: {name}")
        if min(nodes) < 1 or max(nodes) > max_node:
            raise ValueError(f"xmodel submodel has out-of-range nodes: {name}")
        grid = Image.new("L", (width, height), 0)
        pixels = grid.load()
        for node in nodes:
            idx = node - 1
            pixels[idx % width, idx // width] = 255
        masks[name] = grid.resize(source_size, Image.Resampling.NEAREST)
    return masks


def validate_manifest(manifest: dict[str, Any]) -> None:
    frames = manifest.get("required_frames", [])
    layers = manifest.get("layers", [])
    if not isinstance(frames, list) or len(frames) < 10:
        raise ValueError("Manifest must declare review frames")
    if not isinstance(layers, list) or len(layers) < 8:
        raise ValueError("Manifest must declare event layers")
    layer_ids = {str(layer.get("id")) for layer in layers if isinstance(layer, dict)}
    for frame in frames:
        if frame != "idle_ready" and str(frame) not in layer_ids:
            raise ValueError(f"Review frame has no matching layer id: {frame}")
    for layer in layers:
        if not isinstance(layer, dict) or not layer.get("file") or not layer.get("targets"):
            raise ValueError(f"Invalid review layer: {layer!r}")
        if "commands" in layer:
            raise ValueError(f"Layer {layer.get('id')} must not duplicate authored geometry commands")


def _union_masks(targets: list[str], masks: dict[str, Image.Image], size: tuple[int, int]) -> Image.Image:
    union = Image.new("L", size, 0)
    for target in targets:
        if target not in masks:
            raise ValueError(f"Review layer references missing xmodel target: {target}")
        union = ImageChops.lighter(union, masks[target])
    return union


def _transparent_source(source: Image.Image, mask: Image.Image) -> Image.Image:
    layer = source.convert("RGBA").copy()
    layer.putalpha(mask)
    return layer


def make_contact_sheet(source: Image.Image, overlays: dict[str, Image.Image], frames: list[str]) -> Image.Image:
    base = source.convert("RGBA")
    dim = base.convert("RGB").point(lambda v: int(v * 0.28)).convert("RGBA")
    frame_w, label_h = 360, 28
    scale = frame_w / base.width
    frame_h = max(1, round(base.height * scale))
    cols = 2
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * frame_w, rows * (frame_h + label_h)), (20, 20, 20, 255))
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(frames):
        x = (index % cols) * frame_w
        y = (index // cols) * (frame_h + label_h)
        composed = dim.copy()
        overlay = overlays.get(frame)
        if overlay is not None:
            composed.alpha_composite(overlay)
        sheet.alpha_composite(composed.resize((frame_w, frame_h), Image.Resampling.LANCZOS), (x, y + label_h))
        draw.text((x + 8, y + 7), frame, fill=(255, 255, 255, 255))
    return sheet


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def save_image(path: Path, image: Image.Image, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")
    return True


def build(
    source_path: Path,
    manifest_path: Path,
    layers_dir: Path,
    preview_dir: Path,
    overwrite: bool,
    *,
    xmodel_path: Path = DEFAULT_XMODEL,
) -> dict[str, Any]:
    if not source_path.exists():
        raise FileNotFoundError(f"Required source image is missing: {_relative(source_path)}")
    if source_path.suffix.lower() != ".png":
        raise ValueError(f"Source image must be a PNG: {_relative(source_path)}")
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    source = Image.open(source_path).convert("RGBA")
    if source.width < 128 or source.height < 128:
        raise ValueError(f"Source image is too small for a useful review sheet: {source.size}")
    masks = load_xmodel_masks(xmodel_path, source.size)

    overlays: dict[str, Image.Image] = {}
    written: list[str] = []
    skipped: list[str] = []
    for layer in manifest["layers"]:
        layer_id = str(layer["id"])
        mask = _union_masks([str(t) for t in layer["targets"]], masks, source.size)
        overlay = _transparent_source(source, mask)
        overlays[layer_id] = overlay
        out_path = layers_dir / str(layer["file"])
        (written if save_image(out_path, overlay, overwrite) else skipped).append(_relative(out_path))

    frames = [str(frame) for frame in manifest["required_frames"]]
    contact = make_contact_sheet(source, overlays, frames)
    contact_path = preview_dir / str(manifest.get("contact_sheet", "drummer_v3_contact_sheet.png"))
    (written if save_image(contact_path, contact, overwrite) else skipped).append(_relative(contact_path))
    return {
        "schema": "helix.drummer_v3_png_layer_build.v2",
        "source_image": _relative(source_path),
        "xmodel": _relative(xmodel_path),
        "layer_count": len(overlays),
        "frame_count": len(frames),
        "written": written,
        "skipped": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--xmodel", type=Path, default=DEFAULT_XMODEL)
    parser.add_argument("--layers-dir", type=Path, default=DEFAULT_LAYERS_DIR)
    parser.add_argument("--preview-dir", type=Path, default=DEFAULT_PREVIEW_DIR)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = build(
            args.source, args.manifest, args.layers_dir, args.preview_dir,
            args.overwrite, xmodel_path=args.xmodel
        )
    except Exception as exc:
        print(f"Drummer V3 PNG layer build failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
