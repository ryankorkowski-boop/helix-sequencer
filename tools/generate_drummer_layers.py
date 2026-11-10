#!/usr/bin/env python3
"""Generate the locked dim drummer base and transparent overlay placeholders.

Usage examples:

    python tools/generate_drummer_layers.py \
        --source path/to/source_drummer.png

    python tools/generate_drummer_layers.py \
        --source path/to/source_drummer.png \
        --overwrite

This script does not pretend to know the exact arm art yet. It creates the
correctly named, correctly sized PNG stack so an artist/Codex pass can paint the
hit target + arm/stick contact components onto each transparent overlay.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "assets" / "drummers" / "snowman_locked" / "drummer_layers.yaml"
DEFAULT_OUT_DIR = ROOT / "assets" / "drummers" / "snowman_locked"


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Manifest did not parse as a mapping: {path}")
    return data


def fit_to_canvas(source: Image.Image, width: int, height: int) -> Image.Image:
    """Fit source inside the target canvas without cropping."""
    src = source.convert("RGBA")
    if src.size == (width, height):
        return src

    fitted = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    src_ratio = src.width / src.height
    dst_ratio = width / height

    if src_ratio >= dst_ratio:
        new_width = width
        new_height = max(1, round(width / src_ratio))
    else:
        new_height = height
        new_width = max(1, round(height * src_ratio))

    resized = src.resize((new_width, new_height), Image.Resampling.LANCZOS)
    x = (width - new_width) // 2
    y = (height - new_height) // 2
    fitted.alpha_composite(resized, (x, y))
    return fitted


def make_dim_base(source: Image.Image, intensity: float) -> Image.Image:
    """Dim an RGBA source while preserving transparency."""
    rgba = source.convert("RGBA")
    rgb = rgba.convert("RGB")
    dimmed_rgb = ImageEnhance.Brightness(rgb).enhance(max(0.0, intensity))
    dimmed = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    dimmed.paste(dimmed_rgb, (0, 0), rgba.getchannel("A"))
    return dimmed


def make_overlay_placeholder(width: int, height: int) -> Image.Image:
    return Image.new("RGBA", (width, height), (0, 0, 0, 0))


def save_png(path: Path, image: Image.Image, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")
    return True


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def generate(source_path: Path, manifest_path: Path, out_dir: Path, overwrite: bool) -> int:
    manifest = load_manifest(manifest_path)
    canvas = manifest.get("canvas", {})
    width = int(canvas.get("width", 2048))
    height = int(canvas.get("height", 2048))

    source = Image.open(source_path)
    source_canvas = fit_to_canvas(source, width, height)

    base_layer = manifest.get("base_layer", {})
    base_file = base_layer.get("file")
    if not base_file:
        raise ValueError("Manifest base_layer.file is required")
    base_intensity = float(base_layer.get("intensity", 0.32))
    base = make_dim_base(source_canvas, base_intensity)

    written: list[str] = []
    skipped: list[str] = []

    base_path = out_dir / str(base_file)
    if save_png(base_path, base, overwrite):
        written.append(display_path(base_path))
    else:
        skipped.append(display_path(base_path))

    for layer in manifest.get("layers", []):
        if not isinstance(layer, dict) or not layer.get("file"):
            continue
        overlay_path = out_dir / str(layer["file"])
        overlay = make_overlay_placeholder(width, height)
        if save_png(overlay_path, overlay, overwrite):
            written.append(display_path(overlay_path))
        else:
            skipped.append(display_path(overlay_path))

    print("Generated drummer layer files.")
    if written:
        print("Written:")
        for item in written:
            print(f"  - {item}")
    if skipped:
        print("Skipped existing files; pass --overwrite to replace:")
        for item in skipped:
            print(f"  - {item}")
    print("Next art pass: paint each transparent event PNG with target + contacting arm/stick only.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Source drummer PNG/JPG to dim into the locked base layer.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing generated PNGs.")
    args = parser.parse_args(argv)

    if not args.source.exists():
        print(f"Source image not found: {args.source}", file=sys.stderr)
        return 1
    return generate(args.source, args.manifest, args.out_dir, args.overwrite)


if __name__ == "__main__":
    sys.exit(main())
