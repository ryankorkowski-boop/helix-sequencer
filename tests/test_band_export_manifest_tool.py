from __future__ import annotations

import json

from tools.export_band_performance_manifest import export_demo_manifest


def test_export_band_performance_manifest_writes_expected_files(tmp_path) -> None:
    manifest_path = export_demo_manifest(tmp_path)
    summary_path = tmp_path / "HELIXVILLE4_BAND_SUMMARY.txt"

    assert manifest_path.exists()
    assert summary_path.exists()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "helixville4.band_demo_manifest.v1"
    assert payload["runtime_catalog"]["performer_count"] == 5
    assert payload["xlights_export"]["effect_count"] > 0
