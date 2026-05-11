from __future__ import annotations

from core.band_vocal_face_export import BandVocalFaceExportCompiler, VocalPhonemeTiming, build_demo_vocal_face_timings
from models.helixville4_vocal_phonemes import PHONEME_BY_NAME
from tools.export_band_performance_manifest import build_demo_manifest


def test_vocal_face_export_emits_faces_for_both_vocalists() -> None:
    manifest = BandVocalFaceExportCompiler().build_manifest(build_demo_vocal_face_timings())

    assert manifest["schema"] == "helixville4.band_vocal_face_export.v1"
    assert set(manifest["performers"]) == {"singer", "female_singer"}
    assert set(manifest["models"]) == {"HX_SNOWMAN_SINGER", "HX_SNOWMAN_SINGER_FEMALE"}
    assert set(manifest["phonemes"]) <= set(PHONEME_BY_NAME)
    assert all(effect["effect_type"] == "Faces" for effect in manifest["effects"])
    assert all(effect["timing_track"] == "helixville4_vocal_phonemes" for effect in manifest["effects"])


def test_vocal_face_export_rejects_unknown_phoneme() -> None:
    compiler = BandVocalFaceExportCompiler()
    try:
        compiler.compile_timing(VocalPhonemeTiming("singer", "NOPE", 0.0, 0.25))
    except ValueError as exc:
        assert "Unsupported vocal phoneme" in str(exc)
    else:
        raise AssertionError("unknown phoneme should fail")


def test_band_demo_manifest_includes_vocal_face_export() -> None:
    payload = build_demo_manifest()
    assert payload["vocal_face_export"]["schema"] == "helixville4.band_vocal_face_export.v1"
    assert payload["vocal_face_export"]["effect_count"] > 0
    assert set(payload["vocal_face_export"]["performers"]) == {"singer", "female_singer"}
