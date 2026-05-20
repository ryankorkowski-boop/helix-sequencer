from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class BirdsongQualityReport:
    score: float
    musicality: float
    spatial_coherence: float
    layering: float
    novelty: float
    emotion: float
    intent_count: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "score": self.score,
            "musicality": self.musicality,
            "spatial_coherence": self.spatial_coherence,
            "layering": self.layering,
            "novelty": self.novelty,
            "emotion": self.emotion,
            "intent_count": self.intent_count,
        }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _records(manifest: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw = manifest.get("intents", [])
    if not isinstance(raw, Sequence):
        return []
    return [item for item in raw if isinstance(item, Mapping)]


def _float(record: Mapping[str, object], key: str, default: float = 0.0) -> float:
    try:
        return float(record.get(key, default))
    except (TypeError, ValueError):
        return default


def score_musicality(intents: Sequence[Mapping[str, object]]) -> float:
    if not intents:
        return 0.0
    scores = [_float(intent, "score") for intent in intents]
    positive_duration = sum(1 for intent in intents if _float(intent, "duration") > 0)
    avg_score = sum(scores) / len(scores)
    duration_health = positive_duration / len(intents)
    return round(_clamp01(avg_score * 0.75 + duration_health * 0.25), 6)


def score_spatial_coherence(intents: Sequence[Mapping[str, object]]) -> float:
    if not intents:
        return 0.0
    directions = [str(intent.get("direction", "")) for intent in intents]
    motifs = [str(intent.get("motif", "")) for intent in intents]
    nonempty = sum(1 for direction in directions if direction)
    transitions = sum(1 for left, right in zip(directions, directions[1:]) if left != right)
    motif_consistency = sum(1 for motif in motifs if motif) / len(intents)
    transition_balance = 1.0 if len(intents) == 1 else min(1.0, transitions / max(1, len(intents) - 1) + 0.4)
    return round(_clamp01((nonempty / len(intents)) * 0.45 + motif_consistency * 0.35 + transition_balance * 0.20), 6)


def score_layering(intents: Sequence[Mapping[str, object]]) -> float:
    if not intents:
        return 0.0
    starts = sorted(_float(intent, "start_time") for intent in intents)
    if len(starts) == 1:
        return 0.4
    gaps = [right - left for left, right in zip(starts, starts[1:])]
    tight = sum(1 for gap in gaps if 0.25 <= gap <= 4.0) / len(gaps)
    density = min(1.0, len(intents) / 12.0)
    return round(_clamp01(tight * 0.55 + density * 0.45), 6)


def score_novelty(intents: Sequence[Mapping[str, object]]) -> float:
    if not intents:
        return 0.0
    effects = [str(intent.get("effect_name", "")) for intent in intents if intent.get("effect_name")]
    if not effects:
        return 0.0
    unique_ratio = len(set(effects)) / len(effects)
    repeated_pairs = sum(1 for left, right in zip(effects, effects[1:]) if left == right)
    repetition_penalty = repeated_pairs / max(1, len(effects) - 1)
    return round(_clamp01(unique_ratio * 0.75 + (1.0 - repetition_penalty) * 0.25), 6)


def score_emotion(intents: Sequence[Mapping[str, object]]) -> float:
    if not intents:
        return 0.0
    strengths = [_float(intent, "strength") for intent in intents]
    if not strengths:
        return 0.0
    spread = max(strengths) - min(strengths)
    avg = sum(strengths) / len(strengths)
    return round(_clamp01(avg * 0.55 + spread * 0.45), 6)


def score_birdsong_manifest(manifest: Mapping[str, object]) -> BirdsongQualityReport:
    intents = _records(manifest)
    musicality = score_musicality(intents)
    spatial = score_spatial_coherence(intents)
    layering = score_layering(intents)
    novelty = score_novelty(intents)
    emotion = score_emotion(intents)
    total = round(
        musicality * 0.30
        + spatial * 0.25
        + layering * 0.20
        + novelty * 0.15
        + emotion * 0.10,
        6,
    )
    return BirdsongQualityReport(
        score=total,
        musicality=musicality,
        spatial_coherence=spatial,
        layering=layering,
        novelty=novelty,
        emotion=emotion,
        intent_count=len(intents),
    )
