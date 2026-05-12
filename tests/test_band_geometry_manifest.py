from __future__ import annotations

from tools.report_band_geometry_status import build_band_geometry_status, load_geometry_manifest


EXPECTED_MODELS = {
    "HX_SNOWMAN_DRUMMER",
    "HX_SNOWMAN_GUITARIST",
    "HX_SNOWMAN_BASSIST",
    "HX_SNOWMAN_SINGER",
    "HX_SNOWMAN_SINGER_FEMALE",
}



def test_geometry_manifest_contains_all_accepted_models() -> None:
    manifest = load_geometry_manifest()

    assert set(manifest["models"]) == EXPECTED_MODELS



def test_geometry_status_reports_all_manifested_models() -> None:
    report = build_band_geometry_status()

    assert report["accepted_model_count"] == 5
    assert len(report["performers"]) == 5

    performer_models = {entry["model_name"] for entry in report["performers"]}
    assert performer_models == EXPECTED_MODELS
