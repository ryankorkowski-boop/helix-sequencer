from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PlacementQualityReport:
    schema: str = "helix.placement_quality.v1"
    coverage_score: float = 0.0
    role_match_score: float = 0.0
    effect_variety_score: float = 0.0
    density_control_score: float = 0.0
    brightness_safety_score: float = 0.0
    target_balance_score: float = 0.0
    validation_score: float = 0.0
    overall_placement_score: float = 0.0
    grade: str = "blocked"
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _as_list(value: object) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _grade(score: float) -> str:
    if score >= 0.9:
        return "excellent"
    if score >= 0.82:
        return "showcase_ready"
    if score >= 0.72:
        return "good"
    if score >= 0.6:
        return "prototype"
    return "blocked"


def score_placement_plan(placement_plan: Mapping[str, Any]) -> PlacementQualityReport:
    visual_intents = [item for item in _as_list(placement_plan.get("visual_intents")) if isinstance(item, Mapping)]
    candidates = [item for item in _as_list(placement_plan.get("candidates")) if isinstance(item, Mapping)]
    placements = [item for item in _as_list(placement_plan.get("prop_effect_intents")) if isinstance(item, Mapping)]
    validation = dict(placement_plan.get("validation_report", {}) or {})
    planner = dict(placement_plan.get("planner_report", {}) or {})

    intent_count = int(planner.get("intent_count", len(visual_intents)) or 0)
    placement_count = int(planner.get("placement_count", len(placements)) or 0)
    rejected_count = len(_as_list(planner.get("rejected_intents")))
    capped_count = len(_as_list(planner.get("capped_density_intents")))

    targets = [str(item.get("target_prop", "")) for item in placements if item.get("target_prop")]
    roles = [str(item.get("target_role", "")) for item in placements if item.get("target_role")]
    effects = [str(item.get("effect_family", "")) for item in placements if item.get("effect_family")]
    brightness_caps = [float(item.get("brightness_cap", 0.0) or 0.0) for item in placements]
    candidate_names = {str(item.get("prop_name", "")) for item in candidates if item.get("prop_name")}

    unique_targets = len(set(targets))
    unique_roles = len(set(roles))
    unique_effects = len(set(effects))

    target_counts = Counter(targets)
    most_common_target_share = 0.0
    if placements and target_counts:
        most_common_target_share = target_counts.most_common(1)[0][1] / len(placements)

    coverage_score = _clamp((placement_count / max(1, intent_count)) / 3.0 + min(0.35, unique_targets * 0.035))
    if intent_count and rejected_count:
        coverage_score = _clamp(coverage_score - min(0.35, rejected_count / intent_count))

    missing_candidate_targets = [target for target in targets if candidate_names and target not in candidate_names]
    role_match_score = _clamp(1.0 - (len(missing_candidate_targets) / max(1, len(targets))))
    if not targets:
        role_match_score = 0.0

    effect_variety_score = _clamp(0.35 + min(0.45, unique_effects * 0.09) + min(0.2, unique_roles * 0.04)) if effects else 0.0
    density_control_score = _clamp(1.0 - min(0.45, capped_count / max(1, intent_count)) - min(0.25, max(0.0, most_common_target_share - 0.5)))
    brightness_safety_score = 1.0
    if brightness_caps:
        over_soft_limit = sum(1 for cap in brightness_caps if cap > 0.88)
        brightness_safety_score = _clamp(1.0 - (over_soft_limit / len(brightness_caps)) * 0.55 - max(0.0, max(brightness_caps) - 0.82) * 0.4)

    target_balance_score = _clamp(1.0 - max(0.0, most_common_target_share - 0.45) * 1.25) if targets else 0.0
    validation_score = 1.0 if bool(validation.get("passed", True)) else 0.0
    validation_score = _clamp(validation_score - min(0.3, float(validation.get("warning_count", 0) or 0) * 0.03))

    weighted = (
        coverage_score * 0.22
        + role_match_score * 0.16
        + effect_variety_score * 0.14
        + density_control_score * 0.14
        + brightness_safety_score * 0.12
        + target_balance_score * 0.12
        + validation_score * 0.10
    )
    overall = round(_clamp(weighted), 4)

    recommendations: list[str] = []
    if coverage_score < 0.65:
        recommendations.append("Increase role-matched prop coverage per visual intent.")
    if role_match_score < 0.9:
        recommendations.append("Ensure every placement target is present in the candidate inventory.")
    if effect_variety_score < 0.65:
        recommendations.append("Add more role-appropriate effect family variety.")
    if density_control_score < 0.7:
        recommendations.append("Reduce capped-density intents or spread placements across more targets.")
    if brightness_safety_score < 0.85:
        recommendations.append("Lower high brightness caps before rendering.")
    if validation_score < 1.0:
        recommendations.append("Resolve validation warnings/errors before final render.")

    metrics = {
        "intent_count": intent_count,
        "candidate_count": len(candidates),
        "placement_count": placement_count,
        "unique_target_count": unique_targets,
        "unique_role_count": unique_roles,
        "unique_effect_family_count": unique_effects,
        "rejected_intent_count": rejected_count,
        "capped_intent_count": capped_count,
        "most_common_target_share": round(most_common_target_share, 4),
        "missing_candidate_target_count": len(missing_candidate_targets),
    }

    return PlacementQualityReport(
        coverage_score=round(coverage_score, 4),
        role_match_score=round(role_match_score, 4),
        effect_variety_score=round(effect_variety_score, 4),
        density_control_score=round(density_control_score, 4),
        brightness_safety_score=round(brightness_safety_score, 4),
        target_balance_score=round(target_balance_score, 4),
        validation_score=round(validation_score, 4),
        overall_placement_score=overall,
        grade=_grade(overall),
        recommendations=recommendations,
        metrics=metrics,
    )
