from __future__ import annotations

from core.birdsong_behavior_planner import (
    DEFAULT_EFFECT_CANDIDATES,
    intent_duration,
    plan_effect_intent,
    plan_effect_intents_for_pulses,
)
from core.birdsong_feature_state import FeatureState
from core.birdsong_motion import MotionPulse
from core.birdsong_phrase_engine import Phrase


def _state(*, energy: float = 0.8, onset: float = 0.2, bands=(0.2, 0.6, 0.2)) -> FeatureState:
    state = FeatureState(smoothing_alpha=1.0)
    state.update({"energy": energy, "onset": onset, "bands": bands})
    return state


def _phrase(*, motif: str = "wave_sweep", direction: str = "left_to_right") -> Phrase:
    return Phrase(start_time=0.0, duration=4.0, motif=motif, direction=direction, energy_anchor=0.8)


def test_plan_effect_intent_returns_none_for_quiet_state_without_pulse() -> None:
    intent = plan_effect_intent(
        state=_state(energy=0.1, onset=0.1),
        phrase=_phrase(),
        time=1.0,
    )

    assert intent is None


def test_plan_effect_intent_uses_ranked_effect_scoring() -> None:
    intent = plan_effect_intent(
        state=_state(energy=0.8),
        phrase=_phrase(motif="wave_sweep", direction="left_to_right"),
        time=2.5,
    )

    assert intent is not None
    assert intent.effect_name in {candidate.name for candidate in DEFAULT_EFFECT_CANDIDATES}
    assert intent.motif == "wave_sweep"
    assert intent.direction == "left_to_right"
    assert intent.start_time == 2.5
    assert intent.end_time == round(intent.start_time + intent.duration, 6)
    assert intent.score == intent.score_detail.score


def test_intent_duration_is_bounded_by_phrase_duration() -> None:
    phrase = _phrase()
    weak = MotionPulse(position=(0, 0, 0), step=(1, 0, 0), strength=0.0)
    strong = MotionPulse(position=(0, 0, 0), step=(1, 0, 0), strength=1.0)
    short_phrase = Phrase(start_time=0.0, duration=1.0, motif="wave_sweep", direction="left_to_right", energy_anchor=1.0)

    assert intent_duration(phrase, weak) == 0.5
    assert intent_duration(phrase, strong) == 2.0
    assert intent_duration(short_phrase, strong) == 1.0


def test_plan_effect_intent_penalizes_recent_repetition() -> None:
    fresh = plan_effect_intent(
        state=_state(energy=0.8),
        phrase=_phrase(),
        time=0.0,
        recent_effects=(),
    )
    repeated = plan_effect_intent(
        state=_state(energy=0.8),
        phrase=_phrase(),
        time=0.0,
        recent_effects=(fresh.effect_name if fresh else "",),
    )

    assert fresh is not None
    assert repeated is not None
    assert repeated.score <= fresh.score


def test_plan_effect_intents_for_pulses_is_deterministic_and_ordered() -> None:
    pulses = (
        MotionPulse(position=(0, 0, 0), step=(1, 0, 0), strength=0.8),
        MotionPulse(position=(0, 1, 0), step=(0, -1, 0), strength=0.6),
    )

    first = plan_effect_intents_for_pulses(
        state=_state(energy=0.8),
        phrase=_phrase(),
        time=3.0,
        pulses=pulses,
    )
    second = plan_effect_intents_for_pulses(
        state=_state(energy=0.8),
        phrase=_phrase(),
        time=3.0,
        pulses=pulses,
    )

    assert first == second
    assert len(first) == 2
    assert tuple(intent.effect_name for intent in first) == tuple(sorted(intent.effect_name for intent in first))
