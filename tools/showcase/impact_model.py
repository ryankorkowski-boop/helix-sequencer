"""Report-only showcase impact model metrics.

These metrics operate only on synthetic, internal, or permissioned impact traces.
They measure general cinematic sequencing grammar: anticipation, drop punch,
finale payoff, and peak density. They do not ingest copyrighted media, public
videos, or creator-specific choreography.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


IMPACT_KINDS = {"drop", "chorus", "finale", "hit", "reveal", "climax"}
RESTRAINT_KINDS = {"silence", "blackout", "sparse", "breath", "pause"}


@dataclass(frozen=True)
class ImpactTrace:
    name: str
    kind: str = "unknown"
    start: float = 0.0
    end: float = 0.0
    intensity: float = 0.5
    breadth: float = 0.5
    darkness_before: float = 0.0
    density_before: float = 0.5
    surprise: float = 0.0
    beat_alignment: float = 0.5

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def impact_energy(self) -> float:
        return _clamp01((0.45 * self.intensity) + (0.25 * self.breadth) + (0.2 * self.beat_alignment) + (0.1 * self.surprise))

    @property
    def anticipation(self) -> float:
        restraint = 1.0 - self.density_before
        return _clamp01((0.55 * restraint) + (0.35 * self.darkness_before) + (0.1 * self.surprise))

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "start": self.start,
            "end": self.end,
            "intensity": self.intensity,
            "breadth": self.breadth,
            "darkness_before": self.darkness_before,
            "density_before": self.density_before,
            "surprise": self.surprise,
            "beat_alignment": self.beat_alignment,
            "impact_energy": self.impact_energy,
            "anticipation": self.anticipation,
        }


@dataclass(frozen=True)
class ImpactFinding:
    code: str
    severity: str
    message: str
    impact: str | None = None
    penalty: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "impact": self.impact,
            "penalty": self.penalty,
        }


@dataclass(frozen=True)
class ImpactReport:
    impact_count: int
    anticipation_score: float
    drop_punch_score: float
    finale_payoff_score: float
    peak_density_score: float
    showcase_impact_score: float
    raw_metrics: dict[str, float] = field(default_factory=dict)
    findings: tuple[ImpactFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "impact_count": self.impact_count,
            "anticipation_score": self.anticipation_score,
            "drop_punch_score": self.drop_punch_score,
            "finale_payoff_score": self.finale_payoff_score,
            "peak_density_score": self.peak_density_score,
            "showcase_impact_score": self.showcase_impact_score,
            "raw_metrics": self.raw_metrics,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def score_impact_model(raw_impacts: Iterable[Mapping[str, object] | ImpactTrace]) -> ImpactReport:
    impacts = sorted((normalize_impact_trace(item) for item in raw_impacts), key=lambda item: item.start)
    findings: list[ImpactFinding] = []
    if not impacts:
        finding = ImpactFinding(
            code="no_impacts",
            severity="warning",
            message="No impact traces were provided, so showcase impact cannot be measured.",
            penalty=1.0,
        )
        return ImpactReport(
            impact_count=0,
            anticipation_score=0.0,
            drop_punch_score=0.0,
            finale_payoff_score=0.0,
            peak_density_score=0.0,
            showcase_impact_score=0.0,
            findings=(finding,),
        )

    anticipation_score = _score_anticipation(impacts, findings)
    drop_punch_score = _score_drop_punch(impacts, findings)
    finale_payoff_score = _score_finale_payoff(impacts, findings)
    peak_density_score = _score_peak_density(impacts, findings)

    showcase_impact_score = round(
        (0.25 * anticipation_score)
        + (0.3 * drop_punch_score)
        + (0.25 * finale_payoff_score)
        + (0.2 * peak_density_score),
        4,
    )

    return ImpactReport(
        impact_count=len(impacts),
        anticipation_score=anticipation_score,
        drop_punch_score=drop_punch_score,
        finale_payoff_score=finale_payoff_score,
        peak_density_score=peak_density_score,
        showcase_impact_score=showcase_impact_score,
        raw_metrics={
            "mean_impact_energy": round(_mean(item.impact_energy for item in impacts), 4),
            "max_impact_energy": round(max(item.impact_energy for item in impacts), 4),
            "mean_anticipation": round(_mean(item.anticipation for item in impacts), 4),
            "mean_beat_alignment": round(_mean(item.beat_alignment for item in impacts), 4),
        },
        findings=tuple(findings),
    )


def normalize_impact_trace(raw: Mapping[str, object] | ImpactTrace) -> ImpactTrace:
    if isinstance(raw, ImpactTrace):
        return raw
    return ImpactTrace(
        name=str(raw.get("name", raw.get("impact_id", "unnamed_impact"))),
        kind=_normalize_token(str(raw.get("kind", "unknown"))),
        start=float(raw.get("start", raw.get("time", 0.0))),
        end=float(raw.get("end", raw.get("time", 0.0))),
        intensity=_clamp01(float(raw.get("intensity", 0.5))),
        breadth=_clamp01(float(raw.get("breadth", raw.get("prop_breadth", 0.5)))),
        darkness_before=_clamp01(float(raw.get("darkness_before", 0.0))),
        density_before=_clamp01(float(raw.get("density_before", 0.5))),
        surprise=_clamp01(float(raw.get("surprise", 0.0))),
        beat_alignment=_clamp01(float(raw.get("beat_alignment", 0.5))),
    )


def _score_anticipation(impacts: list[ImpactTrace], findings: list[ImpactFinding]) -> float:
    impact_events = [item for item in impacts if item.kind in IMPACT_KINDS]
    if not impact_events:
        findings.append(
            ImpactFinding(
                code="no_primary_impact_events",
                severity="info",
                message="No drop/chorus/finale/hit events were available for anticipation scoring.",
                penalty=0.05,
            )
        )
        return 0.6
    score = round(_mean(item.anticipation for item in impact_events), 4)
    if score < 0.45:
        findings.append(
            ImpactFinding(
                code="weak_anticipation",
                severity="warning",
                message="Impact moments are not preceded by enough restraint/darkness/surprise.",
                penalty=0.1,
            )
        )
    return score


def _score_drop_punch(impacts: list[ImpactTrace], findings: list[ImpactFinding]) -> float:
    drops = [item for item in impacts if item.kind in {"drop", "chorus", "hit", "reveal"}]
    if not drops:
        findings.append(
            ImpactFinding(
                code="no_drop_like_impacts",
                severity="info",
                message="No drop-like impact events were available for drop punch scoring.",
                penalty=0.05,
            )
        )
        return 0.6
    scores = [min(1.0, (0.55 * item.impact_energy) + (0.3 * item.anticipation) + (0.15 * item.beat_alignment)) for item in drops]
    score = round(_mean(scores), 4)
    if score < 0.55:
        findings.append(
            ImpactFinding(
                code="weak_drop_punch",
                severity="warning",
                message="Drop-like impact events do not have enough energy/anticipation/beat alignment.",
                penalty=0.1,
            )
        )
    return score


def _score_finale_payoff(impacts: list[ImpactTrace], findings: list[ImpactFinding]) -> float:
    finale_candidates = [item for item in impacts if item.kind in {"finale", "climax"}]
    finale = finale_candidates[-1] if finale_candidates else impacts[-1]
    earlier = [item.impact_energy for item in impacts if item is not finale]
    earlier_peak = max(earlier) if earlier else 0.0
    lift = finale.impact_energy - earlier_peak
    score = round(_clamp01(0.55 + (lift / 0.35) * 0.3 + (0.15 * finale.breadth)), 4)
    if score < 0.65:
        findings.append(
            ImpactFinding(
                code="weak_finale_payoff",
                severity="warning",
                impact=finale.name,
                message="Finale/climax impact does not clearly exceed earlier peaks.",
                penalty=0.12,
            )
        )
    return score


def _score_peak_density(impacts: list[ImpactTrace], findings: list[ImpactFinding]) -> float:
    high = [item for item in impacts if item.impact_energy >= 0.75]
    ratio = len(high) / len(impacts)
    # Showcase impact benefits from a few clear peaks, not constant peak spam.
    if ratio == 0:
        findings.append(
            ImpactFinding(
                code="no_high_impact_peaks",
                severity="info",
                message="No high-impact peaks were detected.",
                penalty=0.08,
            )
        )
        return 0.35
    if ratio > 0.65:
        findings.append(
            ImpactFinding(
                code="peak_spam_risk",
                severity="warning",
                message="Too many impacts are high-energy, which can reduce perceived wow moments.",
                penalty=0.1,
            )
        )
        return round(max(0.35, 1.0 - (ratio - 0.65)), 4)
    return round(min(1.0, 0.55 + ratio), 4)


def _normalize_token(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
