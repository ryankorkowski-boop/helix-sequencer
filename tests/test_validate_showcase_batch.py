"""Regression tests for the six-pilot batch quality gate."""
import importlib.util
import json
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "validate_showcase_batch.py"
spec = importlib.util.spec_from_file_location("validate_showcase_batch", MODULE)
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def pilots():
    return [
        {"id": f"pilot-{i}", "video": f"pilot-{i}.mp4",
         "audio_source": "song.wav", "excerpt_start_seconds": 10,
         "excerpt_duration_seconds": 35, "layout": "snowman-band"}
        for i in range(6)
    ]


def write_manifest(tmp_path, items):
    path = tmp_path / "pilots.json"
    path.write_text(json.dumps({"pilots": items}), encoding="utf-8")
    return path


def test_requires_exactly_six_pilots(tmp_path):
    with pytest.raises(ValueError, match="exactly six"):
        batch.validate_manifest(write_manifest(tmp_path, pilots()[:5]))


def test_rejects_duplicate_pilot_ids(tmp_path):
    items = pilots()
    items[1]["id"] = items[0]["id"]
    with pytest.raises(ValueError, match="distinct"):
        batch.validate_manifest(write_manifest(tmp_path, items))


def test_missing_video_and_source_fail(tmp_path):
    result = batch.validate_manifest(write_manifest(tmp_path, pilots()))
    assert not result["passed"]
    assert len(result["results"]) == 6
    assert all(not item["passed"] for item in result["results"])
    assert "Source audio file missing" in result["results"][0]["errors"]


def test_missing_required_field_fails(tmp_path):
    items = pilots()
    del items[0]["layout"]
    result = batch.validate_manifest(write_manifest(tmp_path, items))
    assert not result["passed"]
    assert "Missing fields: layout" in result["results"][0]["errors"]


def test_bad_excerpt_fails(tmp_path):
    items = pilots()
    items[0]["excerpt_duration_seconds"] = 10
    result = batch.validate_manifest(write_manifest(tmp_path, items))
    assert not result["passed"]
    assert any("30-42" in error for error in result["results"][0]["errors"])
