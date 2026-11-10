from .beat_detector import normalize_beats
from .performer import performer_events



def test_performance_mapping():
    events = normalize_beats([0.5, 1.0], strength=0.8)
    actions = performer_events(events)

    assert actions[0]["action"] == "pulse"
    assert actions[0]["strength"] == 0.8
