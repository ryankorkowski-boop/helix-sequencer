from .audio_to_events import events_from_hits



def test_audio_events_create_preview_timeline():
    timeline = events_from_hits([
        {"time": 0.5, "instrument": "kick", "strength": 0.9},
        {"time": 1.0, "instrument": "snare", "strength": 0.6},
    ])

    assert len(timeline.events) == 2
    assert timeline.events[0].instrument == "kick"
    assert timeline.events[0].strength == 0.9
