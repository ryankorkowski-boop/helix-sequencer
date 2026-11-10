from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.helix_flow_baseline_compare import BaselineComparison, compare_to_baseline


@dataclass(frozen=True)
class IterationAdvice:
    iteration: int
    weakest_category: str
    action: str
    parameter_updates: dict[str, float | int | str]
    rationale: str

    def as_dict(self) -> dict[str, object]:
        return {
            "iteration": self.iteration,
            "weakest_category": self.weakest_category,
            "action": self.action,
            "parameter_updates": self.parameter_updates,
            "rationale": self.rationale,
        }


ADJUSTMENT_TABLE: dict[str, tuple[str, dict[str, float | int | str], str]] = {
    "musicality": (
        "prefer higher context-fit effects",
        {"min_effect_score": 0.62, "recent_effect_window": 4},
        "Musicality is weakest, so filter out low-ranked effects and keep recent context available for scoring.",
    ),
    "spatial_coherence": (
        "lengthen directional spatial paths",
        {"spread_path_max_models": 5, "direction_weight": 1.15},
        "Spatial coherence is weakest, so use longer directional cascades and bias toward path continuity.",
    ),
    "layering": (
        "increase controlled stagger overlap",
        {"cascade_stagger_seconds": 0.18, "max_parallel_layers": 3},
        "Layering is weakest, so increase useful overlap without creating dense clutter.",
    ),
    "novelty": (
        "rotate repeated effect families",
        {"recent_effect_window": 6, "novelty_weight": 1.20},
        "Novelty is weakest, so penalize repeated effects for a longer window and raise novelty weighting.",
    ),
    "emotion": (
        "increase phrase-level strength contrast",
        {"strength_contrast_boost": 1.15, "min_strength_delta": 0.18},
        "Emotion is weakest, so increase dynamic contrast across phrase-level intent strength.",
    ),
}


def build_iteration_advice(
    quality_report: Mapping[str, object],
    *,
    iteration: int = 1,
    min_delta: float = 0.0,
) -> IterationAdvice:
    if iteration <= 0:
        raise ValueError("iteration must be > 0")
    comparison = compare_to_baseline(quality_report, min_delta=min_delta)
    action, updates, rationale = ADJUSTMENT_TABLE.get(
        comparison.weakest_category,
        (
            "inspect generated artifacts",
            {"manual_review_required": "true"},
            "No known weakest category was found; inspect the generated XSQ and MP4 artifacts.",
        ),
    )
    return IterationAdvice(
        iteration=iteration,
        weakest_category=comparison.weakest_category,
        action=action,
        parameter_updates=updates,
        rationale=rationale,
    )


def build_iteration_report(
    quality_report: Mapping[str, object],
    *,
    iteration: int = 1,
    min_delta: float = 0.0,
) -> dict[str, object]:
    comparison: BaselineComparison = compare_to_baseline(quality_report, min_delta=min_delta)
    advice = build_iteration_advice(quality_report, iteration=iteration, min_delta=min_delta)
    return {
        "comparison": comparison.as_dict(),
        "iteration_advice": advice.as_dict(),
    }
