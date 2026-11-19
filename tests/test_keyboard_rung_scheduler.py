from core.keyboard_rung_scheduler import schedule_keyboard_rungs
import pytest

MAPPING = {str(n): f"KEY_MIDI_{n:03d}" for n in range(21, 109)}


def test_scale_and_chord_are_independent():
    cues = [{"pitch": n, "start": (n - 60) * .1, "duration": .3}
            for n in range(60, 64)]
    result = schedule_keyboard_rungs(cues, MAPPING, duration=2)
    assert [e["pitch"] for e in result] == [60, 61, 62, 63]
    assert len({e["submodel"] for e in result}) == 4


def test_repeated_same_pitch_merges_and_clamps():
    cues = [{"pitch": 60, "start": 0, "end": .3},
            {"pitch": 60, "start": .2, "end": 3}]
    result = schedule_keyboard_rungs(cues, MAPPING, duration=1)
    assert len(result) == 1
    assert result[0]["end"] == 1


def test_bad_mapping_rejected():
    with pytest.raises(ValueError):
        schedule_keyboard_rungs([], {"21": "RUNG"}, duration=1)
