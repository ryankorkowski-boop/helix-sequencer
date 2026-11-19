import pytest

from core.drummer_oracle_comparison import compare_drum_events


def event(kind, time):
    return {"drum_type": kind, "timestamp_ms": time}


def test_perfect_oracle_match_and_drift():
    report = compare_drum_events(
        [event("kick", 100), event("snare", 250)],
        [event("kick", 109), event("snare", 245)],
    )
    assert report["exact_within_tolerance"]
    assert report["matched"] == 2
    assert report["max_absolute_drift_ms"] == 9


def test_class_mismatch_is_not_a_match():
    report = compare_drum_events([event("kick", 100)], [event("snare", 100)])
    assert report["false_positive"] == 1
    assert report["false_negative"] == 1
    assert not report["exact_within_tolerance"]


def test_one_candidate_cannot_match_two_oracle_hits():
    report = compare_drum_events(
        [event("kick", 100), event("kick", 105)],
        [event("kick", 102)],
    )
    assert report["matched"] == 1
    assert report["false_negative"] == 1


def test_earliest_matching_preserves_maximum_match_count():
    report = compare_drum_events(
        [event("kick", 100), event("kick", 130)],
        [event("kick", 120), event("kick", 150)],
        tolerance_ms=20,
    )
    assert report["matched"] == 2


@pytest.mark.parametrize("time", [None, float("nan"), -1, True, "not a time"])
def test_invalid_timestamps_are_rejected(time):
    with pytest.raises(ValueError):
        compare_drum_events([event("kick", time)], [])


def test_no_events_does_not_invent_drift():
    report = compare_drum_events([], [])
    assert report["exact_within_tolerance"]
    assert report["mean_absolute_drift_ms"] is None


def test_file_comparator_uses_real_json_and_rejects_mismatch(tmp_path):
    import json
    from core.drummer_oracle_comparison import compare_oracle_files
    oracle = tmp_path / "approved.json"
    candidate = tmp_path / "candidate.json"
    oracle.write_text(json.dumps({"events": [event("kick", 100)]}))
    candidate.write_text(json.dumps([event("snare", 100)]))
    result = compare_oracle_files(oracle, candidate)
    assert result["false_negative"] == 1
    assert result["false_positive"] == 1


def test_file_comparator_rejects_missing_event_array(tmp_path):
    import json
    from core.drummer_oracle_comparison import compare_oracle_files
    oracle = tmp_path / "approved.json"
    candidate = tmp_path / "candidate.json"
    oracle.write_text(json.dumps({"note": "not an event list"}))
    candidate.write_text("[]")
    with pytest.raises(ValueError):
        compare_oracle_files(oracle, candidate)


def test_cli_fails_closed_on_empty_oracle(tmp_path, monkeypatch):
    import json
    import sys
    from core.drummer_oracle_comparison import main
    oracle = tmp_path / "approved.json"
    candidate = tmp_path / "candidate.json"
    oracle.write_text("[]")
    candidate.write_text(json.dumps([event("kick", 100)]))
    monkeypatch.setattr(sys, "argv", ["oracle", "--oracle", str(oracle), "--candidate", str(candidate)])
    with pytest.raises(SystemExit, match="nonempty real event streams"):
        main()
