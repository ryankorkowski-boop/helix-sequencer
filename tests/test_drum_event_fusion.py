from audio.drum_event_fusion import DrumFusionConfig, fuse_drum_events
from audio.musical_event_model import MusicalEvent


def event(t, kind, confidence, source, strength=0.8):
    return MusicalEvent(
        time_ms=t,
        kind=f"{kind}_{source}",
        confidence=confidence,
        strength=strength,
        source=source,
        instrument=kind,
    )


def test_same_hit_from_two_sources_fuses_once():
    events = [
        MusicalEvent(1000, "drum_kick", 0.8, 0.8, "direct", instrument="kick"),
        MusicalEvent(1018, "stem_drum_kick", 0.7, 0.6, "stem", instrument="kick"),
    ]
    fused, diag = fuse_drum_events(events)
    assert len(fused) == 1
    assert fused[0].kind == "drum_kick"
    assert fused[0].source == "helix.drum_fusion"
    assert fused[0].confidence > 0.8
    assert fused[0].metadata["sources"] == ["direct", "stem"]
    assert diag["duplicates_suppressed"] == 1
    assert diag["multi_source_events"] == 1


def test_distinct_hits_and_types_do_not_merge():
    events = [
        MusicalEvent(1000, "drum_kick", 0.8, 0.8, "direct", instrument="kick"),
        MusicalEvent(1120, "drum_kick", 0.9, 0.9, "direct", instrument="kick"),
        MusicalEvent(1005, "drum_snare", 0.9, 0.9, "direct", instrument="snare"),
    ]
    fused, diag = fuse_drum_events(events, config=DrumFusionConfig(time_tolerance_ms=30))
    assert len(fused) == 3
    assert diag["duplicates_suppressed"] == 0


def test_low_confidence_events_are_suppressed():
    events = [MusicalEvent(1000, "drum_hat", 0.2, 0.4, "direct", instrument="hat")]
    fused, diag = fuse_drum_events(events)
    assert fused == []
    assert diag["input_candidates"] == 0


def test_fusion_is_deterministically_sorted():
    events = [
        MusicalEvent(1200, "drum_crash", 0.7, 0.7, "a", instrument="crash"),
        MusicalEvent(500, "drum_kick", 0.8, 0.8, "a", instrument="kick"),
    ]
    fused, _ = fuse_drum_events(events)
    assert [e.time_ms for e in fused] == [500, 1200]
