from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from export.stage_pack_manifest_export import build_stage_pack_export_manifest
from tools.build_demo_snowman_stage_pack import build_demo_snowman_stage_pack
from tools.preview_snowman_stage_pack import build_stage_pack_preview_svg


DEFAULT_OUTPUT_DIR = Path("outputs/demo_snowman_stage_pack_bundle")


def build_demo_snowman_stage_bundle_payload() -> dict[str, Any]:
    """Build the canonical demo stage pack plus manifest and preview text.

    This is the one-stop artifact builder for review: it generates the rich
    stage-pack payload, the flattened export manifest, and the preview SVG from
    the same deterministic source data so they cannot drift from each other.
    """
    stage_pack = build_demo_snowman_stage_pack()
    manifest = build_stage_pack_export_manifest(stage_pack)
    preview_svg = build_stage_pack_preview_svg(manifest)
    return {
        "schema": "helix.demo_snowman_stage_bundle.v1",
        "stage_pack": stage_pack,
        "manifest": manifest,
        "preview_svg": preview_svg,
        "summary": {
            "pack_id": stage_pack["pack_id"],
            "stage_pack_status": stage_pack["status"],
            "manifest_rows": manifest["row_count"],
            "drummer_feeds_floor_piano": stage_pack["integration"]["drummer_feeds_floor_piano"],
            "performers": sorted(stage_pack["band_members"]),
            "stage_props": sorted(stage_pack["stage_props"]),
            "timing_tracks": manifest["timing_tracks"],
        },
        "validation": {
            "stage_pack_valid": all(stage_pack["validation"].values()),
            "manifest_valid": all(manifest["validation"].values()),
            "preview_has_floor_piano_link": "drummer → floor piano: ACTIVE" in preview_svg,
            "artifact_sources_are_consistent": manifest["pack_id"] == stage_pack["pack_id"],
        },
    }


def write_demo_snowman_stage_bundle(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    payload = build_demo_snowman_stage_bundle_payload()
    output_dir.mkdir(parents=True, exist_ok=True)

    stage_pack_path = output_dir / "demo_snowman_stage_pack.json"
    manifest_path = output_dir / "demo_snowman_stage_pack_manifest.json"
    preview_path = output_dir / "demo_snowman_stage_pack_preview.svg"
    summary_path = output_dir / "demo_snowman_stage_pack_bundle_summary.json"

    stage_pack_path.write_text(json.dumps(payload["stage_pack"], indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(payload["manifest"], indent=2), encoding="utf-8")
    preview_path.write_text(payload["preview_svg"], encoding="utf-8")
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
