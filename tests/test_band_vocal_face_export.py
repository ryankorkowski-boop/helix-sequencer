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


def test_harmony_requires_independent_non_rest_events() -> None:
    """Idle/body light or a lead-only demo must not count as backup singing."""
    compiler = BandVocalFaceExportCompiler()
    lead_only = compiler.build_manifest((
        VocalPhonemeTiming("singer", "AH", 0.0, 0.2),
        VocalPhonemeTiming("female_singer", "REST", 0.0, 0.2),
    ))
    assert not any(
        effect["performer"] == "female_singer" and effect["phoneme"] != "REST"
        and effect["intensity"] > 0
        for effect in lead_only["effects"]
    )
    harmony = compiler.build_manifest((
        VocalPhonemeTiming("singer", "AH", 0.0, 0.2),
        VocalPhonemeTiming("female_singer", "OH", 0.35, 0.22),
    ))
    assert any(
        effect["performer"] == "female_singer" and effect["phoneme"] != "REST"
        and effect["intensity"] > 0 and effect["end"] > effect["start"]
        for effect in harmony["effects"]
    )
    assert {effect["start"] for effect in harmony["effects"] if effect["performer"] == "singer"} != {
        effect["start"] for effect in harmony["effects"] if effect["performer"] == "female_singer"
    }


def test_vocal_export_rejects_invalid_timing_and_nonfinite_intensity() -> None:
    import math
    compiler = BandVocalFaceExportCompiler()
    for start, duration, intensity in (
        (-0.1, 0.2, 1.0),
        (0.0, 0.0, 1.0),
        (0.0, -0.1, 1.0),
        (math.nan, 0.2, 1.0),
        (0.0, math.inf, 1.0),
        (0.0, 0.2, math.nan),
    ):
        try:
            compiler.compile_timing(VocalPhonemeTiming("singer", "AH", start, duration, intensity))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid phoneme timing/intensity must be rejected")


def test_vocal_export_suppresses_silent_open_mouths_independently() -> None:
    compiler = BandVocalFaceExportCompiler()
    effects = compiler.compile_many((
        VocalPhonemeTiming("singer", "AH", 0.0, 0.2, 0.0),
        VocalPhonemeTiming("female_singer", "OH", 0.1, 0.3, 0.8),
        VocalPhonemeTiming("singer", "REST", 0.2, 0.1, 0.0),
    ))
    assert [(effect.performer, effect.phoneme) for effect in effects] == [
        ("female_singer", "OH"), ("singer", "REST")
    ]
