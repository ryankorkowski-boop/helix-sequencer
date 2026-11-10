from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping


SUPPORTED_EFFECT_FAMILIES = {
    "energy_wave",
    "soft_wash",
    "directional_sweep",
    "melody_trail",
    "matrix_pulse",
    "outline_pulse",
    "lyric_pulse",
    "character_hit",
    "beat_pulse",
    "sparkle_accent",
    "support_pulse",
}

MAX_BRIGHTNESS_CAP = 0.88
MAX_SINGLE_TARGET_SHARE = 0.55
MAX_REJECTED_INTENT_SHARE = 0.25
MAX_CAPPED_INTENT_SHARE = 0.5


@dataclass(frozen=True)
class PlacementValidationReport:
    schema: str = "helix.placement_validation.v1"
    passed: bool = True
    error_count: int = 0
    warning_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_list(value: object) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def validate_placement_plan(
    placement_plan: Mapping[str, Any],
    *,
    supported_effect_families: Iterable[str] = SUPPORTED_EFFECT_FAMILIES,
) -> PlacementValidationReport:
    visual_intents = [item for item in _as_list(placement_plan.get("visual_intents")) if isinstance(item, Mapping)]
    candidates = [item for item in _as_list(placement_plan.get("candidates")) if isinstance(item, Mapping)]
    placements = [item for item in _as_list(placement_plan.get("prop_effect_intents")) if isinstance(item, Mapping)]
    planner_report = dict(placement_plan.get("planner_report", {}) or {})
    allowed_effects = set(supported_effect_families)

    errors: list[str] = []
    warnings: list[str] = []

    intent_count = int(planner_report.get("intent_count", len(visual_intents)) or 0)
    placement_count = int(planner_report.get("placement_count", len(placements)) or 0)
    rejected_intents = [str(item) for item in _as_list(planner_report.get("rejected_intents"))]
    capped_intents = [str(item) for item in _as_list(planner_report.get("capped_density_intents"))]

    if intent_count > 0 and not placements:
        errors.append("Placement plan has visual intents but no prop-effect intents.")
    if placements and not candidates:
        warnings.append("Placement plan has prop-effect intents but no candidate inventory.")
    if placement_count != len(placements):
        warnings.append("Planner placement_count does not match exported prop-effect intent count.")

    known_intents = {str(item.get("id", "")) for item in visual_intents}
    known_candidates = {str(item.get("prop_name", "")) for item in candidates}
    target_counts: Counter[str] = Counter()
    effect_counts: Counter[str] = Counter()

    for idx, placement in enumerate(placements):
        prefix = f"placement[{idx}]"
        target_prop = str(placement.get("target_prop", ""))
        visual_intent_id = str(placement.get("visual_intent_id", ""))
        effect_family = str(placement.get("effect_family", ""))
        brightness_cap = _as_float(placement.get("brightness_cap"), -1.0)

        if not target_prop:
            errors.append(f"{prefix} is missing target_prop.")
        elif known_candidates and target_prop not in known_candidates:
            warnings.append(f"{prefix} targets prop not present in candidate inventory: {target_prop}")
        else:
            target_counts[target_prop] += 1

        if not visual_intent_id:
            errors.append(f"{prefix} is missing visual_intent_id.")
        elif known_intents and visual_intent_id not in known_intents:
            warnings.append(f"{prefix} references unknown visual_intent_id: {visual_intent_id}")

        if not effect_family:
            errors.append(f"{prefix} is missing effect_family.")
        elif effect_family not in allowed_effects:
            errors.append(f"{prefix} uses unsupported effect_family: {effect_family}")
        else:
            effect_counts[effect_family] += 1

        if brightness_cap < 0.0 or brightness_cap > 1.0:
            errors.append(f"{prefix} has brightness_cap outside 0..1: {brightness_cap}")
        elif brightness_cap > MAX_BRIGHTNESS_CAP:
            warnings.append(f"{prefix} has high brightness_cap: {brightness_cap:.3f}")

    rejected_share = (len(rejected_intents) / intent_count) if intent_count else 0.0
    capped_share = (len(capped_intents) / intent_count) if intent_count else 0.0
    if rejected_share > MAX_REJECTED_INTENT_SHARE:
        errors.append(f"Rejected intent share too high: {rejected_share:.3f}")
    elif rejected_intents:
        warnings.append(f"Rejected intents present: {', '.join(rejected_intents)}")

    if capped_share > MAX_CAPPED_INTENT_SHARE:
        warnings.append(f"Density-capped intent share is high: {capped_share:.3f}")

    most_common_target_share = 0.0
    if placements and target_counts:
        _target, count = target_counts.most_common(1)[0]
        most_common_target_share = count / len(placements)
        if most_common_target_share > MAX_SINGLE_TARGET_SHARE:
            warnings.append(f"One target receives too much of the plan: {most_common_target_share:.3f}")

    metrics = {
        "intent_count": intent_count,
        "candidate_count": len(candidates),
        "placement_count": len(placements),
        "rejected_intent_count": len(rejected_intents),
        "capped_intent_count": len(capped_intents),
        "rejected_intent_share": round(rejected_share, 4),
        "capped_intent_share": round(capped_share, 4),
        "unique_target_count": len(target_counts),
        "effect_family_count": len(effect_counts),
        "most_common_target_share": round(most_common_target_share, 4),
    }

    return PlacementValidationReport(
        passed=not errors,
        error_count=len(errors),
        warning_count=len(warnings),
        errors=errors,
        warnings=warnings,
        metrics=metrics,
    )
