from __future__ import annotations

from dataclasses import dataclass

from core.birdsong_feature_state import FeatureState, clamp01
from core.birdsong_motion import MotionPulse
from core.birdsong_phrase_engine import Phrase


@dataclass(frozen=True)
class EffectCandidate:
    name: str
    energy_preference: float
    spatial_preference: str
    motif_affinity: tuple[str, ...]
    novelty_bias: float = 0.5


@dataclass(frozen=True)
class EffectScore:
    effect: EffectCandidate
    score: float
    energy_match: float
    spatial_fit: float
    novelty: float
    continuity: float


def energy_match(candidate: EffectCandidate, state: FeatureState, pulse: MotionPulse | None = None) -> float:
    target = pulse.strength if pulse is not None else state.energy_smooth
    return round(1.0 - min(1.0, abs(clamp01(candidate.energy_preference) - clamp01(target))), 6)


def spatial_fit(candidate: EffectCandidate, phrase: Phrase, pulse: MotionPulse | None = None) -> float:
    if candidate.spatial_preference == phrase.direction:
        return 1.0
    if candidate.spatial_preference == "any":
        return 0.75
    if pulse is not None and candidate.spatial_preference in {"horizontal", "vertical"}:
        sx, sy, _ = pulse.step
        if candidate.spatial_preference == "horizontal" and abs(sx) >= abs(sy):
            return 0.8
        if candidate.spatial_preference == "vertical" and abs(sy) > abs(sx):
            return 0.8
    return 0.35


def novelty_score(candidate: EffectCandidate, recent_effects: tuple[str, ...] = ()) -> float:
    base = clamp01(candidate.novelty_bias)
    if candidate.name in recent_effects:
        return round(base * 0.35, 6)
    return round(base, 6)


def continuity_score(candidate: EffectCandidate, phrase: Phrase, previous_effect: str | None = None) -> float:
    if candidate.name == previous_effect:
        return 0.7
    if phrase.motif in candidate.motif_affinity:
        return 1.0
    return 0.45


def score_effect(
    candidate: EffectCandidate,
    *,
    state: FeatureState,
    phrase: Phrase,
    pulse: MotionPulse | None = None,
    recent_effects: tuple[str, ...] = (),
    previous_effect: str | None = None,
) -> EffectScore:
    em = energy_match(candidate, state, pulse)
    sf = spatial_fit(candidate, phrase, pulse)
    nv = novelty_score(candidate, recent_effects)
    ct = continuity_score(candidate, phrase, previous_effect)
    total = round(em * 0.35 + sf * 0.25 + nv * 0.20 + ct * 0.20, 6)
    return EffectScore(
        effect=candidate,
        score=total,
        energy_match=em,
        spatial_fit=sf,
        novelty=nv,
        continuity=ct,
    )


def rank_effects(
    candidates: tuple[EffectCandidate, ...],
    *,
    state: FeatureState,
    phrase: Phrase,
    pulse: MotionPulse | None = None,
    recent_effects: tuple[str, ...] = (),
    previous_effect: str | None = None,
) -> tuple[EffectScore, ...]:
    scores = tuple(
        score_effect(
            candidate,
            state=state,
            phrase=phrase,
            pulse=pulse,
            recent_effects=recent_effects,
            previous_effect=previous_effect,
        )
        for candidate in candidates
    )
    return tuple(sorted(scores, key=lambda item: (item.score, item.effect.name), reverse=True))
