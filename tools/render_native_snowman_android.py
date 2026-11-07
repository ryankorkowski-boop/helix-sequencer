"""Produce phone-readable PNGs directly from verified native position CSVs.

Review-only orthographic XY projections, never physical templates or
time-synchronized lighting renders.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def render_pngs(audit_dir: Path, size: int = 1200) -> list[Path]:
    audit_dir = Path(audit_dir)
    manifest = json.loads((audit_dir / "audit.json").read_text(encoding="utf-8"))
    results = []
    for model in manifest["models"]:
        with (audit_dir / model["coordinate_csv"]).open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            raise ValueError(f"Missing native points for {model['name']}")
        xs = [float(p["design_x"]) for p in rows]
        ys = [float(p["design_y"]) for p in rows]
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        span = max(xmax - xmin, ymax - ymin, 1e-12)
        factor = (size - 180) / span
        xoff = (size - (xmax - xmin) * factor) / 2
        yoff = (size - (ymax - ymin) * factor) / 2
        img = Image.new("RGB", (size, size), (8, 14, 25))
        draw = ImageDraw.Draw(img)
        draw.text((25, 20), model["name"], fill=(255, 255, 255))
        draw.text((25, 45), "NATIVE POSITION PROJECTION - NOT NIGHTTIME LIGHTING", fill=(255, 210, 110))
        draw.text((25, 65), "NOT PHYSICAL SCALE / NOT A DRILLING TEMPLATE", fill=(255, 210, 110))
        for x, y in zip(xs, ys):
            px = xoff + (x - xmin) * factor
            py = size - (yoff + (y - ymin) * factor)
            draw.ellipse((px - 1.5, py - 1.5, px + 1.5, py + 1.5), fill=(210, 240, 255))
        out = audit_dir / (model["name"] + "_android.png")
        img.save(out, optimize=True)
        results.append(out)
    return results


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audit-dir", type=Path, required=True)
    a = p.parse_args()
    print(f"Created {len(render_pngs(a.audit_dir))} Android review PNGs")


if __name__ == "__main__":
    main()
