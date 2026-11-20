import pytest
from helix_intent.placement_planner import PlacementCandidate, plan_prop_effect_intents
from helix_intent.visual_intent import VisualIntent

@pytest.mark.parametrize("role", ["hero", "tree", "matrix", "travel", "arch"])
@pytest.mark.parametrize("kind,expected", [("transition","directional_sweep"), ("trail","melody_trail")])
def test_motion_capable_roles(role, kind, expected):
    intent = VisualIntent("motion", 0, 2, kind, "phrase", "left_to_right_sweep", [role], "medium", "verse", "default", "controlled", "attack_decay", "per_model", 0.9)
    placements, report = plan_prop_effect_intents([intent], [PlacementCandidate("Prop", role)])
    assert report.placement_count == 1
    assert placements[0].effect_family == expected

@pytest.mark.parametrize("role,expected", [("face","lyric_pulse"), ("performer","character_hit"), ("outline","outline_pulse"), ("accent","sparkle_accent")])
def test_specialist_roles_preserved(role, expected):
    intent = VisualIntent("motion", 0, 2, "transition", "phrase", "left_to_right_sweep", [role], "medium", "verse", "default", "controlled", "attack_decay", "per_model", 0.9)
    placements, report = plan_prop_effect_intents([intent], [PlacementCandidate("Prop", role)])
    assert report.placement_count == 1
    assert placements[0].effect_family == expected


def test_directional_role_priority_survives_density_cap():
    intent = VisualIntent("motion", 0, 2, "transition", "phrase", "left_to_right_sweep", ["arches", "matrix", "hero"], "sparse", "verse", "default", "controlled", "attack_decay", "per_model", 0.9)
    candidates = [PlacementCandidate("HeroA", "hero", priority=1), PlacementCandidate("HeroB", "hero", priority=2), PlacementCandidate("Arch", "arch", priority=50), PlacementCandidate("Matrix", "matrix", priority=50)]
    placements, report = plan_prop_effect_intents([intent], candidates)
    assert [p.target_prop for p in placements] == ["Arch", "Matrix"]
    assert report.capped_density_intents == ["motion"]


def test_directional_rotation_is_balanced_and_deterministic():
    intents = [VisualIntent(f"phrase-{i}", i*2, i*2+2, "transition", "phrase", "left_to_right_sweep", ["arches"], "sparse", "verse", "default", "controlled", "attack_decay", "per_model", 0.9) for i in range(3)]
    candidates = [PlacementCandidate(f"Arch{i}", "arch", priority=i) for i in range(6)]
    first, _ = plan_prop_effect_intents(intents, candidates)
    second, _ = plan_prop_effect_intents(intents, list(reversed(candidates)))
    assert [p.target_prop for p in first] == [f"Arch{i}" for i in range(6)]
    assert first == second


@pytest.mark.parametrize("second_start,second_end,expected", [(1,3,False),(2,4,True),(-1,0,True),(0,2,False),(0.5,1,False)])
def test_prop_reservation_boundaries(second_start, second_end, expected):
    from dataclasses import replace
    first = VisualIntent("a", 0, 2, "bloom", "phrase", "impact", ["hero"], "sparse", "verse", "default", "controlled", "attack_decay", "per_model", 0.9)
    second = replace(first, id="b", start_time=second_start, end_time=second_end)
    placements, report = plan_prop_effect_intents([first, second], [PlacementCandidate("Hero", "hero")])
    assert len(placements) == (2 if expected else 1)
    assert report.rejected_intents == ([] if expected else ["b"])


def test_overlapping_intents_use_free_alternatives_before_cap():
    from dataclasses import replace
    first = VisualIntent("a", 0, 2, "bloom", "phrase", "impact", ["hero"], "sparse", "verse", "default", "controlled", "attack_decay", "per_model", 0.9)
    second = replace(first, id="b", start_time=1, end_time=3)
    candidates = [PlacementCandidate(f"Hero{i}", "hero", priority=i) for i in range(4)]
    placements, report = plan_prop_effect_intents([first, second], candidates)
    assert [p.target_prop for p in placements] == ["Hero0", "Hero1", "Hero2", "Hero3"]
    assert report.rejected_intents == []


def test_interval_index_matches_linear_reference():
    from bisect import insort
    from random import Random
    from helix_intent.placement_planner import _interval_available
    rng = Random(20261120)
    intervals = []
    for _ in range(4000):
        start = rng.randrange(0, 10000)
        end = start + rng.randrange(1, 100)
        expected = not any(start < b and a < end for a, b in intervals)
        assert _interval_available(intervals, start, end) == expected
        if expected:
            insort(intervals, (start, end))
