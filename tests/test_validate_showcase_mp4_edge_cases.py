"""Additional failure-mode tests for showcase video validation."""
import importlib.util
import subprocess
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "tools" / "validate_showcase_mp4.py"
spec = importlib.util.spec_from_file_location("showcase_validator_extra", MODULE)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def test_probe_timeout_is_failure(tmp_path):
    video = tmp_path / "slow.mp4"
    video.write_bytes(b"data")
    with patch.object(validator.shutil, "which", return_value="/usr/bin/tool"):
        with patch.object(validator, "run", side_effect=subprocess.TimeoutExpired("ffprobe", 30)):
            result = validator.validate(video)
    assert not result["passed"]
    assert "ffprobe timed out" in result["errors"]


def test_missing_audio_never_attempts_decode(tmp_path):
    video = tmp_path / "video-only.mp4"
    video.write_bytes(b"data")
    probe = subprocess.CompletedProcess(
        ["ffprobe"], 0,
        '{"format":{"duration":"35.0"},"streams":[{"codec_type":"video",'
        '"codec_name":"h264","width":1920,"height":1080,'
        '"avg_frame_rate":"30/1"}]}', "")
    with patch.object(validator.shutil, "which", return_value="/usr/bin/tool"):
        with patch.object(validator, "run", return_value=probe) as runner:
            result = validator.validate(video)
    assert not result["passed"]
    assert "Expected one audio stream, found 0" in result["errors"]
    assert runner.call_count == 1


def test_nonfinite_duration_is_rejected(tmp_path):
    video = tmp_path / "nan.mp4"
    video.write_bytes(b"data")
    probe = subprocess.CompletedProcess(["ffprobe"], 0,
        '{"format":{"duration":"NaN"},"streams":[]}', "")
    with patch.object(validator.shutil, "which", return_value="/usr/bin/tool"):
        with patch.object(validator, "run", return_value=probe):
            result = validator.validate(video)
    assert not result["passed"]
    assert "Invalid or missing duration metadata" in result["errors"]
