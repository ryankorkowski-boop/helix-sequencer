from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from tools.build_helpers.helixia import build_helixia_layout
from tools.build_helpers.helixville4_full_band import FULL_BAND_SPECS, add_full_helixville4_band_models
from tools.build_helpers.helixville4_visible_band import upgrade_visible_band_models
from tools.write_helixville4_band_assets import write_band_assets

XLIGHTS_DISPLAY_TYPE_ALIASES = {
    "CandyCane": "Candy Canes",
    "Matrix": "Horiz Matrix",
    "Icicles": "Poly Line",
    "DMX General": "Single Line",
}


def _count_band_models(layout_path: Path) -> dict[str, int]:
    root = ET.parse(layout_path).getroot()
    names = {spec.model_name for spec in FULL_BAND_SPECS}
    models = [model for model in root.findall(".//model") if model.attrib.get("name") in names]
    submodels = [sub for model in models for sub in model.findall("subModel")]
    return {
        "band_model_count": len(models),
        "band_submodel_count": len(submodels),
    }


def _layout_model_count(layout_path: Path) -> int:
    return len(ET.parse(layout_path).getroot().findall(".//model"))


def normalize_xlights_display_types(layout_path: Path) -> dict[str, int]:
    tree = ET.parse(layout_path)
    root = tree.getroot()
    fixed: dict[str, int] = {}
    for model in root.findall(".//model"):
        display_as = model.attrib.get("DisplayAs")
        replacement = XLIGHTS_DISPLAY_TYPE_ALIASES.get(display_as or "")
        if replacement is None:
            continue
        model.attrib["DisplayAs"] = replacement
        fixed[display_as or ""] = fixed.get(display_as or "", 0) + 1
    if fixed:
        tree.write(layout_path, encoding="utf-8", xml_declaration=True)
    return fixed


def build_full_band_layout(output_dir: str | Path, *, source_layout: str | Path | None = None) -> dict[str, object]:
    out_dir = Path(output_dir)
    layout_path = out_dir / "xlights_rgbeffects.xml"
    source_layout_path = Path(source_layout).resolve() if source_layout is not None else None
    if source_layout_path is not None:
        if not source_layout_path.exists():
            raise FileNotFoundError(f"Source layout not found: {source_layout_path}")
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_layout_path, layout_path)
        payload: dict[str, object] = {
            "layout_id": "helixville4_preserved_source_layout",
            "layout_source": str(source_layout_path),
            "source_model_count": _layout_model_count(layout_path),
            "preservation_policy": "copy_source_layout_then_patch_band_models_only",
        }
    else:
        payload = build_helixia_layout(out_dir)

    display_type_fixes = normalize_xlights_display_types(layout_path)
    add_full_helixville4_band_models(layout_path, include_performer_models=False)
    visible_upgrade = upgrade_visible_band_models(layout_path, create_missing=True)
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
    payload["visible_band_upgrade"] = visible_upgrade
    payload["band_assets"] = band_assets
    payload["xlights_layout"] = dict(payload.get("xlights_layout", {}))
    payload["xlights_layout"]["approved_full_band_enabled"] = True
    payload["xlights_layout"]["display_type_fixes"] = display_type_fixes
    payload["xlights_layout"]["visible_band_upgrade"] = visible_upgrade
    payload["xlights_layout"]["model_count_after_patch"] = _layout_model_count(layout_path)
    payload["xlights_layout"].update(band_counts)

    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "HELIXIA_LAYOUT_NOTES.txt").write_text(
        "Helixville4 approved full snowman band layout patched.\n"
        "When a source layout is supplied, non-band models are preserved and only band models are replaced/upgraded.\n"
        "The live layout uses xLights-safe split band rows; full performer xmodels are exported as separate assets.\n"
        "Visual targets are recorded in docs/HELIXVILLE4_VISUAL_REFERENCE_MANIFEST.md.\n",
        encoding="utf-8",
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Helixville4 with the approved full snowman band wired into xLights XML.")
    parser.add_argument("--output-dir", type=Path, default=Path("test_runs/helixville4_full_band"))
    parser.add_argument("--source-layout", type=Path, default=None, help="Existing xlights_rgbeffects.xml to copy and patch instead of rebuilding the full layout.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_full_band_layout(args.output_dir, source_layout=args.source_layout)
    print(json.dumps(payload.get("approved_full_band_export", {}), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
