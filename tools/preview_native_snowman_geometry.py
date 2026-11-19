"""Render exact native model point projections from audit CSVs.

These are coordinate-space inspection views, NOT manufacturing drawings.
No scaling, pixel pitch, physical outline, or drilled holes are inferred.
Usage: python -m tools.preview_native_snowman_geometry --audit-dir build/native_snowman_audit
"""
from __future__ import annotations
import argparse
import csv
import html
import json
from pathlib import Path


def render(audit_dir: Path) -> list[Path]:
    audit_dir = Path(audit_dir)
    manifest = json.loads((audit_dir / "audit.json").read_text(encoding="utf-8"))
    produced = []
    for model in manifest["models"]:
        with (audit_dir / model["coordinate_csv"]).open(newline="", encoding="utf-8") as f:
            points = list(csv.DictReader(f))
        if not points:
            raise ValueError(f"No native geometry: {model['name']}")
        # Native XYZ: x horizontal, y vertical, z depth.
        # The front view is an orthographic XY projection; no false silhouette.
        x = [float(p["design_x"]) for p in points]
        y = [float(p["design_y"]) for p in points]
        xmin, xmax, ymin, ymax = min(x), max(x), min(y), max(y)
        width, height = 900, 900
        span = max(xmax - xmin, ymax - ymin, 1e-12)
        scale = 780 / span
        ox = (width - (xmax - xmin) * scale) / 2
        oy = (height - (ymax - ymin) * scale) / 2
        dots = []
        for p, px, py in zip(points, x, y):
            sx = ox + (px - xmin) * scale
            sy = height - (oy + (py - ymin) * scale)
            owner = html.escape(p["submodels"])
            node = html.escape(p["node_or_circuit"])
            dots.append(f'<circle cx="{sx:.4f}" cy="{sy:.4f}" r="1.25" fill="#d9f4ff"><title>id={node}; submodels={owner}; depth={html.escape(p["design_z"])}</title></circle>')
        name = html.escape(model["name"])
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 900">'
               '<rect width="900" height="900" fill="#14202b"/>'
               f'<text x="20" y="32" fill="white" font-size="18">{name}</text>'
               '<text x="20" y="55" fill="#ffdb8b" font-size="13">NATIVE XY PROJECTION - NOT PHYSICAL SCALE / NOT DRILL TEMPLATE</text>'
               + "".join(dots) + '</svg>')
        target = audit_dir / f"{model['name']}_front_projection.svg"
        target.write_text(svg, encoding="utf-8")
        produced.append(target)
    return produced


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, required=True)
    args = parser.parse_args()
    print(f"Rendered {len(render(args.audit_dir))} native geometry projections")


if __name__ == "__main__":
    main()
