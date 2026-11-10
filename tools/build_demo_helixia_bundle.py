from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from export.helixia_double_helix_xlights_plan import build_double_helix_xlights_plan
from tools.build_demo_snowman_stage_bundle import write_demo_snowman_stage_bundle
from tools.build_helpers.helixia_3d import build_helixia_3d_layout
from tools.build_helpers.helixia_double_helix_integration import build_helixia_layout_with_double_helix
from tools.preview_helixia_3d_layout import build_helixia_3d_preview_svg
from tools.preview_helixia_double_helix import build_double_helix_preview_svg


DEFAULT_OUTPUT_DIR = Path("outputs/demo_helixia_bundle")


def build_demo_helixia_bundle_payload(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    """Build the complete Helixia/Helixville4 review bundle payload.

    This does not mutate committed helixville4 artifacts. It generates a fresh
    review folder containing the classic Helixia manifest/XML, the grounded 3D
    manifest, double-helix previews/plans, and the full snowman stage bundle.
    """
    helixia_layout = build_helixia_layout_with_double_helix(output_dir)
    helixia_3d = build_helixia_3d_layout(output_dir)
    helixia_3d_preview_svg = build_helixia_3d_preview_svg(helixia_3d)
    double_helix = helixia_layout["giant_double_helix"]
    double_helix_preview_svg = build_double_helix_preview_svg(double_helix)
    double_helix_xlights_plan = build_double_helix_xlights_plan(double_helix)
    snowman_bundle_dir = output_dir / "demo_snowman_stage_pack_bundle"
    snowman_bundle_result = write_demo_snowman_stage_bundle(snowman_bundle_dir)
    return {
        "schema": "helixia.demo_bundle.v1",
        "layout": helixia_layout,
        "layout_3d": helixia_3d,
        "layout_3d_preview_svg": helixia_3d_preview_svg,
        "double_helix_preview_svg": double_helix_preview_svg,
        "double_helix_xlights_plan": double_helix_xlights_plan,
        "snowman_stage_bundle": snowman_bundle_result,
        "summary": {
            "layout_id": helixia_layout["layout_id"],
            "layout_name": helixia_layout["layout_name"],
            "xlights_model_count": helixia_layout["xlights_layout"]["model_count"],
            "layout_3d_model_count": len(helixia_3d.get("models", []) or []),
            "layout_3d_stage_model_count": helixia_3d.get("stage_zones", {}).get("model_count", 0),
            "double_helix_model_id": double_helix["model_id"],
            "double_helix_height_ft": double_helix["config"]["height_ft"],
            "double_helix_xlights_effects": len(double_helix_xlights_plan["effect_placements"]),
            "snowman_stage_bundle_dir": snowman_bundle_result["output_dir"],
        },
        "validation": {
            "helixia_manifest_has_double_helix": "giant_double_helix" in helixia_layout,
            "xlights_xml_generated": bool(helixia_layout.get("xlights_layout", {}).get("output_layout")),
            "layout_3d_valid": all(helixia_3d["validation"].values()),
            "all_grounded_models_on_ground": helixia_3d["grounding"]["all_grounded_models_on_ground"],
            "no_grounded_models_below_ground": helixia_3d["grounding"]["no_grounded_models_below_ground"],
            "double_helix_grounded": helixia_3d["validation"]["double_helix_grounded"],
            "double_helix_xlights_plan_valid": all(double_helix_xlights_plan["validation"].values()),
            "double_helix_preview_has_identity": "HELIXIA_DNA_STRAND_A" in double_helix_preview_svg
            and "HELIXIA_DNA_STRAND_B" in double_helix_preview_svg,
            "layout_3d_preview_has_ground_plane": "GROUND PLANE Z=0" in helixia_3d_preview_svg,
            "snowman_stage_bundle_valid": all(snowman_bundle_result["validation"].values()),
        },
    }


def write_demo_helixia_bundle(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_demo_helixia_bundle_payload(output_dir)

    helixia_manifest_path = output_dir / "helixia_manifest.json"
    layout_3d_manifest_path = output_dir / "helixia_3d_manifest.json"
    layout_3d_preview_path = output_dir / "helixia_3d_grounded_preview.svg"
    double_helix_preview_path = output_dir / "helixia_double_helix_preview.svg"
    double_helix_xlights_plan_path = output_dir / "helixia_double_helix_xlights_plan.json"
    summary_path = output_dir / "demo_helixia_bundle_summary.json"

    # build_helixia_layout_with_double_helix and build_helixia_3d_layout already write
    # helixia_manifest.json, HELIXIA_LAYOUT_NOTES.txt, xlights_rgbeffects.xml, and helixia_3d_manifest.json.
    helixia_manifest_path.write_text(json.dumps(payload["layout"], indent=2), encoding="utf-8")
    layout_3d_manifest_path.write_text(json.dumps(payload["layout_3d"], indent=2), encoding="utf-8")
    layout_3d_preview_path.write_text(payload["layout_3d_preview_svg"], encoding="utf-8")
    double_helix_preview_path.write_text(payload["double_helix_preview_svg"], encoding="utf-8")
    double_helix_xlights_plan_path.write_text(json.dumps(payload["double_helix_xlights_plan"], indent=2), encoding="utf-8")
    summary = {
        "schema": payload["schema"],
        "summary": payload["summary"],
        "validation": payload["validation"],
        "artifacts": {
            "helixia_manifest": str(helixia_manifest_path),
            "layout_notes": str(output_dir / "HELIXIA_LAYOUT_NOTES.txt"),
            "xlights_rgbeffects": str(output_dir / "xlights_rgbeffects.xml"),
            "helixia_3d_manifest": str(layout_3d_manifest_path),
            "helixia_3d_preview_svg": str(layout_3d_preview_path),
            "helixia_double_helix_preview_svg": str(double_helix_preview_path),
            "helixia_double_helix_xlights_plan": str(double_helix_xlights_plan_path),
            "snowman_stage_bundle": payload["snowman_stage_bundle"],
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "output_dir": str(output_dir),
        "helixia_manifest": str(helixia_manifest_path),
        "layout_notes": str(output_dir / "HELIXIA_LAYOUT_NOTES.txt"),
        "xlights_rgbeffects": str(output_dir / "xlights_rgbeffects.xml"),
        "helixia_3d_manifest": str(layout_3d_manifest_path),
        "helixia_3d_preview_svg": str(layout_3d_preview_path),
        "helixia_double_helix_preview_svg": str(double_helix_preview_path),
        "helixia_double_helix_xlights_plan": str(double_helix_xlights_plan_path),
        "snowman_stage_bundle": payload["snowman_stage_bundle"],
        "summary": str(summary_path),
        "validation": payload["validation"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the complete demo Helixia/Helixville4 review bundle.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    print(json.dumps(write_demo_helixia_bundle(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
