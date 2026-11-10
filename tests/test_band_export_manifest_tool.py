from __future__ import annotations

import json

from tools.export_band_performance_manifest import ARTIFACT_FILENAMES, export_demo_manifest


EXPECTED_MODELS = {
    "HX_SNOWMAN_DRUMMER",
    "HX_SNOWMAN_GUITARIST",
    "HX_SNOWMAN_BASSIST",
    "HX_SNOWMAN_SINGER",
    "HX_SNOWMAN_SINGER_FEMALE",
}
EXPECTED_PERFORMERS = {"drummer", "guitarist", "bassist", "singer", "female_singer"}


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_export_band_performance_manifest_writes_expected_files(tmp_path) -> None:
    manifest_path = export_demo_manifest(tmp_path)
    summary_path = tmp_path / ARTIFACT_FILENAMES["summary"]
    runtime_path = tmp_path / ARTIFACT_FILENAMES["runtime_catalog"]
    xlights_path = tmp_path / ARTIFACT_FILENAMES["xlights_export"]
    vocal_face_path = tmp_path / ARTIFACT_FILENAMES["vocal_face_export"]

    assert manifest_path.exists()
    assert summary_path.exists()
    assert runtime_path.exists()
    assert xlights_path.exists()
    assert vocal_face_path.exists()

    payload = _read_json(manifest_path)
    runtime_catalog = _read_json(runtime_path)
    xlights_export = _read_json(xlights_path)
    vocal_face_export = _read_json(vocal_face_path)

    assert payload["schema"] == "helixville4.band_demo_manifest.v1"
    assert runtime_catalog == payload["runtime_catalog"]
    assert xlights_export == payload["xlights_export"]
    assert vocal_face_export == payload["vocal_face_export"]

    assert runtime_catalog["performer_count"] == 5
    assert set(runtime_catalog["model_names"]) == EXPECTED_MODELS
    assert set(xlights_export["models"]) == EXPECTED_MODELS
    assert set(xlights_export["performers"]) == EXPECTED_PERFORMERS
    assert xlights_export["effect_count"] > 0
    assert set(vocal_face_export["performers"]) == {"singer", "female_singer"}
