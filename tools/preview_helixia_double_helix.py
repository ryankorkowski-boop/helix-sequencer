from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from models.helixia_double_helix import build_giant_double_helix


DEFAULT_OUTPUT_PATH = Path("outputs/helixia_double_helix_preview.svg")


def _svg_escape(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _project(point: Mapping[str, Any], *, bounds: Mapping[str, float], width: int = 420, height: int = 720) -> tuple[float, float]:
    min_x = float(bounds["min_x_ft"])
    max_x = float(bounds["max_x_ft"])
    min_y = float(bounds["min_y_ft"])
    max_y = float(bounds["max_y_ft"])
    x = float(point["world_x_ft"])
    y = float(point["world_y_ft"])
    # Slight z contribution makes the crossing/twist readable in a 2D preview.
    z = float(point.get("world_z_ft", 0.0))
    norm_x = (x - min_x) / max(1e-9, max_x - min_x)
    norm_y = (y - min_y) / max(1e-9, max_y - min_y)
    px = 50 + norm_x * (width - 100) + z * 0.42
    py = height - 70 - norm_y * (height - 140)
    return round(px, 3), round(py, 3)


def _polyline(points: Iterable[Mapping[str, Any]], *, bounds: Mapping[str, float]) -> str:
    return " ".join(f"{x},{y}" for x, y in (_project(point, bounds=bounds) for point in points))


def _rung_lines(payload: Mapping[str, Any]) -> str:
    bounds = payload["bounds_ft"]
    strand_a = {point["node_id"]: point for point in payload["strand_a"]}
    strand_b = {point["node_id"]: point for point in payload["strand_b"]}
    parts: list[str] = []
    for rung_idx, rung in enumerate(payload["rungs"]):
        a = strand_a[rung["strand_a_node"]]
        b = strand_b[rung["strand_b_node"]]
        x1, y1 = _project(a, bounds=bounds)
        x2, y2 = _project(b, bounds=bounds)
        color = ["#f7ff72", "#6efcff", "#ff79d7", "#8cff8c", "#ffb66e"][rung_idx % 5]
        parts.append(
            f'<line class="dna-rung" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="4" stroke-linecap="round" opacity="0.82"/>'
        )
    return "\n    ".join(parts)


def build_double_helix_preview_svg(payload: Mapping[str, Any] | None = None) -> str:
    payload = payload or build_giant_double_helix()
    bounds = payload["bounds_ft"]
    strand_a_points = _polyline(payload["strand_a"], bounds=bounds)
    strand_b_points = _polyline(payload["strand_b"], bounds=bounds)
    rungs = _rung_lines(payload)
    config = payload["config"]
    top_count = len(payload["submodels"]["HELIXIA_DNA_TOP_INPUT"])
    bottom_count = len(payload["submodels"]["HELIXIA_DNA_BOTTOM_OUTPUT"])
    rung_count = len(payload["rungs"])
    node_count = len(payload["strand_a"]) + len(payload["strand_b"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="820" viewBox="0 0 520 820">
  <defs>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <linearGradient id="strandA" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0%" stop-color="#6efcff"/>
      <stop offset="45%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#ff79d7"/>
    </linearGradient>
    <linearGradient id="strandB" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0%" stop-color="#ff79d7"/>
      <stop offset="45%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#6efcff"/>
    </linearGradient>
  </defs>
  <rect width="520" height="820" fill="#07101d"/>
  <circle cx="260" cy="745" r="118" fill="#111f2e" stroke="#f6f2d8" stroke-width="5" opacity="0.95"/>
  <circle cx="260" cy="745" r="96" fill="none" stroke="#f7ff72" stroke-width="2" opacity="0.55"/>

  <text x="260" y="36" text-anchor="middle" fill="#ffffff" font-size="22" font-weight="700">Helixia Giant Lighted Double Helix</text>
  <text x="260" y="60" text-anchor="middle" fill="#b8d7ff" font-size="12">geometry preview · {node_count} strand nodes · {rung_count} rungs · {config['height_ft']} ft tall</text>

  <rect x="58" y="78" width="404" height="54" rx="14" fill="#101e31" stroke="#6efcff" opacity="0.92"/>
  <text x="260" y="100" text-anchor="middle" fill="#6efcff" font-size="13" font-weight="700">AUDIO INPUT / UNTWINED TOP ZONE</text>
  <text x="260" y="119" text-anchor="middle" fill="#d7f7ff" font-size="10">HELIXIA_DNA_TOP_INPUT · {_svg_escape(top_count)} nodes</text>

  <g id="HELIXIA_DNA_RUNGS" filter="url(#glow)">
    {rungs}
  </g>
  <polyline id="HELIXIA_DNA_STRAND_A" points="{strand_a_points}" fill="none" stroke="url(#strandA)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>
  <polyline id="HELIXIA_DNA_STRAND_B" points="{strand_b_points}" fill="none" stroke="url(#strandB)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>

  <rect x="66" y="704" width="388" height="52" rx="14" fill="#101e31" stroke="#ff79d7" opacity="0.93"/>
  <text x="260" y="726" text-anchor="middle" fill="#ff79d7" font-size="13" font-weight="700">LIGHTS OUT / FINISHED OUTPUT ZONE</text>
  <text x="260" y="744" text-anchor="middle" fill="#ffe6fb" font-size="10">HELIXIA_DNA_BOTTOM_OUTPUT · {_svg_escape(bottom_count)} nodes</text>

  <text x="260" y="790" text-anchor="middle" fill="#d8e6f3" font-size="11">Audio in. Lights out. The helix is generated from real 3D model coordinates.</text>
</svg>
'''


def write_double_helix_preview(path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    payload = build_giant_double_helix()
    svg = build_double_helix_preview_svg(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    return {
        "path": str(path),
        "model_id": payload["model_id"],
        "strand_nodes": len(payload["strand_a"]) + len(payload["strand_b"]),
        "rungs": len(payload["rungs"]),
        "top_input_nodes": len(payload["submodels"]["HELIXIA_DNA_TOP_INPUT"]),
        "bottom_output_nodes": len(payload["submodels"]["HELIXIA_DNA_BOTTOM_OUTPUT"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an SVG preview for the Helixia giant double helix geometry.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    print(json.dumps(write_double_helix_preview(args.output), indent=2))


if __name__ == "__main__":
    main()
