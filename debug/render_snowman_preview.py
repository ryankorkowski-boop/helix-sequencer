from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from export.snowman_band_json_export import export_band_pack
from models.grid_canvas import DrawableModelTemplate
from models.snowman_geometry import build_band_templates
from models.submodel_generation import validate_model


REGION_COLORS = {
    "body": (235, 245, 255, 255),
    "face_container": (80, 160, 255, 100),
    "limb": (125, 80, 38, 255),
    "instrument": (196, 116, 42, 255),
    "instrument_target": (255, 210, 60, 255),
    "drum": (120, 180, 255, 255),
    "drumstick": (230, 190, 120, 255),
    "costume": (225, 40, 60, 255),
    "mouth": (10, 10, 14, 255),
}


def ascii_preview(model: DrawableModelTemplate, mouth_shape: str = "mouth_A") -> str:
    grid = [["." for _ in range(model.canvas.width)] for _ in range(model.canvas.height)]
    for region in model.base_regions.values():
        char = "o" if region.category in {"body", "face_container"} else "+"
        for x, y in region.coordinates:
            grid[y][x] = char
    mouth = model.mouth_regions.get(mouth_shape)
    if mouth:
        for x, y in mouth.coordinates:
            grid[y][x] = "#"
    return "\n".join("".join(row) for row in grid)


def render_png(model: DrawableModelTemplate, path: Path, mouth_shape: str = "mouth_A", scale: int = 10) -> None:
    img = Image.new("RGBA", (model.canvas.width * scale, model.canvas.height * scale), (8, 12, 20, 255))
    draw = ImageDraw.Draw(img)
    for region in model.base_regions.values():
        color = REGION_COLORS.get(region.category, (180, 180, 180, 255))
        for x, y in region.coordinates:
            draw.rectangle((x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1), fill=color)
    mouth = model.mouth_regions.get(mouth_shape)
    if mouth:
        for x, y in mouth.coordinates:
            draw.rectangle((x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1), fill=REGION_COLORS["mouth"])
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export and preview generated Snowman Band custom-model geometry.")
    parser.add_argument("--out", default="outputs/snowman_band_models", help="Output directory")
    parser.add_argument("--canvas", type=int, default=64, choices=(32, 48, 64))
    parser.add_argument("--png", action="store_true", help="Render PNG previews")
    args = parser.parse_args()
    out = Path(args.out)
    result = export_band_pack(out, args.canvas)
    print(f"Exported Snowman Band pack: {result['combined_path']}")
    for role, model in build_band_templates(args.canvas).items():
        issues = validate_model(model)
        print(f"{role}: regions={len(model.all_regions())} submodels={len(model.submodels)} issues={len(issues)}")
        if args.png:
            render_png(model, out / f"{model.id}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
