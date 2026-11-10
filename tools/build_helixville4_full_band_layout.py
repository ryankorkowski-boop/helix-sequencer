from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from tools.build_helpers.helixia import build_helixia_layout
from tools.build_helpers.helixville4_full_band import FULL_BAND_SPECS, add_full_helixville4_band_models
from tools.write_helixville4_band_assets import write_band_assets


def _count_band_models(layout_path: Path) -> dict[str, int]:
    root = ET.parse(layout_path).getroot()
    names = {spec.model_name for spec in FULL_BAND_SPECS}
    models = [model for model in root.findall(".//model") if model.attrib.get("name") in names]
    submodels = [sub for model in models for sub in model.findall("subModel")]
    return {
        "band_model_count": len(models),
        "band_submodel_count": len(submodels),
    }


def build_full_band_layout(output_dir: str | Path) -> dict[str, object]:
    out_dir = Path(output_dir)
    payload = build_helixia_layout(out_dir, use_helixville4_band_model_specs=False)
    layout_path = out_dir / "xlights_rgbeffects.xml"

    add_full_helixville4_band_models(layout_path)
    band_assets = write_band_assets(out_dir / "band_assets")
    band_counts = _count_band_models(layout_path)

    payload["approved_full_band_export"] = {
        "schema": "helixville4.approved_full_band_export.v1",
        "state": "approved_design_full_band_v1",
        "layout_path": str(layout_path),
        "models": [
            {
                "model_name": spec.model_name,
                "state": spec.state,
                "visual_target": spec.visual_target,
                "submodel_count": len(spec.parts),
                "animation_states": list(spec.animation_states),
            }
            for spec in FULL_BAND_SPECS
        ],
        **band_counts,
    }
    payload["band_assets"] = band_assets
    payload["xlights_layout"] = dict(payload.get("xlights_layout", {}))
    payload["xlights_layout"]["approved_full_band_enabled"] = True
    payload["xlights_layout"].update(band_counts)

    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "HELIXIA_LAYOUT_NOTES.txt").write_text(
        "Helixville4 approved full snowman band layout generated.\n"
        "All five band members are exported as non-placeholder custom models with named submodels.\n"
        "Visual targets are recorded in docs/HELIXVILLE4_VISUAL_REFERENCE_MANIFEST.md.\n",
        encoding="utf-8",
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Helixville4 with the approved full snowman band wired into xLights XML.")
    parser.add_argument("--output-dir", type=Path, default=Path("test_runs/helixville4_full_band"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_full_band_layout(args.output_dir)
    print(json.dumps(payload.get("approved_full_band_export", {}), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
