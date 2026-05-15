from __future__ import annotations

from pathlib import Path

from tools.run_lightsout_layout_regression_matrix import build_matrix_cases, run_matrix



def test_matrix_contains_requested_cases() -> None:
    cases = {case.name: case for case in build_matrix_cases()}

    assert "allmodels_lightsout_showcase" in cases
    assert "aaatest_allmodels_pack" in cases
    assert "helixville4_full_band_lightsout_30s" in cases
    assert "helixville4_full_band_lightsout_30s_dry_run" in cases



def test_matrix_records_required_assets() -> None:
    cases = {case.name: case for case in build_matrix_cases()}

    assert "allmodels/xlights_rgbeffects.xml" in cases["allmodels_lightsout_showcase"].required_assets
    assert "allmodels/xlights_rgbeffects.xml" in cases["aaatest_allmodels_pack"].required_assets
    assert "LightsOutTheme.mp3" in cases["helixville4_full_band_lightsout_30s"].required_assets



def test_matrix_report_writes_without_execution(tmp_path: Path) -> None:
    report = tmp_path / "matrix_report.json"
    payload = run_matrix(execute=False, report_path=report)

    assert report.exists()
    assert payload["schema"] == "helix.lightsout_layout_regression_matrix.v1"
    assert payload["case_count"] == 4
