from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tools.build_helpers.helixia import build_helixia_layout
from tools.build_helpers.helixville4_finished_band import add_finished_helixville4_band_models
from tools.write_helixville4_band_assets import write_band_assets


def build_finished_drummer_layout(output_dir: str | Path) -> dict[str, object]:
    out_dir = Path(output_dir)
    payload = build_helixia_layout(out_dir, use_helixville4_band_model_specs=False)
    layout_path = out_dir / "xlights_rgbeffects.xml"
    add_finished_helixville4_band_models(layout_path)
    band_assets = write_band_assets(out_dir / "band_assets")
    payload["finished_band_export"] = {
        "schema": "helixville4.finished_band_export.v1",
        "drummer_model": "HX_SNOWMAN_DRUMMER",
        "drummer_state": "finished_drummer_v1",
        "drummer_submodel_count": 23,
        "drummer_visual_target": "docs/HELIXVILLE4_DRUMMER_TARGET.md",
        "layout_path": str(layout_path),
        "remaining_members_state": "placeholder_pending_finished_exporter",
    }
    payload["band_assets"] = band_assets
    payload["xlights_layout"] = dict(payload.get("xlights_layout", {}))
    payload["xlights_layout"]["band_model_specs_enabled"] = True
    payload["xlights_layout"]["finished_drummer_enabled"] = True
    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "HELIXIA_LAYOUT_NOTES.txt").write_text(
        "Helixville4 finished drummer layout generated.\n"
        "HX_SNOWMAN_DRUMMER uses finished_drummer_v1 custom model geometry with 23 named submodels.\n"
        "Singer, guitarist, and bassist are still placeholder_pending_finished_exporter.\n",
        encoding="utf-8",
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Helixville4 with the finished snowman drummer model wired into xLights XML.")
    parser.add_argument("--output-dir", type=Path, default=Path("test_runs/helixville4_finished_drummer"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_finished_drummer_layout(args.output_dir)
    print(json.dumps(payload.get("finished_band_export", {}), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
