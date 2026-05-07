from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tools.build_helpers.helixia_3d import build_helixia_3d_layout


DEFAULT_OUTPUT_DIR = Path("outputs/helixia_3d_preview")
DEFAULT_PREVIEW_NAME = "helixia_3d_grounded_preview.svg"


def _svg_escape(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _bounds(models: list[Mapping[str, Any]]) -> dict[str, float]:
    if not models:
        return {"min_x": -1.0, "max_x": 1.0, "min_y": -1.0, "max_y": 1.0, "max_z": 1.0}
    return {
        "min_x": min(float(model.get("anchor_x_ft", 0.0)) for model in models),
        "max_x": max(float(model.get("anchor_x_ft", 0.0)) for model in models),
        "min_y": min(float(model.get("anchor_y_ft", 0.0)) for model in models),
        "max_y": max(float(model.get("anchor_y_ft", 0.0)) for model in models),
        "max_z": max(float(model.get("max_z_ft", 0.0)) for model in models),
    }


def _project(model: Mapping[str, Any], bounds: Mapping[str, float], *, width: int = 980, height: int = 680) -> tuple[float, float]:
    x = float(model.get("anchor_x_ft", 0.0))
    y = float(model.get("anchor_y_ft", 0.0))
    min_x = float(bounds["min_x"])
    max_x = float(bounds["max_x"])
    min_y = float(bounds["min_y"])
    max_y = float(bounds["max_y"])
    norm_x = (x - min_x) / max(1e-9, max_x - min_x)
    norm_y = (y - min_y) / max(1e-9, max_y - min_y)
    px = 80 + norm_x * (width - 160)
    py = height - 90 - norm_y * (height - 170)
    return round(px, 3), round(py, 3)


def _model_color(model: Mapping[str, Any]) -> str:
    lot_id = str(model.get("lot_id", ""))
    model_type = str(model.get("model_type", ""))
    if model.get("model_id") == "HELIXIA_GIANT_DOUBLE_HELIX":
        return "#ff79d7"
    if lot_id.startswith("house_"):
        return "#8fd3ff"
    if bool(model.get("stage_zone")):
        return "#f7ff72"
    if model_type == "tree":
        return "#8cff8c"
    return "#d8e6f3"


def _model_shape(model: Mapping[str, Any], bounds: Mapping[str, float]) -> str:
    x, y = _project(model, bounds)
    color = _model_color(model)
    model_id = _svg_escape(model.get("model_id", ""))
    lot_id = _svg_escape(model.get("lot_id", ""))
    max_z = float(model.get("max_z_ft", 0.0))
    height_px = max(8.0, min(120.0, max_z * 0.9))
    width_ft = float(model.get("width_ft", 10.0) or 10.0)
    depth_ft = float(model.get("depth_ft", 10.0) or 10.0)
    radius = max(4.0, min(16.0, (width_ft + depth_ft) / 8.0))
    if model.get("model_id") == "HELIXIA_GIANT_DOUBLE_HELIX":
        return f'''
    <g class="model double-helix" data-model="{model_id}">
      <line x1="{x}" y1="{y}" x2="{x}" y2="{round(y - height_px, 3)}" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.88"/>
      <circle cx="{x}" cy="{y}" r="18" fill="none" stroke="#6efcff" stroke-width="3"/>
      <circle cx="{x}" cy="{round(y - height_px, 3)}" r="10" fill="#6efcff" opacity="0.85"/>
      <text x="{x}" y="{round(y + 32, 3)}" text-anchor="middle" fill="#ffffff" font-size="10" font-weight="700">DOUBLE HELIX GROUNDED</text>
    </g>'''
    return f'''
    <g class="model" data-model="{model_id}">
      <rect x="{round(x - radius, 3)}" y="{round(y - radius, 3)}" width="{round(radius * 2, 3)}" height="{round(radius * 2, 3)}" rx="4" fill="{color}" stroke="#07101d" stroke-width="1.5" opacity="0.9"/>
      <line x1="{x}" y1="{y}" x2="{x}" y2="{round(y - height_px, 3)}" stroke="{color}" stroke-width="2" opacity="0.55"/>
      <title>{model_id} · {lot_id} · z 0→{round(max_z, 2)} ft</title>
    </g>'''


def build_helixia_3d_preview_svg(layout_3d: Mapping[str, Any]) -> str:
    models = list(layout_3d.get("models", []) or [])
    bounds = _bounds(models)
    model_shapes = "\n".join(_model_shape(model, bounds) for model in models)
    validation = dict(layout_3d.get("validation", {}) or {})
    status = "PASS" if all(bool(value) for value in validation.values()) else "CHECK"
    stage_count = len(layout_3d.get("stage_zones", {}).get("model_ids", []) or [])
    model_count = len(models)
    floating = len(layout_3d.get("grounding", {}).get("floating_grounded_models", []) or [])
    negative = len(layout_3d.get("grounding", {}).get("negative_grounded_models", []) or [])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="980" height="760" viewBox="0 0 980 760">
  <rect width="980" height="760" fill="#07101d"/>
  <text x="490" y="38" text-anchor="middle" fill="#ffffff" font-size="24" font-weight="700">Helixia 3D Grounded Layout Preview</text>
  <text x="490" y="64" text-anchor="middle" fill="#b8d7ff" font-size="12">3D is source of truth · 2D is derived projection · ground plane z=0</text>

  <rect x="50" y="94" width="880" height="560" rx="22" fill="#111f2e" stroke="#d8e6f3" stroke-width="2"/>
  <line x1="70" y1="605" x2="910" y2="605" stroke="#ffffff" stroke-width="3" opacity="0.55"/>
  <text x="82" y="596" fill="#ffffff" font-size="12" font-weight="700">GROUND PLANE Z=0</text>

  <g id="models">
{model_shapes}
  </g>

  <rect x="70" y="668" width="840" height="58" rx="14" fill="#101e31" stroke="#6efcff" opacity="0.95"/>
  <text x="92" y="692" fill="#6efcff" font-size="13" font-weight="700">Validation: {_svg_escape(status)}</text>
  <text x="92" y="714" fill="#d8e6f3" font-size="11">models: {model_count} · stage models: {stage_count} · floating grounded models: {floating} · below-ground models: {negative}</text>
  <text x="650" y="692" fill="#8fd3ff" font-size="11">houses</text>
  <text x="710" y="692" fill="#f7ff72" font-size="11">stage</text>
  <text x="765" y="692" fill="#8cff8c" font-size="11">trees</text>
  <text x="815" y="692" fill="#ff79d7" font-size="11">double helix</text>
</svg>
'''


def write_helixia_3d_preview(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    layout_3d = build_helixia_3d_layout(output_dir)
    preview_svg = build_helixia_3d_preview_svg(layout_3d)
    preview_path = output_dir / DEFAULT_PREVIEW_NAME
    preview_path.write_text(preview_svg, encoding="utf-8")
    summary_path = output_dir / "helixia_3d_preview_summary.json"
    summary = {
        "schema": "helixia.layout3d_preview.summary.v1",
        "layout_manifest": str(output_dir / "helixia_3d_manifest.json"),
        "preview_svg": str(preview_path),
        "model_count": len(layout_3d.get("models", []) or []),
        "stage_model_count": len(layout_3d.get("stage_zones", {}).get("model_ids", []) or []),
        "validation": layout_3d.get("validation", {}),
        "grounding": layout_3d.get("grounding", {}),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "output_dir": str(output_dir),
        "layout_manifest": str(output_dir / "helixia_3d_manifest.json"),
        "preview_svg": str(preview_path),
        "summary": str(summary_path),
        "validation": layout_3d.get("validation", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a grounded 3D Helixia layout manifest and SVG preview.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    print(json.dumps(write_helixia_3d_preview(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
