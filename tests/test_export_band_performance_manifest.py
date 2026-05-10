from __future__ import annotations

import json
from pathlib import Path

from tools.export_band_performance_manifest import build_demo_manifest, export_demo_manifest


def test_build_demo_manifest_contains_complete_performer_pipeline() -> None:
    manifest = build_demo_manifest()

    assert manifest["schema"] == "helixville4.band_demo_manifest.v1"
    assert manifest["runtime_catalog"]["performer_count"] == 5
    assert manifest["intent_count"] == 2
    assert manifest["expanded_event_count"] > 0
    assert manifest["adapted_event_count"] > 0
    assert manifest["timeline_event_count"] > 0

    export = manifest["xlights_export"]

    assert export["schema"] == "helixville4.band_xlights_export.v1"
    assert sorted(export["performers"]) == [
        "bassist",
        "drummer",
        "female_singer",
        "guitarist",
        "singer",
    ]
    assert set(export["models"]) == {
        "HX_SNOWMAN_BASSIST",
        "HX_SNOWMAN_DRUMMER",
        "HX_SNOWMAN_GUITARIST",
        "HX_SNOWMAN_SINGER",
        "HX_SNOWMAN_SINGER_FEMALE",
    }
    assert export["effect_count"] == len(export["effects"])


def test_export_demo_manifest_writes_review_artifacts(tmp_path: Path) -> None:
    manifest_path = export_demo_manifest(tmp_path)
    summary_path = tmp_path / "HELIXVILLE4_BAND_SUMMARY.txt"

    assert manifest_path.exists()
    assert summary_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema"] == "helixville4.band_demo_manifest.v1"
    assert manifest["runtime_catalog"]["state"] == "approved_finished_band_members_v1"
    assert manifest["xlights_export"]["effect_count"] > 0
    assert "all five runtime performers" in summary_path.read_text(encoding="utf-8")
