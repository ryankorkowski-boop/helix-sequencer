"""Regression tests: reject false native Snowman Band showcase acceptance."""
from pathlib import Path
import pytest
from tools.verify_native_snowman_performance import verify, ROLES


def proof():
    return dict(layout_source="native_HX_SNOW", roles=list(ROLES),
                model_names=["HX_SNOW_" + r.upper() for r in ROLES],
                source_audio_sha256="a" * 64,
                source_analysis_provenance="source-bound verified analysis",
                musical_accuracy_independently_verified=True,
                full_decode_passed=True, audio_synchronized=True,
                full_song_showcase_complete=True)


def test_valid_provenance_contract(tmp_path):
    video = tmp_path / "native.mp4"
    video.write_bytes(b"not-a-real-video")  # This unit test checks metadata; decoder verifies separately.
    verify(proof(), video)


@pytest.mark.parametrize("field,value", [
    ("layout_source", "legacy_256"),
    ("roles", ["drummer"]),
    ("model_names", ["HX_SNOW_DRUMMER"]),
    ("source_audio_sha256", ""),
    ("source_analysis_provenance", ""),
    ("musical_accuracy_independently_verified", False),
    ("full_decode_passed", False),
    ("audio_synchronized", False),
    ("full_song_showcase_complete", False),
    ("diagnostic", True),
    ("authored_fixture", True),
])
def test_rejects_unverified_showcase(tmp_path, field, value):
    video = tmp_path / "native.mp4"
    video.write_bytes(b"stub")
    report = proof()
    report[field] = value
    with pytest.raises(ValueError):
        verify(report, video)


def test_rejects_missing_mp4(tmp_path):
    with pytest.raises(ValueError):
        verify(proof(), tmp_path / "missing.mp4")
