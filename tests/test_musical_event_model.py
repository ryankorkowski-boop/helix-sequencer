from audio.musical_event_model import MusicalEvent, MusicalEventMap


def test_musical_event_clamps_serialized_confidence_and_strength():
    event = MusicalEvent(time_ms=100, kind="drum_snare", confidence=2.0, strength=-1.0)
    payload = event.to_dict()
    assert payload["confidence"] == 1.0
    assert payload["strength"] == 0.0


def test_event_map_sorts_deterministically():
    event_map = MusicalEventMap(duration_ms=1000)
    event_map.add(MusicalEvent(300, "drum_kick", 0.8))
    event_map.add(MusicalEvent(100, "drum_snare", 0.9))
    event_map.add(MusicalEvent(100, "drum_kick", 0.7))
    event_map.sort()
    assert [(e.time_ms, e.kind) for e in event_map.events] == [
        (100, "drum_kick"),
        (100, "drum_snare"),
        (300, "drum_kick"),
    ]


def test_high_confidence_filter():
    event_map = MusicalEventMap(duration_ms=1000, events=[
        MusicalEvent(100, "a", 0.9),
        MusicalEvent(200, "b", 0.4),
    ])
    assert [e.kind for e in event_map.high_confidence(0.7)] == ["a"]
