from core.choreography_intent import (
    ChoreographyIntent, ChoreographyTarget, IntentLayerRole, MotionVocabulary,
)
from core.intent_graph import IntentGraph
from core.intent_arbitration_diagnostics import arbitration_diagnostics


def intent(start=0, family=ChoreographyTarget.MOTION, prop=None, role=IntentLayerRole.MOTION):
    return ChoreographyIntent(
        start=start, duration=2.0, section="chorus", event_type="phrase",
        style="test", emotional_energy=0.6, intensity=0.6,
        focal_region="center", target_families=(family,), dominant_prop=prop,
        motion_vocabulary=(MotionVocabulary.CHASE,), layer_roles=(role,),
    )


def test_overlapping_motion_same_target_reported_without_mutation():
    graph = IntentGraph([intent(), intent(start=1)])
    before = graph.to_dict()
    report = arbitration_diagnostics(graph)
    assert report["motion_conflict_count"] == 1
    assert report["mode"] == "observe_only"
    assert graph.to_dict() == before


def test_distinct_prop_targets_not_conflicts():
    graph = IntentGraph([intent(prop="arch_1"), intent(start=1, prop="tree_1")])
    assert arbitration_diagnostics(graph)["motion_conflict_count"] == 0


def test_distinct_families_and_nonmotion_roles_not_conflicts():
    graph = IntentGraph([
        intent(family=ChoreographyTarget.MATRIX),
        intent(start=1, family=ChoreographyTarget.OUTLINE),
        intent(start=1, role=IntentLayerRole.ACCENT),
    ])
    assert arbitration_diagnostics(graph)["motion_conflict_count"] == 0


def test_nonoverlapping_intents_not_conflicts():
    graph = IntentGraph([intent(), intent(start=2)])
    assert arbitration_diagnostics(graph)["motion_conflict_count"] == 0


def test_director_opt_in_defaults_off():
    from core.multi_pass_orchestration_director import MultiPassOrchestrationDirector
    assert MultiPassOrchestrationDirector().audit_motion_conflicts is False
    assert MultiPassOrchestrationDirector(audit_motion_conflicts=True).audit_motion_conflicts is True


def test_audit_flag_is_removed_before_engine_invocation():
    from core.sequence_builder import _clean_engine_args
    assert _clean_engine_args(["--audit-motion-conflicts", "--audio", "song.wav"]) == [
        "--audio", "song.wav",
    ]
