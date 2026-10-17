"""Regression tests for the review-only native advertisement assembler."""
import importlib.util
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "assemble_native_ad.py"
spec = importlib.util.spec_from_file_location("assemble_native_ad", MODULE)
ad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ad)


def test_rejects_empty_manifest(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"clips": []}')
    with pytest.raises(ValueError, match="nonempty"):
        ad.assemble(manifest, tmp_path / "out.mp4")


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg unavailable")
def test_assembly_with_synthetic_fixture(tmp_path):
    source = tmp_path / "fixture.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=blue:s=320x180:r=40:d=3", "-f", "lavfi", "-i",
                    "sine=frequency=440:sample_rate=48000:duration=3",
                    "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(source)], check=True)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"clips": [
        {"file": "fixture.mp4", "start": 0, "duration": 1},
        {"file": "fixture.mp4", "start": 1, "duration": 1}]}))
    output = tmp_path / "ad.mp4"
    result = ad.assemble(manifest, output)
    assert output.is_file()
    assert result["clips"] == 2
    assert abs(ad.probe(output) - 2) < 0.15


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg unavailable")
def test_rejects_audio_free_clip(tmp_path):
    source = tmp_path / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=black:s=64x64:r=10:d=2", "-c:v", "mpeg4", str(source)], check=True)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"clips": [{"file": "silent.mp4", "duration": 1}]}))
    with pytest.raises(ValueError, match="soundtrack"):
        ad.assemble(manifest, tmp_path / "ad.mp4")

def test_rejects_changed_source_before_output_replacement(tmp_path):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"tampered source")
    output = tmp_path / "ad.mp4"
    output.write_bytes(b"existing approved video")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"clips": [
        {"file": "clip.mp4", "duration": 1, "sha256": "0" * 64}
    ]}))
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        ad.assemble(manifest, output)
    assert output.read_bytes() == b"existing approved video"


def test_rejects_malformed_source_hash(tmp_path):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"media")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"clips": [
        {"file": "clip.mp4", "duration": 1, "sha256": "not-a-hash"}
    ]}))
    with pytest.raises(ValueError, match="Invalid source SHA256"):
        ad.assemble(manifest, tmp_path / "ad.mp4")
