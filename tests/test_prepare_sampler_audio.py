"""Regressions for source-bound MP4 extraction."""
import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "prepare_sampler_audio.py"
SPEC = importlib.util.spec_from_file_location("prepare_sampler_audio", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="ffmpeg tools unavailable")
def test_extract_manifest_and_no_overwrite(tmp_path):
    source = tmp_path / "sample.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=1", "-f", "lavfi", "-i",
                    "color=c=black:s=64x64:d=1", "-shortest", "-c:v", "mpeg4",
                    "-c:a", "aac", str(source)], check=True)
    folder = tmp_path / "out"
    result = MODULE.prepare(source, folder)
    assert result["status"] == "audio_extracted_only"
    assert not result["original_sampler_identity_verified"]
    assert not result["instrument_analysis_verified"]
    assert MODULE.sha256(folder / result["extracted_audio_name"]) == result["extracted_audio_sha256"]
    with pytest.raises(FileExistsError):
        MODULE.prepare(source, folder)
    assert MODULE.prepare(source, folder, overwrite=True)["source_video_sha256"] == result["source_video_sha256"]


def test_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        MODULE.prepare(tmp_path / "missing.mp4", tmp_path / "out")
