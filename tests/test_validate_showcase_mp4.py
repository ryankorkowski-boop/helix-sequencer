"""Regression tests for the showcase MP4 validation gate."""
import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "validate_showcase_mp4.py"
spec = importlib.util.spec_from_file_location("validate_showcase_mp4", MODULE)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def test_missing_video_is_failure(tmp_path):
    result = validator.validate(tmp_path / "absent.mp4")
    assert not result["passed"]
    assert "File does not exist" in result["errors"]


def test_invalid_mp4_fails_probe(tmp_path):
    fake = tmp_path / "invalid.mp4"
    fake.write_bytes(b"not a movie")
    result = validator.validate(fake)
    assert not result["passed"]
    assert result["errors"]


def test_valid_video_when_ffmpeg_available(tmp_path):
    import shutil
    import subprocess
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        import pytest
        pytest.skip("FFmpeg tools unavailable")
    video = tmp_path / "sample.mp4"
    command = ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi",
               "-i", "color=c=blue:s=320x180:r=30:d=2",
               "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-shortest", str(video)]
    subprocess.run(command, check=True)
    result = validator.validate(video, minimum=1.5, maximum=2.5)
    assert result["passed"], result["errors"]
    assert result["video"]["codec_name"] == "h264"
    assert result["audio"]["channels"] == 2
