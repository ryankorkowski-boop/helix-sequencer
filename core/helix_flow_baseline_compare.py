from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


BASELINE_QUALITY: dict[str, float] = {
    "score": 0.55,
    "musicality": 0.55,
    "spatial_coherence": 0.50,
    "layering": 0.45,
    "novelty": 0.50,
    "emotion": 0.45,
}

QUALITY_KEYS: tuple[str, ...] = (
    "score",
    "musicality",
    "spatial_coherence",
    "layering",
    "novelty",
    "emotion",
)


@dataclass(frozen=True)
class BaselineComparison:
    score: float
    baseline_score: float
    delta: float
    passed: bool
    weakest_category: str
    deltas: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "baseline_score": self.baseline_score,
            "delta": self.delta,
            "passed": self.passed,
            "weakest_category": self.weakest_category,
            "deltas": self.deltas,
        }


def _metric(report: Mapping[str, object], key: str) -> float:
    try:
        return float(report.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def compare_to_baseline(
    report: Mapping[str, object],
    *,
    baseline: Mapping[str, float] = BASELINE_QUALITY,
    min_delta: float = 0.0,
) -> BaselineComparison:
    deltas = {
        key: round(_metric(report, key) - float(baseline.get(key, 0.0)), 6)
        for key in QUALITY_KEYS
    }
    score = _metric(report, "score")
    baseline_score = float(baseline.get("score", 0.0))
    weakest = min((key for key in QUALITY_KEYS if key != "score"), key=lambda key: (_metric(report, key), key))
    delta = round(score - baseline_score, 6)
    return BaselineComparison(
        score=round(score, 6),
        baseline_score=round(baseline_score, 6),
        delta=delta,
        passed=delta >= min_delta,
        weakest_category=weakest,
        deltas=deltas,
    )


def recommended_next_adjustment(comparison: BaselineComparison) -> str:
    recommendations = {
        "musicality": "increase phrase/effect score fit and reduce low-scoring intents",
        "spatial_coherence": "increase path continuity and direction-aware target selection",
        "layering": "increase useful staggered overlaps while avoiding clutter",
        "novelty": "reduce repeated effect names and rotate motif-compatible candidates",
        "emotion": "increase strength contrast and phrase-level energy arcs",
    }
    return recommendations.get(comparison.weakest_category, "inspect quality report and add a targeted planner adjustment")
