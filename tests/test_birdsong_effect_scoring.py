from __future__ import annotations

from core.birdsong_effect_scoring import (
    EffectCandidate,
    energy_match,
    novelty_score,
    rank_effects,
    score_effect,
    spatial_fit,
)
from core.birdsong_feature_state import FeatureState
from core.birdsong_motion import MotionPulse
from core.birdsong_phrase_engine import Phrase


def _state(energy: float = 0.8) -> FeatureState:
    state = FeatureState(smoothing_alpha=1.0)
    state.update({"energy": energy, "onset": 0.2, "bands": (0.2, 0.6, 0.2)})
    return state


def _phrase(motif: str = "wave_sweep", direction: str = "left_to_right") -> Phrase:
    return Phrase(start_time=0.0, duration=4.0, motif=motif, direction=direction, energy_anchor=0.8)


def _candidate(
    name: str = "Bars",
    *,
    energy_preference: float = 0.8,
    spatial_preference: str = "left_to_right",
    motif_affinity: tuple[str, ...] = ("wave_sweep",),
    novelty_bias: float = 0.75,
) -> EffectCandidate:
    return EffectCandidate(
        name=name,
        energy_preference=energy_preference,
        spatial_preference=spatial_preference,
        motif_affinity=motif_affinity,
        novelty_bias=novelty_bias,
    )


def test_energy_match_prefers_candidate_near_current_energy() -> None:
    state = _state(0.8)

    close = energy_match(_candidate(energy_preference=0.75), state)
    far = energy_match(_candidate(energy_preference=0.1), state)

    assert close > far
    assert close == 0.95


def test_spatial_fit_uses_phrase_direction_and_pulse_orientation() -> None:
    phrase = _phrase(direction="left_to_right")
    horizontal = MotionPulse(position=(0, 0, 0), step=(1, 0, 0), strength=0.8)
    vertical = MotionPulse(position=(0, 0, 0), step=(0, 1, 0), strength=0.8)

    assert spatial_fit(_candidate(spatial_preference="left_to_right"), phrase) == 1.0
    assert spatial_fit(_candidate(spatial_preference="any"), phrase) == 0.75
    assert spatial_fit(_candidate(spatial_preference="horizontal"), phrase, horizontal) == 0.8
    assert spatial_fit(_candidate(spatial_preference="vertical"), phrase, vertical) == 0.8
    assert spatial_fit(_candidate(spatial_preference="top_down"), phrase) == 0.35


def test_novelty_score_penalizes_recent_repetition() -> None:
    candidate = _candidate(name="Twinkle", novelty_bias=0.8)

    assert novelty_score(candidate, recent_effects=()) == 0.8
    assert novelty_score(candidate, recent_effects=("Twinkle",)) == 0.28


def test_score_effect_uses_issue_two_weighting_formula() -> None:
    state = _state(0.8)
    phrase = _phrase()
    candidate = _candidate(novelty_bias=0.75)

    scored = score_effect(candidate, state=state, phrase=phrase)

    expected = round(
        scored.energy_match * 0.35
        + scored.spatial_fit * 0.25
        + scored.novelty * 0.20
        + scored.continuity * 0.20,
        6,
    )
    assert scored.score == expected
    assert scored.energy_match == 1.0
    assert scored.spatial_fit == 1.0
    assert scored.continuity == 1.0


def test_rank_effects_is_deterministic_and_prefers_best_context_fit() -> None:
    candidates = (
        _candidate("Weak", energy_preference=0.1, spatial_preference="top_down", motif_affinity=("sparkle_field",), novelty_bias=0.4),
        _candidate("Strong", energy_preference=0.8, spatial_preference="left_to_right", motif_affinity=("wave_sweep",), novelty_bias=0.8),
        _candidate("Repeated", energy_preference=0.8, spatial_preference="left_to_right", motif_affinity=("wave_sweep",), novelty_bias=0.8),
    )

    first = rank_effects(
        candidates,
        state=_state(0.8),
        phrase=_phrase(),
        recent_effects=("Repeated",),
    )
    second = rank_effects(
        candidates,
        state=_state(0.8),
        phrase=_phrase(),
        recent_effects=("Repeated",),
    )

    assert first == second
    assert first[0].effect.name == "Strong"
    assert first[-1].effect.name == "Weak"
