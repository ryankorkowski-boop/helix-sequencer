"""Report-only showcase energy metrics.

These metrics operate on synthetic/internal/permissioned section traces. They do
not ingest public videos, copyrighted media, or third-party choreography. The goal
is to measure cinematic sequencing grammar: restraint, lift, drop payoff, and
finale escalation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from tools.showcase.trace import SectionTrace, mean, normalize_section_traces


CHORUS_KINDS = {"chorus", "drop", "refrain"}
VERSE_KINDS = {"verse", "intro", "pre_chorus", "bridge", "breakdown"}
FINALE_KINDS = {"finale", "outro"}


@dataclass(frozen=True)
class ShowcaseEnergyFinding:
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
class ShowcaseEnergyReport:
    section_count: int
    energy_curve_score: float
    chorus_contrast_delta: float
    drop_amplification_index: float
    finale_escalation_index: float
    showcase_energy_score: float
    raw_metrics: dict[str, float] = field(default_factory=dict)
    findings: tuple[ShowcaseEnergyFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "section_count": self.section_count,
            "energy_curve_score": self.energy_curve_score,
            "chorus_contrast_delta": self.chorus_contrast_delta,
            "drop_amplification_index": self.drop_amplification_index,
            "finale_escalation_index": self.finale_escalation_index,
            "showcase_energy_score": self.showcase_energy_score,
            "raw_metrics": self.raw_metrics,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def score_showcase_energy(
    raw_sections: Iterable[Mapping[str, object] | SectionTrace],
) -> ShowcaseEnergyReport:
    """Score macro energy grammar without changing generation behavior."""

    sections = normalize_section_traces(raw_sections)
    findings: list[ShowcaseEnergyFinding] = []
    if not sections:
        finding = ShowcaseEnergyFinding(
            code="no_sections",
            severity="warning",
            message="No section traces were provided, so showcase energy cannot be measured.",
            penalty=1.0,
        )
        return ShowcaseEnergyReport(
            section_count=0,
            energy_curve_score=0.0,
            chorus_contrast_delta=0.0,
            drop_amplification_index=0.0,
            finale_escalation_index=0.0,
            showcase_energy_score=0.0,
            findings=(finding,),
        )

    energies = [section.visual_energy for section in sections]
    first_energy = energies[0]
    peak_energy = max(energies)
    peak_index = energies.index(peak_energy)
    final_energy = energies[-1]

    early_count = max(1, len(sections) // 3)
    late_start = max(0, len(sections) - early_count)
    early_mean = mean(energies[:early_count])
    late_mean = mean(energies[late_start:])
    overall_mean = mean(energies)

    intro_restraint = max(0.0, min(1.0, 1.0 - early_mean))
    late_lift = max(0.0, min(1.0, late_mean - early_mean + 0.5))
    peak_placement = 1.0 if peak_index >= max(0, len(sections) - 2) else max(0.0, peak_index / max(1, len(sections) - 1))
    variation = max(energies) - min(energies)
    variation_score = min(1.0, variation / 0.45)
    energy_curve_score = round((0.25 * intro_restraint) + (0.3 * late_lift) + (0.25 * peak_placement) + (0.2 * variation_score), 4)

    if variation < 0.18:
        findings.append(
            ShowcaseEnergyFinding(
                code="flat_energy_curve",
                severity="warning",
                message="Section energy is too flat to read as showcase-level pacing.",
                penalty=0.15,
            )
        )
    if final_energy < peak_energy - 0.2:
        findings.append(
            ShowcaseEnergyFinding(
                code="finale_not_near_peak",
                severity="info",
                section=sections[-1].name,
                message="The final section is substantially below the sequence peak.",
                penalty=0.08,
            )
        )

    chorus_sections = [section for section in sections if section.kind in CHORUS_KINDS]
    verse_sections = [section for section in sections if section.kind in VERSE_KINDS]
    chorus_mean = mean(section.visual_energy for section in chorus_sections)
    verse_mean = mean(section.visual_energy for section in verse_sections)
    chorus_delta_raw = chorus_mean - verse_mean if chorus_sections and verse_sections else 0.0
    chorus_contrast_delta = round(max(0.0, min(1.0, (chorus_delta_raw + 0.15) / 0.5)), 4)
    if chorus_sections and verse_sections and chorus_delta_raw < 0.12:
        findings.append(
            ShowcaseEnergyFinding(
                code="weak_chorus_lift",
                severity="warning",
                message="Chorus/drop sections do not lift strongly enough over lower-energy sections.",
                penalty=0.12,
            )
        )

    drop_amplification_index = _score_drop_amplification(sections, findings)
    finale_escalation_index = _score_finale_escalation(sections, findings)

    showcase_energy_score = round(
        (0.35 * energy_curve_score)
        + (0.25 * chorus_contrast_delta)
        + (0.2 * drop_amplification_index)
        + (0.2 * finale_escalation_index),
        4,
    )

    return ShowcaseEnergyReport(
        section_count=len(sections),
        energy_curve_score=energy_curve_score,
        chorus_contrast_delta=chorus_contrast_delta,
        drop_amplification_index=drop_amplification_index,
        finale_escalation_index=finale_escalation_index,
        showcase_energy_score=showcase_energy_score,
        raw_metrics={
            "early_mean_energy": round(early_mean, 4),
            "late_mean_energy": round(late_mean, 4),
            "overall_mean_energy": round(overall_mean, 4),
            "peak_energy": round(peak_energy, 4),
            "final_energy": round(final_energy, 4),
            "energy_variation": round(variation, 4),
            "chorus_mean_energy": round(chorus_mean, 4),
            "verse_mean_energy": round(verse_mean, 4),
            "chorus_delta_raw": round(chorus_delta_raw, 4),
        },
        findings=tuple(findings),
    )


def _score_drop_amplification(sections: list[SectionTrace], findings: list[ShowcaseEnergyFinding]) -> float:
    drop_scores: list[float] = []
    for index, section in enumerate(sections):
        if section.kind not in {"drop", "chorus"} or index == 0:
            continue
        previous = sections[index - 1]
        pre_restraint = max(0.0, 1.0 - previous.visual_energy)
        lift = max(0.0, section.visual_energy - previous.visual_energy)
        darkness_release = max(0.0, previous.darkness - section.darkness)
        drop_scores.append(min(1.0, (0.45 * pre_restraint) + (0.4 * min(1.0, lift / 0.35)) + (0.15 * darkness_release)))

    if not drop_scores:
        findings.append(
            ShowcaseEnergyFinding(
                code="no_drop_or_chorus_for_amplification",
                severity="info",
                message="No drop/chorus transition was available for drop amplification scoring.",
                penalty=0.05,
            )
        )
        return 0.6 if sections else 0.0
    score = round(mean(drop_scores), 4)
    if score < 0.45:
        findings.append(
            ShowcaseEnergyFinding(
                code="weak_drop_amplification",
                severity="info",
                message="Drop/chorus sections do not expand enough from the preceding section.",
                penalty=0.08,
            )
        )
    return score


def _score_finale_escalation(sections: list[SectionTrace], findings: list[ShowcaseEnergyFinding]) -> float:
    finale_candidates = [section for section in sections if section.kind in FINALE_KINDS]
    finale = finale_candidates[-1] if finale_candidates else sections[-1]
    earlier = [section.visual_energy for section in sections if section is not finale]
    earlier_peak = max(earlier) if earlier else 0.0
    finale_energy = finale.visual_energy
    lift = finale_energy - earlier_peak
    breadth_bonus = finale.breadth
    hero_bonus = finale.hero_share
    score = round(max(0.0, min(1.0, 0.45 + (lift / 0.35) * 0.35 + (0.1 * breadth_bonus) + (0.1 * hero_bonus))), 4)
    if score < 0.65:
        findings.append(
            ShowcaseEnergyFinding(
                code="weak_finale_escalation",
                severity="warning",
                section=finale.name,
                message="Finale does not decisively exceed earlier energy/focal breadth.",
                penalty=0.12,
            )
        )
    return score
