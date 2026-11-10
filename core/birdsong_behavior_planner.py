from __future__ import annotations

from dataclasses import dataclass

from core.birdsong_effect_scoring import EffectCandidate, EffectScore, rank_effects
from core.birdsong_feature_state import FeatureState
from core.birdsong_motion import MotionPulse, create_motion_pulse
from core.birdsong_phrase_engine import Phrase


DEFAULT_EFFECT_CANDIDATES: tuple[EffectCandidate, ...] = (
    EffectCandidate("Bars", energy_preference=0.55, spatial_preference="horizontal", motif_affinity=("wave_sweep", "pulse_cascade"), novelty_bias=0.65),
    EffectCandidate("Spirals", energy_preference=0.70, spatial_preference="center_out", motif_affinity=("spiral", "orbit"), novelty_bias=0.75),
    EffectCandidate("Twinkle", energy_preference=0.45, spatial_preference="vertical", motif_affinity=("sparkle_field",), novelty_bias=0.85),
    EffectCandidate("Ramp", energy_preference=0.80, spatial_preference="any", motif_affinity=("wave_sweep", "pulse_cascade"), novelty_bias=0.55),
    EffectCandidate("Morph", energy_preference=0.65, spatial_preference="any", motif_affinity=("spiral", "orbit", "wave_sweep"), novelty_bias=0.70),
)


@dataclass(frozen=True)
class EffectIntent:
    effect_name: str
    motif: str
    direction: str
    start_time: float
    duration: float
    strength: float
    score: float
    score_detail: EffectScore

    @property
    def end_time(self) -> float:
        return round(self.start_time + self.duration, 6)


def intent_duration(phrase: Phrase, pulse: MotionPulse) -> float:
    span = 0.5 + pulse.strength * 1.5
    return round(max(0.25, min(phrase.duration, span)), 6)


def plan_effect_intent(
    *,
    state: FeatureState,
    phrase: Phrase,
    time: float,
    pulse: MotionPulse | None = None,
    candidates: tuple[EffectCandidate, ...] = DEFAULT_EFFECT_CANDIDATES,
    recent_effects: tuple[str, ...] = (),
    previous_effect: str | None = None,
) -> EffectIntent | None:
    active_pulse = pulse if pulse is not None else create_motion_pulse(state, phrase)
    if active_pulse is None or not active_pulse.active:
        return None

    ranked = rank_effects(
        candidates,
        state=state,
        phrase=phrase,
        pulse=active_pulse,
        recent_effects=recent_effects,
        previous_effect=previous_effect,
    )
    if not ranked:
        return None

    best = ranked[0]
    return EffectIntent(
        effect_name=best.effect.name,
        motif=phrase.motif,
        direction=phrase.direction,
        start_time=round(float(time), 6),
        duration=intent_duration(phrase, active_pulse),
        strength=active_pulse.strength,
        score=best.score,
        score_detail=best,
    )


def plan_effect_intents_for_pulses(
    *,
    state: FeatureState,
    phrase: Phrase,
    time: float,
    pulses: tuple[MotionPulse, ...],
    candidates: tuple[EffectCandidate, ...] = DEFAULT_EFFECT_CANDIDATES,
    recent_effects: tuple[str, ...] = (),
    previous_effect: str | None = None,
) -> tuple[EffectIntent, ...]:
    intents: list[EffectIntent] = []
    for pulse in pulses:
        intent = plan_effect_intent(
            state=state,
            phrase=phrase,
            time=time,
            pulse=pulse,
            candidates=candidates,
            recent_effects=recent_effects,
            previous_effect=previous_effect,
        )
        if intent is not None:
            intents.append(intent)
    return tuple(sorted(intents, key=lambda item: (item.start_time, item.effect_name, item.score)))
