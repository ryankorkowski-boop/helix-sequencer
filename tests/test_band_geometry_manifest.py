from __future__ import annotations

from tools.report_band_geometry_status import build_band_geometry_status, load_geometry_manifest

EXPECTED_MODELS = {
    "HX_SNOWMAN_DRUMMER_V3",
    "HX_SNOWMAN_GUITARIST",
    "HX_SNOWMAN_BASSIST",
    "HX_SNOWMAN_SINGER",
    "HX_SNOWMAN_SINGER_FEMALE",
}


def test_geometry_manifest_contains_exact_active_runtime_models() -> None:
    manifest = load_geometry_manifest()
    assert set(manifest["models"]) == EXPECTED_MODELS
    assert "HX_SNOWMAN_DRUMMER" not in manifest["models"]
    assert "HX_SNOWMAN_DRUMMER" in manifest["archived_models"]


def test_geometry_status_reports_all_five_active_performers() -> None:
    report = build_band_geometry_status()
    assert report["accepted_model_count"] == 5
    assert len(report["performers"]) == 5
    assert {entry["model_name"] for entry in report["performers"]} == EXPECTED_MODELS


def test_active_v3_manifest_has_exact_eight_runtime_targets() -> None:
    manifest = load_geometry_manifest()
    submodels = manifest["models"]["HX_SNOWMAN_DRUMMER_V3"]["submodels"]
    assert len(submodels) == 8
    assert set(submodels) == {
        "HX_SNOWMAN_DRUMMER_V3_KICK","HX_SNOWMAN_DRUMMER_V3_SNARE","HX_SNOWMAN_DRUMMER_V3_HI_HAT",
        "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH","HX_SNOWMAN_DRUMMER_V3_TOM_MID","HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR",
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT","HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
    }
