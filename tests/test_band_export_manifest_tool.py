from __future__ import annotations

import json

from tools.export_band_performance_manifest import export_demo_manifest


EXPECTED_MODELS = {
    "HX_SNOWMAN_DRUMMER",
    "HX_SNOWMAN_GUITARIST",
    "HX_SNOWMAN_BASSIST",
    "HX_SNOWMAN_SINGER",
    "HX_SNOWMAN_SINGER_FEMALE",
}
EXPECTED_PERFORMERS = {"drummer", "guitarist", "bassist", "singer", "female_singer"}


def test_export_band_performance_manifest_writes_expected_files(tmp_path) -> None:
    manifest_path = export_demo_manifest(tmp_path)
    summary_path = tmp_path / "HELIXVILLE4_BAND_SUMMARY.txt"

    assert manifest_path.exists()
    assert summary_path.exists()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    xlights_export = payload["xlights_export"]

    assert payload["schema"] == "helixville4.band_demo_manifest.v1"
    assert payload["runtime_catalog"]["performer_count"] == 5
    assert set(payload["runtime_catalog"]["model_names"]) == EXPECTED_MODELS
    assert set(xlights_export["models"]) == EXPECTED_MODELS
    assert set(xlights_export["performers"]) == EXPECTED_PERFORMERS
    assert xlights_export["effect_count"] > 0
