from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class RenderPermissionReport:
    schema: str = "helix.render_permission.v1"
    allowed: bool = False
    reason: str = "blocked"
    minimum_quality_score: float = 0.6
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_render_permission(
    placement_plan: Mapping[str, Any],
    *,
    minimum_quality_score: float = 0.6,
    allow_warnings: bool = True,
) -> RenderPermissionReport:
    validation = dict(placement_plan.get("validation_report", {}) or {})
    quality = dict(placement_plan.get("quality_report", {}) or {})
    errors: list[str] = []
    warnings: list[str] = []

    if not bool(validation.get("passed", False)):
        errors.append("Placement validation failed.")
        errors.extend(str(item) for item in list(validation.get("errors", []) or []))

    quality_score = float(quality.get("overall_placement_score", 0.0) or 0.0)
    if quality_score < minimum_quality_score:
        errors.append(f"Placement quality below render threshold: {quality_score:.4f} < {minimum_quality_score:.4f}")

    warnings.extend(str(item) for item in list(validation.get("warnings", []) or []))
    warnings.extend(str(item) for item in list(quality.get("recommendations", []) or []))
    if warnings and not allow_warnings:
        errors.append("Warnings are present and allow_warnings is false.")

    allowed = not errors
    reason = "allowed" if allowed else "blocked"
    return RenderPermissionReport(
        allowed=allowed,
        reason=reason,
        minimum_quality_score=minimum_quality_score,
        errors=errors,
        warnings=warnings,
    )
