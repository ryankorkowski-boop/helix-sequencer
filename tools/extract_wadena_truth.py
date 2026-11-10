"""Extract a compact physical/electrical inventory from xLights layout XML.

Usage:
    python tools/extract_wadena_truth.py xlights_rgbeffects.xml data/wadena/WADENA_256_TRUTH.json

The extractor never rewrites the source layout and preserves the source model
name, start channel, string type, world coordinates and point geometry when
available.  It is intentionally conservative: unknown physical semantics are
left unknown instead of guessed.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def model_record(model: ET.Element) -> dict[str, object]:
    def f(name: str, default: float = 0.0) -> float:
        try:
            return float(model.get(name, default))
        except (TypeError, ValueError):
            return default

    start = model.get("StartChannel")
    try:
        start_channel: int | None = int(start) if start else None
    except ValueError:
        start_channel = None

    return {
        "name": model.get("name", ""),
        "display_as": model.get("DisplayAs", ""),
        "string_type": model.get("StringType", ""),
        "start_channel": start_channel,
        "world": {"x": f("WorldPosX"), "y": f("WorldPosY"), "z": f("WorldPosZ")},
        "end": {"x": f("X2"), "y": f("Y2"), "z": f("Z2")},
        "num_points": int(model.get("NumPoints", "0") or 0),
        "point_data": model.get("PointData", ""),
        "layout_group": model.get("LayoutGroup", ""),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: extract_wadena_truth.py INPUT_XML OUTPUT_JSON", file=sys.stderr)
        return 2
    source = Path(argv[1])
    destination = Path(argv[2])
    root = ET.parse(source).getroot()
    models = [model_record(node) for node in root.findall(".//model")]
    payload = {
        "schema": "helix.wadena.truth.v1",
        "source": str(source),
        "model_count": len(models),
        "models": models,
        "notes": [
            "Electrical truth is taken from the source xLights layout.",
            "Physical element semantics are not inferred by this extractor.",
            "R/G/W single-color models remain independent channels.",
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(models)} models to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
