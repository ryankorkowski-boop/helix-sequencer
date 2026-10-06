#!/usr/bin/env python3
"""Build high-fidelity Drummer V3 review layers from the canonical pose spec."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.drummer_v3_visual_masks import (
    build_geometry_masks,
    compose_emissive,
    load_spec,
    refine_actuator_to_source_art,
    refine_surface_to_source_art,
)

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
            raise ValueError(f"Review layer references missing canonical target: {target}")
        union = ImageChops.lighter(union, masks[target])
    return union


def _transparent_emissive(source: Image.Image, mask: Image.Image) -> Image.Image:
    composed = compose_emissive(source, {"_ACTIVE": mask}, ["_ACTIVE"])
    layer = composed.convert("RGBA")
    layer.putalpha(mask)
    return layer


def make_contact_sheet(source: Image.Image, masks_by_frame: dict[str, Image.Image], frames: list[str]) -> Image.Image:
    base = source.convert("RGBA")
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
        mask = masks_by_frame.get(frame)
        if mask is None:
            composed = compose_emissive(base, {}, [])
        else:
            composed = compose_emissive(base, {"_ACTIVE": mask}, ["_ACTIVE"])
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
    if not xmodel_path.exists():
        raise FileNotFoundError(f"Required xmodel is missing: {_relative(xmodel_path)}")
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    source = Image.open(source_path).convert("RGBA")
    if source.width < 128 or source.height < 128:
        raise ValueError(f"Source image is too small for a useful review sheet: {source.size}")
    spec = load_spec()
    geometry = build_geometry_masks(source.size, spec)
    authored_targets = geometry["targets"]
    target_specs = {
        f"{spec['model_name']}_{str(item['id'])}": item
        for item in spec.get("lighting_targets", [])
        if isinstance(item, dict) and item.get("id") and item.get("surface")
    }
    masks: dict[str, Image.Image] = {}
    for target, target_spec in target_specs.items():
        surface_id = str(target_spec["surface"])
        authored_surface = geometry["surfaces"][surface_id]
        exact_surface = refine_surface_to_source_art(source, authored_surface, target)
        authored_actuator = ImageChops.subtract(authored_targets[target], authored_surface)
        if authored_actuator.getbbox() is None:
            exact_actuator = Image.new("L", source.size, 0)
        else:
            exact_actuator = refine_actuator_to_source_art(source, authored_actuator)
        masks[target] = ImageChops.lighter(exact_surface, exact_actuator)

    overlays: dict[str, Image.Image] = {}
    frame_masks: dict[str, Image.Image] = {}
    written: list[str] = []
    skipped: list[str] = []
    for layer in manifest["layers"]:
        layer_id = str(layer["id"])
        mask = _union_masks([str(t) for t in layer["targets"]], masks, source.size)
        frame_masks[layer_id] = mask
        overlay = _transparent_emissive(source, mask)
        overlays[layer_id] = overlay
        out_path = layers_dir / str(layer["file"])
        (written if save_image(out_path, overlay, overwrite) else skipped).append(_relative(out_path))

    frames = [str(frame) for frame in manifest["required_frames"]]
    contact = make_contact_sheet(source, frame_masks, frames)
    contact_path = preview_dir / str(manifest.get("contact_sheet", "drummer_v3_contact_sheet.png"))
    (written if save_image(contact_path, contact, overwrite) else skipped).append(_relative(contact_path))
    return {
        "schema": "helix.drummer_v3_png_layer_build.v3",
        "source_image": _relative(source_path),
        "xmodel": _relative(xmodel_path),
        "geometry_source": "exact drummerbg source pixels inside canonical pose-spec zones",
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
        result = build(args.source, args.manifest, args.layers_dir, args.preview_dir, args.overwrite, xmodel_path=args.xmodel)
    except Exception as exc:
        print(f"Drummer V3 PNG layer build failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
