from animation.drummer_motion import build_drummer_motion
from audio.drum_classification import DrumEvent


def test_alternating_hands_across_slow_and_fast_strikes():
    events = [DrumEvent(t, .8, .9, {}, None, kind)
              for kind in ("snare", "cymbal") for t in (0.1, 0.2, 1.4, 2.8)]
    motions = build_drummer_motion(events)
    for kind in ("snare", "cymbal"):
        hits = [m for m in motions if m["drum_type"] == kind]
        assert [m["hand"] for m in hits] == ["L", "R", "L", "R"]
        if kind == "cymbal":
            assert [m["component"].rsplit("_", 1)[-1] for m in hits] == ["LEFT", "RIGHT", "LEFT", "RIGHT"]
    assert motions == build_drummer_motion(events)


def test_export_mapping_preserves_hand_assignment():
    from mapping.drum_mapper import map_events_to_drummer_components
    events = [DrumEvent(t, .8, .9, {}, None, kind)
              for kind in ("snare", "cymbal") for t in (.1, .8, 1.6, 2.4)]
    mapped = map_events_to_drummer_components(events)
    for kind in ("snare", "cymbal"):
        assert [m["hand"] for m in mapped if m["drum_type"] == kind] == ["L", "R", "L", "R"]


def test_interleaved_instrument_candidates_cluster_independently():
    from core.drummer_v3_analysis import Candidate, DrumType, _cluster_candidates
    candidates = [
        Candidate(10, .10, DrumType.SNARE, .8, "snare_a"),
        Candidate(11, .11, DrumType.KICK, .8, "kick"),
        Candidate(12, .12, DrumType.SNARE, .8, "snare_b"),
    ]
    clusters = _cluster_candidates(candidates, .045)
    assert [[c.source for c in cluster] for cluster in clusters] == [["snare_a", "snare_b"], ["kick"]]


def test_reactive_member_keeps_simultaneous_motion_instrument_identity():
    from models.working_drummer import build_reactive_drummer_member
    payload = build_reactive_drummer_member(kicks=[1000], snares=[1000], hats=[1000], cymbals=[1000])
    cues = payload["reactive_cues"]
    assert cues
    assert all(cue["kind"] == cue["motion"]["drum_type"] for cue in cues)
    assert all(cue["kind"] == cue["visual_effect"]["drum_type"] for cue in cues)


def test_scheduler_deduplicates_interleaved_same_instrument():
    from mapping.drum_mapper import build_streams_from_legacy, flatten_drum_streams, schedule_drum_events
    events = flatten_drum_streams(build_streams_from_legacy([1010], [1000, 1020], [], []))
    scheduled = schedule_drum_events(events)
    assert sorted(event.drum_type for event in scheduled) == ["kick", "snare"]


def test_scheduler_preserves_three_explicit_toms():
    from audio.drum_classification import DrumEvent
    from mapping.drum_mapper import schedule_drum_events, tom_class_for_event
    events = [DrumEvent(timestamp=1.0, velocity=.8, confidence=.9, frequency_band_info={"tom_class": label}, cluster_id=i, drum_type="tom", source="test") for i, label in enumerate(("high", "mid", "floor"))]
    assert {tom_class_for_event(e) for e in schedule_drum_events(events)} == {"high", "mid", "floor"}


def test_explicit_ride_has_independent_target_and_effect():
    from audio.drum_classification import DrumEvent, empty_drum_streams
    from mapping.drum_mapper import resolve_drum_streams
    from effects.drum_effects import build_drum_effect_cues
    streams = empty_drum_streams()
    streams["ride_events"].append(DrumEvent(1., .8, .9, {}, 1, "ride", "explicit_test"))
    result = resolve_drum_streams(streams)
    assert result["drummer_component_events"][0]["component"] == "HX_SNOWMAN_DRUMMER_RIDE"
    assert build_drum_effect_cues(result["events"])[0]["effect"] == "ride_ping"


def test_distinct_toms_preserve_full_strike_velocity():
    from mapping.drum_mapper import schedule_drum_events
    events = [DrumEvent(1.0, .8, .9, {"tom_class": label}, i, "tom") for i, label in enumerate(("high", "mid", "floor"))]
    result = schedule_drum_events(events)
    assert len(result) == 3
    assert all(e.velocity == .8 for e in result)


def test_bounded_scheduler_preserves_priority_and_window_boundary():
    from mapping.drum_mapper import schedule_drum_events, DrumMappingConfig
    events = [DrumEvent(t, .8, .9, {}, i, kind) for i, (t, kind) in enumerate([(1., "hihat"), (1.07, "kick"), (1.141, "snare")])]
    result = schedule_drum_events(events, DrumMappingConfig(max_hits_per_window=1))
    assert [e.drum_type for e in result] == ["kick", "snare"]
