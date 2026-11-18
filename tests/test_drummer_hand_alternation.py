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
