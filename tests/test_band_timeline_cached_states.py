from core.band_intent_adapter import BandExecutionEvent
from core.band_performance_timeline import BandPerformanceTimelineCompiler
from core.choreography_intent import IntentLayerRole, MotionVocabulary
from models.helixville4_performer_runtime import DRUMMER


def _event(state="snare_hit"):
    return BandExecutionEvent(
        intent_id="test", intent_source="test", performer="drummer",
        performer_state=state, motion=MotionVocabulary.IMPACT,
        layer_role=IntentLayerRole.EVENT, start=1.0, duration=0.2,
        intensity=0.8, stage_region="front", instrument_emphasis="drums",
    )


def test_cached_state_lookup_preserves_approved_drummer_state():
    compiler = BandPerformanceTimelineCompiler((DRUMMER,))
    first = compiler.compile_event(_event())
    second = compiler.compile_event(_event())
    assert first == second
    assert first.state == "snare_hit"
    assert first.submodels == next(
        state.primary_submodels for state in DRUMMER.states if state.name == "snare_hit"
    )


def test_missing_runtime_states_fail_explicitly():
    from dataclasses import replace
    import pytest

    no_states = replace(DRUMMER, states=())
    compiler = BandPerformanceTimelineCompiler((no_states,))
    with pytest.raises(ValueError, match="no approved runtime states"):
        compiler.compile_event(_event())


def test_unknown_performer_rejected():
    import pytest

    compiler = BandPerformanceTimelineCompiler((DRUMMER,))
    from dataclasses import replace
    with pytest.raises(ValueError, match="Unknown band performer"):
        compiler.compile_event(replace(_event(), performer="xylophonist"))
