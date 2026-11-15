"""Regression contract for owner-selected three-tom drummer references.

This is logic evidence only; approval also requires a source-matched native
xLights XSQ/FSEQ render and visual comparison with Drive Truths videos.
"""
from audio.drum_classification import DrumEvent
from mapping.drum_mapper import (
    DrumMappingConfig,
    DRUMMER_V3_MODEL,
    map_events_to_drummer_v3_poses,
    schedule_drum_events,
)


def _hit(ms: int, kind: str, tom: str | None = None, velocity: float = 0.8):
    info = {"tom_class": tom, "tom_class_confidence": 0.95} if tom else {}
    return DrumEvent(ms / 1000, velocity, 0.95, info, ms, kind, "three_tom_truth_test")


def test_independent_toms_survive_one_simultaneous_full_kit_onset():
    events = [
        _hit(10000, "kick"),
        _hit(10000, "snare"),
        _hit(10000, "hihat"),
        _hit(10000, "tom", "high"),
        _hit(10000, "tom", "mid"),
        _hit(10000, "tom", "floor"),
    ]
    schedule = schedule_drum_events(
        events, DrumMappingConfig(intro_gate_enabled=False)
    )
    poses = map_events_to_drummer_v3_poses(schedule)
    assert len(schedule) == len(poses) == 6
    assert {int(p["timestamp_ms"]) for p in poses} == {10000}
    assert {p["component"] for p in poses} == {
        DRUMMER_V3_MODEL + suffix
        for suffix in ("_KICK", "_SNARE", "_HI_HAT",
                       "_TOM_HIGH", "_TOM_MID", "_TOM_FLOOR")
    }
    assert {p["tom_class"] for p in poses if p["drum_type"] == "tom"} == {
        "high", "mid", "floor"
    }
    assert all(p["intensity"] == 0.8 for p in poses)
    assert all("TOM_4" not in p["component"] for p in poses)


def test_distinct_toms_do_not_merge_or_dim_inside_repeat_window():
    schedule = schedule_drum_events(
        [_hit(2000, "tom", "high"), _hit(2030, "tom", "mid")],
        DrumMappingConfig(intro_gate_enabled=False),
    )
    assert [(p.timestamp_ms, p.velocity) for p in schedule] == [
        (2000, 0.8), (2030, 0.8)
    ]


def test_repeated_same_tom_remains_deduplicated():
    schedule = schedule_drum_events(
        [_hit(2000, "tom", "high", 0.52), _hit(2010, "tom", "high", 0.83)],
        DrumMappingConfig(intro_gate_enabled=False),
    )
    assert len(schedule) == 1
    assert schedule[0].velocity == 0.83


def test_staggered_noisy_burst_still_respects_existing_clutter_limit():
    events = [
        _hit(1000, "kick"),
        _hit(1005, "snare"),
        _hit(1010, "tom", "high"),
        _hit(1015, "tom", "mid"),
        _hit(1020, "tom", "floor"),
        _hit(1025, "hihat"),
    ]
    schedule = schedule_drum_events(
        events, DrumMappingConfig(intro_gate_enabled=False)
    )
    assert len(schedule) <= 4


def test_unclassified_toms_still_fail_closed():
    schedule = schedule_drum_events(
        [_hit(1000, "tom"), _hit(1010, "kick")],
        DrumMappingConfig(intro_gate_enabled=False),
    )
    assert [event.drum_type for event in schedule] == ["kick"]
