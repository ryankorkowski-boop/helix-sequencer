from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from export.helixia_double_helix_xlights_plan import build_double_helix_xlights_plan
from export.stage_pack_manifest_export import build_stage_pack_export_manifest
from models.working_double_helix import build_reactive_double_helix_from_manifest
from tools.build_demo_snowman_stage_pack import build_demo_snowman_stage_pack
from tools.preview_helixia_double_helix import build_double_helix_preview_svg
from tools.preview_snowman_stage_pack import build_stage_pack_preview_svg


DEFAULT_OUTPUT_DIR = Path("outputs/demo_snowman_stage_pack_bundle")


def build_demo_snowman_stage_bundle_payload() -> dict[str, Any]:
    """Build the canonical demo stage pack plus manifest and previews.

    This is the one-stop artifact builder for review: it generates the rich
    stage-pack payload, the flattened export manifest, the snowman stage preview,
    and the reactive giant-double-helix artifacts from the same deterministic
    source data so they cannot drift from each other.
    """
    stage_pack = build_demo_snowman_stage_pack()
    manifest = build_stage_pack_export_manifest(stage_pack)
    preview_svg = build_stage_pack_preview_svg(manifest)
    reactive_double_helix = build_reactive_double_helix_from_manifest(manifest)
    double_helix_preview_svg = build_double_helix_preview_svg(reactive_double_helix["geometry"])
    double_helix_xlights_plan = build_double_helix_xlights_plan(reactive_double_helix["geometry"])
    return {
        "schema": "helix.demo_snowman_stage_bundle.v1",
        "stage_pack": stage_pack,
        "manifest": manifest,
        "preview_svg": preview_svg,
        "reactive_double_helix": reactive_double_helix,
        "double_helix_preview_svg": double_helix_preview_svg,
        "double_helix_xlights_plan": double_helix_xlights_plan,
        "summary": {
            "pack_id": stage_pack["pack_id"],
            "stage_pack_status": stage_pack["status"],
            "manifest_rows": manifest["row_count"],
            "drummer_feeds_floor_piano": stage_pack["integration"]["drummer_feeds_floor_piano"],
            "performers": sorted(stage_pack["band_members"]),
            "stage_props": sorted(stage_pack["stage_props"]),
            "timing_tracks": manifest["timing_tracks"],
            "double_helix_status": reactive_double_helix["status"],
            "double_helix_cues": len(reactive_double_helix.get("reactive_cues", [])),
            "double_helix_targets": reactive_double_helix.get("reactive_debug", {}).get("cue_targets", []),
        },
        "validation": {
            "stage_pack_valid": all(stage_pack["validation"].values()),
            "manifest_valid": all(manifest["validation"].values()),
            "preview_has_floor_piano_link": "drummer → floor piano: ACTIVE" in preview_svg,
            "artifact_sources_are_consistent": manifest["pack_id"] == stage_pack["pack_id"],
            "double_helix_reactive": bool(reactive_double_helix["validation"].get("has_reactive_cues")),
            "double_helix_targets_valid": bool(
                reactive_double_helix["validation"].get("reactive_cues_target_existing_submodels")
            ),
            "double_helix_has_audio_in_and_lights_out": bool(
                reactive_double_helix["validation"].get("has_audio_in_and_lights_out")
            ),
            "double_helix_xlights_plan_valid": all(double_helix_xlights_plan["validation"].values()),
            "double_helix_preview_has_identity": "HELIXIA_DNA_STRAND_A" in double_helix_preview_svg
            and "HELIXIA_DNA_STRAND_B" in double_helix_preview_svg,
        },
    }


def write_demo_snowman_stage_bundle(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    payload = build_demo_snowman_stage_bundle_payload()
    output_dir.mkdir(parents=True, exist_ok=True)

    stage_pack_path = output_dir / "demo_snowman_stage_pack.json"
    manifest_path = output_dir / "demo_snowman_stage_pack_manifest.json"
    preview_path = output_dir / "demo_snowman_stage_pack_preview.svg"
    double_helix_path = output_dir / "demo_snowman_stage_pack_double_helix.json"
    double_helix_preview_path = output_dir / "helixia_double_helix_preview.svg"
    double_helix_xlights_plan_path = output_dir / "helixia_double_helix_xlights_plan.json"
    summary_path = output_dir / "demo_snowman_stage_pack_bundle_summary.json"

    stage_pack_path.write_text(json.dumps(payload["stage_pack"], indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(payload["manifest"], indent=2), encoding="utf-8")
    preview_path.write_text(payload["preview_svg"], encoding="utf-8")
    double_helix_path.write_text(json.dumps(payload["reactive_double_helix"], indent=2), encoding="utf-8")
    double_helix_preview_path.write_text(payload["double_helix_preview_svg"], encoding="utf-8")
    double_helix_xlights_plan_path.write_text(json.dumps(payload["double_helix_xlights_plan"], indent=2), encoding="utf-8")
    summary_path.write_text(
        json.dumps(
            {
                "schema": payload["schema"],
                "summary": payload["summary"],
                "validation": payload["validation"],
                "artifacts": {
                    "stage_pack": str(stage_pack_path),
                    "manifest": str(manifest_path),
                    "preview_svg": str(preview_path),
                    "reactive_double_helix": str(double_helix_path),
                    "double_helix_preview_svg": str(double_helix_preview_path),
                    "double_helix_xlights_plan": str(double_helix_xlights_plan_path),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "output_dir": str(output_dir),
        "stage_pack": str(stage_pack_path),
        "manifest": str(manifest_path),
        "preview_svg": str(preview_path),
        "reactive_double_helix": str(double_helix_path),
        "double_helix_preview_svg": str(double_helix_preview_path),
        "double_helix_xlights_plan": str(double_helix_xlights_plan_path),
        "summary": str(summary_path),
        "validation": payload["validation"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the full demo snowman stage pack artifact bundle.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    print(json.dumps(write_demo_snowman_stage_bundle(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
