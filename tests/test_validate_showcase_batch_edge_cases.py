"""Security and data-quality regressions for showcase manifest validation."""
import importlib.util
import json
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "validate_showcase_batch.py"
spec = importlib.util.spec_from_file_location("showcase_batch_security", MODULE)
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def _pilots():
    return [{"id": f"pilot-{i}", "video": f"v{i}.mp4",
             "audio_source": "song.mp3", "excerpt_start_seconds": 5,
             "excerpt_duration_seconds": 35, "layout": "snowman-band"}
            for i in range(6)]


def _check(tmp_path, pilots):
    manifest = tmp_path / "pilots.json"
    manifest.write_text(json.dumps({"pilots": pilots}), encoding="utf-8")
    return batch.validate_manifest(manifest)


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity", True, None, "oops"])
def test_reject_nonfinite_or_invalid_excerpt(tmp_path, bad):
    pilots = _pilots()
    pilots[0]["excerpt_duration_seconds"] = bad
    result = _check(tmp_path, pilots)
    assert not result["passed"]
    assert not result["results"][0]["passed"]


@pytest.mark.parametrize("path", ["../elsewhere.mp4", "/tmp/elsewhere.mp4", "nested/../../elsewhere.mp4"])
def test_reject_escaping_video_path(tmp_path, path):
    pilots = _pilots()
    pilots[0]["video"] = path
    result = _check(tmp_path, pilots)
    assert any("manifest directory" in e for e in result["results"][0]["errors"])


def test_reject_nonobject_pilot(tmp_path):
    manifest = tmp_path / "pilots.json"
    manifest.write_text(json.dumps({"pilots": [None] * 6}), encoding="utf-8")
    with pytest.raises(ValueError, match="object"):
        batch.validate_manifest(manifest)


def test_unchecked_video_cannot_pass(tmp_path, monkeypatch):
    pilots = _pilots()
    (tmp_path / "song.mp3").write_bytes(b"not actual audio")
    monkeypatch.setattr(batch._validator, "validate",
                        lambda _: {"passed": False, "errors": []})
    result = _check(tmp_path, pilots)
    assert not result["passed"]
    assert "Video validation did not pass" in result["results"][0]["errors"]
