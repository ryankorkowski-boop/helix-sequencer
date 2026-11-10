#!/usr/bin/env python3
"""Build Drummer v3 transparent event layers from drummerbg.png.

The approved background PNG is the visual input. This script does not create a
replacement drummer. It only draws authored transparent overlays and a contact
sheet for review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "fixtures" / "band_geometry" / "source" / "drummerbg.png"
DEFAULT_MANIFEST = ROOT / "fixtures" / "band_geometry" / "drummer_v3_png_layer_manifest.json"
DEFAULT_LAYERS_DIR = ROOT / "fixtures" / "band_geometry" / "layers"
DEFAULT_PREVIEW_DIR = ROOT / "fixtures" / "band_geometry" / "previews"


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Manifest did not parse as an object: {path}")
    return data


def _rgba(command: dict[str, Any]) -> tuple[int, int, int, int]:
    values = command.get("rgba", [255, 255, 255, 220])
    if not isinstance(values, list) or len(values) != 4:
        raise ValueError(f"Invalid rgba value in command: {command!r}")
    return tuple(int(v) for v in values)  # type: ignore[return-value]


def _box(command: dict[str, Any], size: tuple[int, int]) -> tuple[int, int, int, int]:
    raw = command.get("box")
    if not isinstance(raw, list) or len(raw) != 4:
        raise ValueError(f"Command missing normalized box: {command!r}")
    width, height = size
    x0, y0, x1, y1 = [float(v) for v in raw]
    return (round(x0 * width), round(y0 * height), round(x1 * width), round(y1 * height))


def _points(command: dict[str, Any], size: tuple[int, int]) -> tuple[int, int, int, int]:
    raw = command.get("points")
    if not isinstance(raw, list) or len(raw) != 4:
        raise ValueError(f"Command missing normalized points: {command!r}")
    width, height = size
    x0, y0, x1, y1 = [float(v) for v in raw]
    return (round(x0 * width), round(y0 * height), round(x1 * width), round(y1 * height))


def _expand_box(box: tuple[int, int, int, int], amount: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (x0 - amount, y0 - amount, x1 + amount, y1 + amount)


def _scaled_width(command: dict[str, Any], size: tuple[int, int], default: float = 0.01) -> int:
    return max(1, round(float(command.get("width", default)) * min(size)))


def draw_command(draw: ImageDraw.ImageDraw, command: dict[str, Any], size: tuple[int, int]) -> None:
    shape = str(command.get("shape", ""))
    color = _rgba(command)
    glow_px = round(float(command.get("glow", 0.0)) * min(size))

    if shape == "ellipse":
        box = _box(command, size)
        if glow_px:
            for step in range(3, 0, -1):
                alpha = max(12, color[3] // (step + 2))
                draw.ellipse(_expand_box(box, round(glow_px * step / 3)), fill=(*color[:3], alpha))
        draw.ellipse(box, fill=color)
        return

    if shape == "ellipse_outline":
        box = _box(command, size)
        width = _scaled_width(command, size)
        if glow_px:
            for step in range(3, 0, -1):
                alpha = max(12, color[3] // (step + 2))
                draw.ellipse(_expand_box(box, round(glow_px * step / 3)), outline=(*color[:3], alpha), width=width + step * 2)
        draw.ellipse(box, outline=color, width=width)
        return

    if shape == "rectangle_outline":
        box = _box(command, size)
        width = _scaled_width(command, size)
        if glow_px:
            for step in range(3, 0, -1):
                alpha = max(12, color[3] // (step + 2))
                draw.rectangle(_expand_box(box, round(glow_px * step / 3)), outline=(*color[:3], alpha), width=width + step * 2)
        draw.rectangle(box, outline=color, width=width)
        return

    if shape == "line":
        x0, y0, x1, y1 = _points(command, size)
        width = _scaled_width(command, size)
        if glow_px:
            for step in range(3, 0, -1):
                alpha = max(12, color[3] // (step + 2))
                draw.line((x0, y0, x1, y1), fill=(*color[:3], alpha), width=width + step * max(1, glow_px // 3))
        draw.line((x0, y0, x1, y1), fill=color, width=width)
        return

    if shape == "burst":
        raw_center = command.get("center")
        if not isinstance(raw_center, list) or len(raw_center) != 2:
            raise ValueError(f"Burst command missing center: {command!r}")
        width, height = size
        cx = round(float(raw_center[0]) * width)
        cy = round(float(raw_center[1]) * height)
        radius = round(float(command.get("radius", 0.05)) * min(size))
        spokes = int(command.get("spokes", 10))
        import math

        for index in range(spokes):
            angle = math.tau * index / max(1, spokes)
            x1 = round(cx + math.cos(angle) * radius)
            y1 = round(cy + math.sin(angle) * radius)
            draw.line((cx, cy, x1, y1), fill=color, width=max(1, radius // 18))
        return

    raise ValueError(f"Unsupported layer command shape: {shape}")


def build_overlay(size: tuple[int, int], layer: dict[str, Any]) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    commands = layer.get("commands", [])
    if not isinstance(commands, list) or not commands:
        raise ValueError(f"Layer {layer.get('id')} has no draw commands")
    for command in commands:
        if not isinstance(command, dict):
            raise ValueError(f"Invalid command in {layer.get('id')}: {command!r}")
        draw_command(draw, command, size)
    return overlay


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


def make_contact_sheet(source: Image.Image, overlays: dict[str, Image.Image], frames: list[str]) -> Image.Image:
    base = source.convert("RGBA")
    frame_w = 360
    label_h = 28
    scale = frame_w / base.width
    frame_h = max(1, round(base.height * scale))
    cols = 2
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * frame_w, rows * (frame_h + label_h)), (20, 20, 20, 255))
    draw = ImageDraw.Draw(sheet)

    for index, frame in enumerate(frames):
        x = (index % cols) * frame_w
        y = (index // cols) * (frame_h + label_h)
        composed = base.copy()
        overlay = overlays.get(frame)
        if overlay is not None:
            composed.alpha_composite(overlay)
        thumb = composed.resize((frame_w, frame_h), Image.Resampling.LANCZOS)
        sheet.alpha_composite(thumb, (x, y + label_h))
        draw.text((x + 8, y + 7), frame, fill=(255, 255, 255, 255))
    return sheet


def validate_manifest(manifest: dict[str, Any]) -> None:
    frames = manifest.get("required_frames", [])
    layers = manifest.get("layers", [])
    if not isinstance(frames, list) or len(frames) < 10:
        raise ValueError("Manifest must declare at least 10 review frames")
    if not isinstance(layers, list) or len(layers) < 8:
        raise ValueError("Manifest must declare event layers")
    layer_ids = {str(layer.get("id")) for layer in layers if isinstance(layer, dict)}
    for frame in frames:
        if frame == "idle_ready":
            continue
        if str(frame) not in layer_ids:
            raise ValueError(f"Review frame has no matching layer id: {frame}")
    for layer in layers:
        if not isinstance(layer, dict):
            raise ValueError(f"Invalid layer entry: {layer!r}")
        if not layer.get("file"):
            raise ValueError(f"Layer {layer.get('id')} is missing file")
        if not layer.get("target_components"):
            raise ValueError(f"Layer {layer.get('id')} is missing target_components")
        if not layer.get("contact_components"):
            raise ValueError(f"Layer {layer.get('id')} is missing contact_components")


def build(source_path: Path, manifest_path: Path, layers_dir: Path, preview_dir: Path, overwrite: bool) -> dict[str, Any]:
    if not source_path.exists():
        raise FileNotFoundError(f"Required source image is missing: {_relative(source_path)}")
    if source_path.suffix.lower() != ".png":
        raise ValueError(f"Source image must be a PNG: {_relative(source_path)}")

    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)

    source = Image.open(source_path).convert("RGBA")
    if source.width < 128 or source.height < 128:
        raise ValueError(f"Source image is too small for a useful review sheet: {source.size}")

    overlays: dict[str, Image.Image] = {}
    written: list[str] = []
    skipped: list[str] = []

    for layer in manifest["layers"]:
        layer_id = str(layer["id"])
        overlay = build_overlay(source.size, layer)
        overlays[layer_id] = overlay
        out_path = layers_dir / str(layer["file"])
        if save_image(out_path, overlay, overwrite):
            written.append(_relative(out_path))
        else:
            skipped.append(_relative(out_path))

    frames = [str(frame) for frame in manifest["required_frames"]]
    contact_sheet = make_contact_sheet(source, overlays, frames)
    contact_path = preview_dir / str(manifest.get("contact_sheet", "drummer_v3_contact_sheet.png"))
    if save_image(contact_path, contact_sheet, overwrite):
        written.append(_relative(contact_path))
    else:
        skipped.append(_relative(contact_path))

    return {
        "schema": "helix.drummer_v3_png_layer_build.v1",
        "source_image": _relative(source_path),
        "layer_count": len(overlays),
        "frame_count": len(frames),
        "written": written,
        "skipped": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--layers-dir", type=Path, default=DEFAULT_LAYERS_DIR)
    parser.add_argument("--preview-dir", type=Path, default=DEFAULT_PREVIEW_DIR)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = build(args.source, args.manifest, args.layers_dir, args.preview_dir, args.overwrite)
    except Exception as exc:
        print(f"Drummer v3 PNG layer build failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
