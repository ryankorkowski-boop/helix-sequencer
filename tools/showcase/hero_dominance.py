"""Report-only showcase hero/focal dominance metrics.

These metrics operate only on synthetic, internal, or permissioned section traces.
They do not ingest public videos, copyrighted media, or third-party choreography.
The goal is to measure cinematic staging grammar: clear focal hierarchy, hero
moments, and avoidance of visual mush.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from tools.showcase.trace import SectionTrace, mean, normalize_section_traces


@dataclass(frozen=True)
class HeroDominanceFinding:
    code: str
    severity: str
    message: str
    section: str | None = None
    penalty: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "section": self.section,
            "penalty": self.penalty,
        }


@dataclass(frozen=True)
class HeroDominanceReport:
    section_count: int
    focal_clarity_score: float
    hero_moment_score: float
    support_balance_score: float
    visual_mush_penalty: float
    showcase_hero_score: float
    raw_metrics: dict[str, float] = field(default_factory=dict)
    findings: tuple[HeroDominanceFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "section_count": self.section_count,
            "focal_clarity_score": self.focal_clarity_score,
            "hero_moment_score": self.hero_moment_score,
            "support_balance_score": self.support_balance_score,
            "visual_mush_penalty": self.visual_mush_penalty,
            "showcase_hero_score": self.showcase_hero_score,
            "raw_metrics": self.raw_metrics,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def score_hero_dominance(
    raw_sections: Iterable[Mapping[str, object] | SectionTrace],
) -> HeroDominanceReport:
    """Score focal staging clarity without changing generation behavior."""

    sections = normalize_section_traces(raw_sections)
    findings: list[HeroDominanceFinding] = []
    if not sections:
        finding = HeroDominanceFinding(
            code="no_sections",
            severity="warning",
            message="No section traces were provided, so hero dominance cannot be measured.",
            penalty=1.0,
        )
        return HeroDominanceReport(
            section_count=0,
            focal_clarity_score=0.0,
            hero_moment_score=0.0,
            support_balance_score=0.0,
            visual_mush_penalty=1.0,
            showcase_hero_score=0.0,
            findings=(finding,),
        )

    hero_shares = [section.hero_share for section in sections]
    energies = [section.visual_energy for section in sections]
    high_energy_sections = [section for section in sections if section.visual_energy >= 0.68]

    focal_clarity_score = _score_focal_clarity(sections, findings)
    hero_moment_score = _score_hero_moments(sections, high_energy_sections, findings)
    support_balance_score = _score_support_balance(sections, findings)
    visual_mush_penalty = _score_visual_mush_penalty(sections, findings)

    showcase_hero_score = round(
        max(
            0.0,
            (0.35 * focal_clarity_score)
            + (0.3 * hero_moment_score)
            + (0.2 * support_balance_score)
            + (0.15 * (1.0 - visual_mush_penalty)),
        ),
        4,
    )

    return HeroDominanceReport(
        section_count=len(sections),
        focal_clarity_score=focal_clarity_score,
        hero_moment_score=hero_moment_score,
        support_balance_score=support_balance_score,
        visual_mush_penalty=visual_mush_penalty,
        showcase_hero_score=showcase_hero_score,
        raw_metrics={
            "mean_hero_share": round(mean(hero_shares), 4),
            "max_hero_share": round(max(hero_shares), 4),
            "min_hero_share": round(min(hero_shares), 4),
            "mean_visual_energy": round(mean(energies), 4),
            "high_energy_section_count": float(len(high_energy_sections)),
        },
        findings=tuple(findings),
    )


def _score_focal_clarity(sections: list[SectionTrace], findings: list[HeroDominanceFinding]) -> float:
    # Showcase staging benefits from a readable focal hierarchy. Too little hero
    # share is mush; too much for the whole show can feel like one-prop monotony.
    ideal_scores: list[float] = []
    for section in sections:
        hero = section.hero_share
        if hero < 0.2 and section.visual_energy >= 0.55:
            findings.append(
                HeroDominanceFinding(
                    code="weak_focal_hierarchy",
                    severity="warning",
                    section=section.name,
                    message="Medium/high-energy section has no clear focal hero prop.",
                    penalty=0.08,
                )
            )
        if hero > 0.9 and section.visual_energy < 0.65:
            findings.append(
                HeroDominanceFinding(
                    code="overfocused_low_energy_section",
                    severity="info",
                    section=section.name,
                    message="Low/medium-energy section is dominated almost entirely by one focal prop.",
                    penalty=0.04,
                )
            )
        # Peak around 0.6: clear hero with support still visible.
        ideal_scores.append(max(0.0, 1.0 - abs(hero - 0.6) / 0.6))
    return round(mean(ideal_scores), 4)


def _score_hero_moments(
    sections: list[SectionTrace],
    high_energy_sections: list[SectionTrace],
    findings: list[HeroDominanceFinding],
) -> float:
    if not high_energy_sections:
        findings.append(
            HeroDominanceFinding(
                code="no_high_energy_hero_moments",
                severity="info",
                message="No high-energy sections were available to evaluate hero dominance.",
                penalty=0.06,
            )
        )
        return 0.6 if sections else 0.0

    hero_scores = [min(1.0, section.hero_share / 0.65) for section in high_energy_sections]
    score = round(mean(hero_scores), 4)
    if score < 0.55:
        findings.append(
            HeroDominanceFinding(
                code="weak_hero_moments",
                severity="warning",
                message="High-energy sections do not give enough visual dominance to hero props.",
                penalty=0.12,
            )
        )
    return score


def _score_support_balance(sections: list[SectionTrace], findings: list[HeroDominanceFinding]) -> float:
    # breadth represents how much of the layout participates. Hero share and
    # breadth should both be present in showcase moments: focal point plus support.
    balances: list[float] = []
    for section in sections:
        if section.visual_energy < 0.45:
            balances.append(0.75)
            continue
        hero = section.hero_share
        support_share = max(0.0, 1.0 - hero)
        support_visible = min(1.0, section.breadth / 0.75)
        balance = min(1.0, (0.55 * min(1.0, hero / 0.6)) + (0.45 * min(1.0, support_share * support_visible / 0.35)))
        balances.append(balance)
        if hero >= 0.65 and section.breadth < 0.35:
            findings.append(
                HeroDominanceFinding(
                    code="hero_without_support_stage",
                    severity="info",
                    section=section.name,
                    message="Hero prop is dominant but the supporting stage is too narrow.",
                    penalty=0.05,
                )
            )
    return round(mean(balances), 4)


def _score_visual_mush_penalty(sections: list[SectionTrace], findings: list[HeroDominanceFinding]) -> float:
    mush_sections = []
    for section in sections:
        # High breadth + high energy + low hero share often reads as everything
        # firing at once with no focal point.
        if section.breadth >= 0.8 and section.visual_energy >= 0.68 and section.hero_share < 0.25:
            mush_sections.append(section)
            findings.append(
                HeroDominanceFinding(
                    code="visual_mush_risk",
                    severity="warning",
                    section=section.name,
                    message="High-energy wide-layout section may lack a clear focal point.",
                    penalty=0.1,
                )
            )
    return round(min(1.0, len(mush_sections) / max(1, len(sections))), 4)
