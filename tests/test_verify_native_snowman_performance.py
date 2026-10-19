"""Regression tests: reject false native Snowman Band showcase acceptance."""
from pathlib import Path
import hashlib
import subprocess
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


def make_video(tmp_path):
    video = tmp_path / 'native.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=black:s=32x32:r=2:d=1','-c:v','mpeg4','-y',str(video)],check=True)
    return video


def test_valid_provenance_contract(tmp_path):
    video = make_video(tmp_path)
    report = proof()
    report["video_sha256"] = hashlib.sha256(video.read_bytes()).hexdigest()
    verify(report, video)


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
    video = make_video(tmp_path)
    report = proof()
    report["video_sha256"] = hashlib.sha256(video.read_bytes()).hexdigest()
    report[field] = value
    with pytest.raises(ValueError):
        verify(report, video)


def test_rejects_missing_mp4(tmp_path):
    with pytest.raises(ValueError):
        verify(proof(), tmp_path / "missing.mp4")


def test_rejects_wrong_video_hash(tmp_path):
    video = make_video(tmp_path)
    report = proof()
    report["video_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        verify(report, video)
