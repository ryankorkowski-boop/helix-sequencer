import json

import pytest

from core.stage_metrics import capture_metrics, phase, profile_run, timed_stage


def test_disabled_stages_preserve_results_and_have_no_output(tmp_path, monkeypatch):
    monkeypatch.delenv("HELIX_PROFILE_OUTPUT", raising=False)
    @profile_run
    @timed_stage("test")
    def work():
        phase("phase")
        return 12
    assert work() == 12
    assert not list(tmp_path.iterdir())


def test_nested_captures_share_collector_and_record_failures(tmp_path):
    path = tmp_path / "metrics.json"
    @timed_stage("failure")
    def fail():
        raise ValueError("original")
    with pytest.raises(ValueError, match="original"):
        with capture_metrics(path) as outer:
            phase("planning")
            with capture_metrics() as inner:
                assert inner is outer
                fail()
    payload = json.loads(path.read_text())
    assert not payload["success"]
    assert payload["wall_seconds"] >= 0
    assert payload["stages"]["failure"]["calls"] == 1
    assert payload["stages"]["planning"]["calls"] == 1
    assert payload["peak_rss_bytes"] is None or payload["peak_rss_bytes"] > 0
    with capture_metrics() as fresh:
        assert fresh is not outer


def test_metrics_write_failure_does_not_lose_original_error(tmp_path):
    path = tmp_path / "file"
    path.write_text("cannot be a directory")
    with pytest.warns(RuntimeWarning, match="Could not save"):
        with pytest.raises(RuntimeError, match="original"):
            with capture_metrics(path / "metrics.json"):
                raise RuntimeError("original")
