from audio.drum_classification import DrumEvent
from mapping.drum_performance import build_performance, stick_pose


def _event(ms: int, kind: str, velocity: float = 0.8) -> DrumEvent:
    return DrumEvent(ms / 1000, velocity, 0.9, {}, ms, kind, "test")


def test_snare_hits_alternate_hands():
    hits = build_performance([_event(100, "snare"), _event(300, "snare"), _event(500, "snare")])
    assert [h.hand for h in hits] == ["L", "R", "L"]


def test_toms_alternate_left_and_right_targets():
    hits = build_performance([_event(100, "tom"), _event(300, "tom")])
    assert [h.target for h in hits] == ["tom_left", "tom_right"]


def test_stick_reaches_hit_target_at_contact():
    hit = build_performance([_event(1000, "snare")])[0]
    pose = stick_pose(hit, 1000, "L")
    assert abs(pose.x - 0.43) < 0.01
    assert abs(pose.y - 0.58) < 0.01


def test_kick_has_no_stick_assignment():
    hit = build_performance([_event(100, "kick")])[0]
    assert hit.hand is None
    assert hit.target == "kick"
