#!/usr/bin/env python3
"""Validate the layered snowman drummer asset stack.

This checks the manifest and, when PNG files are present, verifies that all layers
share the same canvas size and that event overlays contain transparency.

The validator is intentionally non-destructive and can run before the art exists.
Missing images are reported clearly so the manifest can be committed first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - friendly CLI failure
    yaml = None

try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover - friendly CLI failure
    Image = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "assets" / "drummers" / "snowman_locked" / "drummer_layers.yaml"
DEFAULT_ASSET_DIR = ROOT / "assets" / "drummers" / "snowman_locked"


def load_manifest(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to parse drummer_layers.yaml")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Manifest did not parse as a mapping: {path}")
    return data


def image_size_and_alpha(path: Path) -> tuple[tuple[int, int], bool]:
    if Image is None:
        raise RuntimeError("Pillow is required to inspect PNG dimensions/alpha")
    with Image.open(path) as img:
        size = img.size
        has_alpha = img.mode in {"LA", "RGBA"} or "transparency" in img.info
    return size, has_alpha


def validate(manifest_path: Path, asset_dir: Path, strict_missing: bool) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest_path.exists():
        errors.append(f"Manifest missing: {manifest_path}")
        print_report(errors, warnings)
        return 1

    manifest = load_manifest(manifest_path)
    canvas = manifest.get("canvas", {})
    expected_size = (int(canvas.get("width", 0)), int(canvas.get("height", 0)))
    if expected_size[0] <= 0 or expected_size[1] <= 0:
        errors.append("Manifest canvas width/height must be positive integers")

    base = manifest.get("base_layer", {})
    layers = manifest.get("layers", [])
    if not isinstance(layers, list) or not layers:
        errors.append("Manifest must define at least one event layer")

    image_specs: list[tuple[str, Path, bool]] = []
    if isinstance(base, dict) and base.get("file"):
        image_specs.append((str(base.get("id", "base_layer")), asset_dir / str(base["file"]), False))
    else:
        errors.append("Manifest base_layer.file is required")

    for layer in layers if isinstance(layers, list) else []:
        if not isinstance(layer, dict):
            errors.append(f"Invalid layer entry: {layer!r}")
            continue
        layer_id = str(layer.get("id", "<missing id>"))
        filename = layer.get("file")
        if not filename:
            errors.append(f"Layer {layer_id} missing file")
            continue
        image_specs.append((layer_id, asset_dir / str(filename), True))

        target_components = layer.get("target_components", [])
        moving_components = layer.get("moving_components", [])
        if not target_components:
            errors.append(f"Layer {layer_id} needs at least one target component")
        if not moving_components:
            errors.append(f"Layer {layer_id} needs at least one moving/contact component")

    for layer_id, image_path, should_have_alpha in image_specs:
        if not image_path.exists():
            message = f"Missing PNG for {layer_id}: {image_path.relative_to(ROOT)}"
            if strict_missing:
                errors.append(message)
            else:
                warnings.append(message)
            continue

        if image_path.suffix.lower() != ".png":
            errors.append(f"{layer_id} is not a PNG: {image_path}")
            continue

        size, has_alpha = image_size_and_alpha(image_path)
        if expected_size != (0, 0) and size != expected_size:
            errors.append(
                f"{layer_id} canvas mismatch: got {size[0]}x{size[1]}, "
                f"expected {expected_size[0]}x{expected_size[1]}"
            )
        if should_have_alpha and not has_alpha:
            errors.append(f"{layer_id} event overlay must have transparency/alpha")

    print_report(errors, warnings)
    return 1 if errors else 0


def print_report(errors: list[str], warnings: list[str]) -> None:
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    if not errors and not warnings:
        print("Drummer layer manifest and PNG stack look valid.")
    elif not errors:
        print("Drummer layer manifest is valid; add the missing PNG artwork when ready.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--asset-dir", type=Path, default=DEFAULT_ASSET_DIR)
    parser.add_argument(
        "--strict-missing",
        action="store_true",
        help="Treat missing PNG artwork as an error instead of a warning.",
    )
    args = parser.parse_args(argv)
    return validate(args.manifest, args.asset_dir, args.strict_missing)


if __name__ == "__main__":
    sys.exit(main())
