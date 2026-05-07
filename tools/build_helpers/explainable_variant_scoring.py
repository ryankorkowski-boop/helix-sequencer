"""Explainable variant scoring for Helix candidate reports.

Slice 8 is advisory/report-only. This module combines source-agnostic quality
signals into an explainable shortlist score. It does not render effects, write XSQ
content, mutate layouts, choose variants in the active engine, or replace existing
quality-gate behavior by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


PRESET_THRESHOLDS: dict[str, dict[str, float]] = {
    "general": {
        "min_quality_score": 90.0,
        "min_audit_score": 80.0,
        "max_rejected_effects": 28000.0,
        "min_explainable_score": 0.70,
    },
    "showcase": {
        "min_quality_score": 93.0,
        "min_audit_score": 86.0,
        "max_rejected_effects": 18000.0,
        "min_explainable_score": 0.78,
    },
    "vendor": {
        "min_quality_score": 96.0,
        "min_audit_score": 90.0,
        "max_rejected_effects": 12000.0,
        "min_explainable_score": 0.86,
    },
}

DEFAULT_WEIGHTS: dict[str, float] = {
    "quality": 0.18,
    "audit": 0.14,
    "restraint": 0.12,
    "section_identity": 0.14,
    "palette_discipline": 0.12,
    "motif_memory": 0.10,
    "prop_roles": 0.08,
    "manual_lock_respect": 0.07,
    "rejected_effects": 0.05,
}


@dataclass(frozen=True)
class VariantScoreFinding:
    """One explainable variant-scoring finding."""

    code: str
    severity: str
    message: str
    contribution: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "contribution": self.contribution,
        }


@dataclass(frozen=True)
class VariantScoreReport:
    """Explainable combined score for one candidate variant."""

    variant_id: str
    preset: str
    passed: bool
    score: float
    weighted_components: dict[str, float]
    normalized_components: dict[str, float]
    raw_metrics: dict[str, object]
    findings: tuple[VariantScoreFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "variant_id": self.variant_id,
            "preset": self.preset,
            "passed": self.passed,
            "score": self.score,
            "weighted_components": self.weighted_components,
            "normalized_components": self.normalized_components,
            "raw_metrics": self.raw_metrics,
            "findings": [finding.as_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class ShortlistReport:
    """Ranked explainable shortlist output."""

    preset: str
    winner: str | None
    variants: tuple[VariantScoreReport, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "preset": self.preset,
            "winner": self.winner,
            "variants": [variant.as_dict() for variant in self.variants],
        }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _as_float(raw: object, default: float = 0.0) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _nested_score(raw: Mapping[str, object], key: str, default: float = 0.0) -> float:
    value = raw.get(key, default)
    if isinstance(value, Mapping):
        return _clamp01(_as_float(value.get("score", default), default))
    return _clamp01(_as_float(value, default))


def _normalize_rejected_effects(rejected_effects: float, max_rejected_effects: float) -> float:
    if max_rejected_effects <= 0:
        return 0.0 if rejected_effects > 0 else 1.0
    return _clamp01(1.0 - (rejected_effects / max_rejected_effects))


def _get_thresholds(preset: str) -> dict[str, float]:
    return PRESET_THRESHOLDS.get(preset, PRESET_THRESHOLDS["general"])


def score_variant(
    raw_variant: Mapping[str, object],
    preset: str = "showcase",
    weights: Mapping[str, float] | None = None,
) -> VariantScoreReport:
    """Combine available candidate metrics into an explainable score."""

    active_weights = dict(DEFAULT_WEIGHTS)
    if weights:
        active_weights.update({key: float(value) for key, value in weights.items()})
    total_weight = sum(active_weights.values()) or 1.0

    thresholds = _get_thresholds(preset)
    variant_id = str(raw_variant.get("variant_id", raw_variant.get("id", "unnamed_variant")))
    quality_score = _as_float(raw_variant.get("quality_score", raw_variant.get("quality", 0.0)))
    audit_score = _as_float(raw_variant.get("audit_score", raw_variant.get("audit", 0.0)))
    rejected_effects = _as_float(raw_variant.get("rejected_effects", 0.0))

    normalized = {
        "quality": _clamp01(quality_score / 100.0),
        "audit": _clamp01(audit_score / 100.0),
        "restraint": _nested_score(raw_variant, "restraint", 0.75),
        "section_identity": _nested_score(raw_variant, "section_identity", 0.75),
        "palette_discipline": _nested_score(raw_variant, "palette_discipline", 0.75),
        "motif_memory": _nested_score(raw_variant, "motif_memory", 0.75),
        "prop_roles": _nested_score(raw_variant, "prop_roles", 0.75),
        "manual_lock_respect": _nested_score(raw_variant, "manual_lock_respect", 1.0),
        "rejected_effects": _normalize_rejected_effects(rejected_effects, thresholds["max_rejected_effects"]),
    }

    weighted = {
        key: round(normalized.get(key, 0.0) * weight / total_weight, 6)
        for key, weight in active_weights.items()
    }
    score = round(sum(weighted.values()), 4)

    findings: list[VariantScoreFinding] = []
    if quality_score < thresholds["min_quality_score"]:
        findings.append(
            VariantScoreFinding(
                code="quality_below_preset",
                severity="warning",
                message=(
                    f"Quality score {quality_score:.2f} is below {preset} threshold "
                    f"{thresholds['min_quality_score']:.2f}."
                ),
                contribution=weighted["quality"],
            )
        )
    if audit_score < thresholds["min_audit_score"]:
        findings.append(
            VariantScoreFinding(
                code="audit_below_preset",
                severity="warning",
                message=(
                    f"Audit score {audit_score:.2f} is below {preset} threshold "
                    f"{thresholds['min_audit_score']:.2f}."
                ),
                contribution=weighted["audit"],
            )
        )
    if rejected_effects > thresholds["max_rejected_effects"]:
        findings.append(
            VariantScoreFinding(
                code="too_many_rejected_effects",
                severity="warning",
                message=(
                    f"Rejected effects {rejected_effects:.0f} exceed {preset} threshold "
                    f"{thresholds['max_rejected_effects']:.0f}."
                ),
                contribution=weighted["rejected_effects"],
            )
        )

    for key in ("restraint", "section_identity", "palette_discipline", "motif_memory", "prop_roles", "manual_lock_respect"):
        if normalized[key] < 0.65:
            findings.append(
                VariantScoreFinding(
                    code=f"weak_{key}",
                    severity="info",
                    message=f"{key.replace('_', ' ').title()} score is {normalized[key]:.2f}.",
                    contribution=weighted[key],
                )
            )

    if score < thresholds["min_explainable_score"]:
        findings.append(
            VariantScoreFinding(
                code="combined_score_below_preset",
                severity="warning",
                message=(
                    f"Combined explainable score {score:.2f} is below {preset} threshold "
                    f"{thresholds['min_explainable_score']:.2f}."
                ),
                contribution=score,
            )
        )

    passed = (
        quality_score >= thresholds["min_quality_score"]
        and audit_score >= thresholds["min_audit_score"]
        and rejected_effects <= thresholds["max_rejected_effects"]
        and score >= thresholds["min_explainable_score"]
    )

    return VariantScoreReport(
        variant_id=variant_id,
        preset=preset,
        passed=passed,
        score=score,
        weighted_components=weighted,
        normalized_components={key: round(value, 4) for key, value in normalized.items()},
        raw_metrics={
            "quality_score": quality_score,
            "audit_score": audit_score,
            "rejected_effects": rejected_effects,
        },
        findings=tuple(findings),
    )


def rank_variants(
    raw_variants: Iterable[Mapping[str, object]],
    preset: str = "showcase",
    weights: Mapping[str, float] | None = None,
) -> ShortlistReport:
    """Return a ranked explainable shortlist, preferring passing variants."""

    reports = [score_variant(variant, preset=preset, weights=weights) for variant in raw_variants]
    reports.sort(key=lambda item: (item.passed, item.score), reverse=True)
    winner = reports[0].variant_id if reports else None
    return ShortlistReport(preset=preset, winner=winner, variants=tuple(reports))
