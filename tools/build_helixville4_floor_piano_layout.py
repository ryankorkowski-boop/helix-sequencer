from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from tools.build_helpers.helixia import build_helixia_layout
from tools.build_helpers.helixville4_floor_piano import FLOOR_PIANO_KEYS, add_floor_piano_to_layout


def _count_floor_piano(layout_path: Path) -> dict[str, int]:
    root = ET.parse(layout_path).getroot()
    model = root.find(".//model[@name='HX_FLOOR_PIANO']")
    if model is None:
        return {"floor_piano_model_count": 0, "floor_piano_submodel_count": 0, "floor_piano_note_count": 0}
    submodels = model.findall("subModel")
    note_names = {f"HX_FLOOR_PIANO_{key.label}" for key in FLOOR_PIANO_KEYS}
    note_count = sum(1 for sub in submodels if sub.attrib.get("name") in note_names)
    return {
        "floor_piano_model_count": 1,
        "floor_piano_submodel_count": len(submodels),
        "floor_piano_note_count": note_count,
    }


def build_floor_piano_layout(output_dir: str | Path) -> dict[str, object]:
    out_dir = Path(output_dir)
    payload = build_helixia_layout(out_dir, use_helixville4_band_model_specs=False)
    layout_path = out_dir / "xlights_rgbeffects.xml"
    add_floor_piano_to_layout(layout_path)
    counts = _count_floor_piano(layout_path)

    payload["floor_piano_export"] = {
        "schema": "helixville4.floor_piano_export.v1",
        "state": "floor_piano_note_reactive_v1",
        "layout_path": str(layout_path),
        "model_name": "HX_FLOOR_PIANO",
        "visual_target": "docs/HELIXVILLE4_FLOOR_PIANO_TARGET.md",
        "sequence_axis": "low_to_high",
        "note_order": [key.label for key in FLOOR_PIANO_KEYS],
        **counts,
    }
    payload["xlights_layout"] = dict(payload.get("xlights_layout", {}))
    payload["xlights_layout"]["floor_piano_enabled"] = True
    payload["xlights_layout"].update(counts)

    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "HELIXIA_LAYOUT_NOTES.txt").write_text(
        "Helixville4 floor piano layout generated.\n"
        "HX_FLOOR_PIANO is exported as a note-reactive sequential custom model.\n"
        "The floor piano is the reference implementation for reusable sequential model layering.\n",
        encoding="utf-8",
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Helixville4 with the note-reactive floor piano wired into xLights XML.")
    parser.add_argument("--output-dir", type=Path, default=Path("test_runs/helixville4_floor_piano"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_floor_piano_layout(args.output_dir)
    print(json.dumps(payload.get("floor_piano_export", {}), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
