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
