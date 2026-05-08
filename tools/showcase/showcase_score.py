"""Composite showcase scoring for legal-safe Helix reports.

This module combines report-only showcase component scores into one explainable
score. It does not train, scrape, render, mutate layouts, or influence candidate
selection. Inputs should be synthetic, internal, or permissioned metric reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


DEFAULT_SHOWCASE_WEIGHTS: dict[str, float] = {
    "showcase_energy": 0.24,
    "showcase_hero_dominance": 0.20,
    "showcase_motion_continuity": 0.18,
    "showcase_palette_arc": 0.16,
    "showcase_impact_model": 0.22,
}

SCORE_KEY_BY_REPORT = {
    "showcase_energy": "showcase_energy_score",
    "showcase_hero_dominance": "showcase_hero_score",
    "showcase_motion_continuity": "showcase_motion_score",
    "showcase_palette_arc": "showcase_palette_score",
    "showcase_impact_model": "showcase_impact_score",
}


@dataclass(frozen=True)
class ShowcaseScoreFinding:
    code: str
    severity: str
    message: str
    component: str | None = None
    contribution: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "component": self.component,
            "contribution": self.contribution,
        }


@dataclass(frozen=True)
class ShowcaseScoreReport:
    score: float
    available_components: tuple[str, ...]
    missing_components: tuple[str, ...]
    weighted_components: dict[str, float] = field(default_factory=dict)
    normalized_components: dict[str, float] = field(default_factory=dict)
    findings: tuple[ShowcaseScoreFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "available_components": list(self.available_components),
            "missing_components": list(self.missing_components),
            "weighted_components": self.weighted_components,
            "normalized_components": self.normalized_components,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def score_showcase_report(
    reports: Mapping[str, object],
    weights: Mapping[str, float] | None = None,
) -> ShowcaseScoreReport:
    """Combine available showcase metric reports into one score."""

    active_weights = dict(DEFAULT_SHOWCASE_WEIGHTS)
    if weights:
        active_weights.update({key: float(value) for key, value in weights.items()})

    findings: list[ShowcaseScoreFinding] = []
    normalized: dict[str, float] = {}
    missing: list[str] = []

    for report_name, score_key in SCORE_KEY_BY_REPORT.items():
        report = reports.get(report_name)
        if not isinstance(report, Mapping) or score_key not in report:
            missing.append(report_name)
            findings.append(
                ShowcaseScoreFinding(
                    code="missing_showcase_component",
                    severity="info",
                    component=report_name,
                    message=f"Showcase component '{report_name}' was not available for composite scoring.",
                )
            )
            continue
        score = _clamp01(_as_float(report.get(score_key)))
        normalized[report_name] = score
        if score < 0.55:
            findings.append(
                ShowcaseScoreFinding(
                    code="weak_showcase_component",
                    severity="warning",
                    component=report_name,
                    message=f"Showcase component '{report_name}' is weak at {score:.2f}.",
                )
            )

    available = sorted(normalized)
    if not normalized:
        findings.append(
            ShowcaseScoreFinding(
                code="no_showcase_components",
                severity="warning",
                message="No showcase components were available for composite scoring.",
            )
        )
        return ShowcaseScoreReport(
            score=0.0,
            available_components=(),
            missing_components=tuple(missing),
            findings=tuple(findings),
        )

    available_weight_total = sum(active_weights.get(component, 0.0) for component in normalized) or 1.0
    weighted = {
        component: round(normalized[component] * active_weights.get(component, 0.0) / available_weight_total, 6)
        for component in normalized
    }
    score = round(sum(weighted.values()), 4)

    for component, contribution in weighted.items():
        findings.append(
            ShowcaseScoreFinding(
                code="showcase_component_contribution",
                severity="debug",
                component=component,
                contribution=contribution,
                message=f"Component '{component}' contributed {contribution:.4f} to composite showcase score.",
            )
        )

    return ShowcaseScoreReport(
        score=score,
        available_components=tuple(available),
        missing_components=tuple(missing),
        weighted_components=weighted,
        normalized_components={key: round(value, 4) for key, value in normalized.items()},
        findings=tuple(findings),
    )


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
