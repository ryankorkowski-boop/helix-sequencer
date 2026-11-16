"""Approved nine-cue performance contract for the canonical eight-component kit."""
from animation.drummer_motion import build_drummer_motion
from audio.drum_classification import DrumEvent
from mapping.drum_mapper import map_events_to_drummer_components


def _event(kind, ms):
    return DrumEvent(timestamp=ms / 1000, velocity=0.8, confidence=0.9,
                     frequency_band_info={}, cluster_id=None, drum_type=kind)


def test_snare_alternates_sticks_even_when_hits_are_far_apart():
    events = [_event("snare", ms) for ms in (100, 700, 1400, 2300)]
    motions = build_drummer_motion(events)
    assert [motion["hand"] for motion in motions] == ["L", "R", "L", "R"]
    assert len({motion["component"] for motion in motions}) == 1
    assert motions[0]["component"] == "HX_SNOWMAN_DRUMMER_SNARE"


def test_cymbals_alternate_physical_targets_and_hands():
    events = [_event("cymbal", ms) for ms in (100, 800, 1500, 2200)]
    mapped = map_events_to_drummer_components(events)
    motions = build_drummer_motion(events)
    assert [item["component"] for item in mapped] == [
        "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT",
        "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT",
    ]
    assert [motion["hand"] for motion in motions] == ["L", "R", "L", "R"]
    assert [motion["component"] for motion in motions] == [item["component"] for item in mapped]


def test_nine_performance_cues_preserve_eight_physical_targets():
    events = [_event("kick", 100), _event("snare", 200), _event("snare", 300),
              _event("hihat", 400), _event("tom", 500), _event("tom", 600),
              _event("tom", 700), _event("cymbal", 800), _event("cymbal", 900)]
    motions = build_drummer_motion(events)
    assert len(motions) == 9
    assert len({motion["component"] for motion in motions}) == 8
    assert [m["tom_class"] for m in motions if m["drum_type"] == "tom"] == ["high", "mid", "floor"]
