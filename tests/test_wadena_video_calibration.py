import json
from pathlib import Path


FIXTURE = Path("data/wadena_video_calibration.json")
EXPECTED_TIMES = (7.7, 31.7, 36.8, 59.9, 79.4, 97.2, 108.1, 154.4, 163.1, 218.7, 225.9)
VALID_TYPES = {"observed", "inferred", "uncertain", "not_visible"}


def _load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_is_machine_readable_and_contains_all_candidate_windows():
    data = _load()
    assert data["schema_version"] == 1
    assert data["source"]["fps"] > 0
    windows = data["candidate_windows"]
    assert len(windows) == len(EXPECTED_TIMES)
    actual = tuple(round((w["time_window"][0] + w["time_window"][1]) / 2, 1) for w in windows)
    assert actual == EXPECTED_TIMES


def test_fixture_has_explicit_evidence_semantics_and_safe_unknowns():
    data = _load()
    for window in data["candidate_windows"]:
        assert window["observation_type"] in VALID_TYPES
        assert window["direction"] in {
            "unknown", "left_to_right", "right_to_left", "center_out", "out_to_center",
            "bottom_up", "top_down", "impact_propagation"
        }
        assert 0.0 <= window["confidence"] <= 1.0
        assert 0.0 <= window["magnitude"] <= 1.0
        assert window["frame_range"][0] <= window["frame_range"][1]
        assert window["time_window"][0] <= window["time_window"][1]


def test_end_of_recording_window_is_not_visible_not_a_choreography_event():
    data = _load()
    end_window = data["candidate_windows"][-1]
    assert end_window["observation_type"] == "not_visible"
    assert "recorder_ui" in end_window["roles"]
