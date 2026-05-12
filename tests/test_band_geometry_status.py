from __future__ import annotations

from tools.report_band_geometry_status import build_band_geometry_status



def test_band_geometry_status_reports_all_performers() -> None:
    report = build_band_geometry_status()

    assert report["accepted_model_count"] == 5
    assert len(report["performers"]) == 5



def test_band_geometry_status_reports_geometry_state() -> None:
    report = build_band_geometry_status()

    assert "geometry_complete" in report
    assert "missing_geometry_models" in report
