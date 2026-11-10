"""Advisory section-identity scoring for Helix sequence planning.

This module is renderer-neutral. It does not render effects, write XSQ content,
mutate layouts, or promote/reject variants on its own. It gives future reporting
and shortlist logic a source-agnostic way to measure whether song sections have
clear visual contrast, shaped intensity, and a strong earned finale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence


DENSITY_WEIGHTS = {
    "none": 0.0,
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "peak": 1.0,
}

SECTION_KINDS_EXPECTED_INTENSITY = {
    "intro": (0.1, 0.55),
    "verse": (0.2, 0.65),
    "pre_chorus": (0.45, 0.8),
    "chorus": (0.65, 0.95),
    "bridge": (0.25, 0.85),
    "solo": (0.55, 0.95),
    "breakdown": (0.15, 0.75),
    "drop": (0.8, 1.0),
    "finale": (0.85, 1.0),
    "outro": (0.1, 0.7),
    "unknown": (0.0, 1.0),
}


@dataclass(frozen=True)
class SectionView:
    """Normalized minimal section data used by the identity scorer."""

    name: str
    kind: str = "unknown"
    start: float = 0.0
    end: float = 0.0
    target_intensity: float = 0.5
    primary_groups: tuple[str, ...] = field(default_factory=tuple)
    secondary_groups: tuple[str, ...] = field(default_factory=tuple)
    palette: str = ""
    motion_intent: str = ""
    density: str = "medium"

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def all_groups(self) -> tuple[str, ...]:
        seen: list[str] = []
        for group in (*self.primary_groups, *self.secondary_groups):
            if group not in seen:
                seen.append(group)
        return tuple(seen)

    @property
    def density_value(self) -> float:
        return DENSITY_WEIGHTS.get(self.density.lower(), 0.5)


@dataclass(frozen=True)
class SectionIdentityFinding:
    """One advisory finding produced by section-identity scoring."""

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
class SectionIdentityReport:
    """Summarized advisory score for section contrast and shape."""

    section_count: int
    coverage_score: float
    contrast_score: float
    intensity_shape_score: float
    finale_strength_score: float
    score: float
    findings: tuple[SectionIdentityFinding, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "section_count": self.section_count,
            "coverage_score": self.coverage_score,
            "contrast_score": self.contrast_score,
            "intensity_shape_score": self.intensity_shape_score,
            "finale_strength_score": self.finale_strength_score,
            "score": self.score,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return ()


def normalize_section(raw: Mapping[str, object] | SectionView) -> SectionView:
    """Normalize section-like mappings while preserving SectionView objects."""

    if isinstance(raw, SectionView):
        return raw

    return SectionView(
        name=str(raw.get("name", raw.get("kind", "unknown"))),
        kind=str(raw.get("kind", "unknown")),
        start=float(raw.get("start", 0.0)),
        end=float(raw.get("end", 0.0)),
        target_intensity=float(raw.get("target_intensity", raw.get("intensity", 0.5))),
        primary_groups=_as_string_tuple(raw.get("primary_groups")),
        secondary_groups=_as_string_tuple(raw.get("secondary_groups")),
        palette=str(raw.get("palette", "")),
        motion_intent=str(raw.get("motion_intent", "")),
        density=str(raw.get("density", "medium")),
    )


def normalize_sections(raw_sections: Iterable[Mapping[str, object] | SectionView]) -> list[SectionView]:
    """Normalize and sort sections by start time."""

    return sorted((normalize_section(section) for section in raw_sections), key=lambda section: section.start)


def _jaccard_similarity(left: Sequence[str], right: Sequence[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    union = left_set | right_set
    if not union:
        return 1.0
    return len(left_set & right_set) / len(union)


def _section_delta(left: SectionView, right: SectionView) -> float:
    intensity_delta = abs(left.target_intensity - right.target_intensity)
    density_delta = abs(left.density_value - right.density_value)
    palette_delta = 0.0 if left.palette and left.palette == right.palette else 0.2
    motion_delta = 0.0 if left.motion_intent and left.motion_intent == right.motion_intent else 0.15
    group_delta = 1.0 - _jaccard_similarity(left.all_groups, right.all_groups)

    # Weighted, capped visual-difference estimate. This is intentionally simple
    # and source-agnostic until real render metrics are wired in.
    return min(
        1.0,
        (0.35 * intensity_delta)
        + (0.2 * density_delta)
        + (0.2 * group_delta)
        + palette_delta
        + motion_delta,
    )


def _score_coverage(sections: Sequence[SectionView], findings: list[SectionIdentityFinding]) -> float:
    if not sections:
        findings.append(
            SectionIdentityFinding(
                code="no_sections",
                severity="warning",
                message="No sections were provided, so section identity cannot be measured.",
                penalty=1.0,
            )
        )
        return 0.0

    missing_data_penalty = 0.0
    for section in sections:
        if section.duration <= 0:
            missing_data_penalty += 0.12
            findings.append(
                SectionIdentityFinding(
                    code="invalid_section_duration",
                    severity="warning",
                    section=section.name,
                    penalty=0.12,
                    message=f"Section '{section.name}' has non-positive duration.",
                )
            )
        if not section.all_groups:
            missing_data_penalty += 0.08
            findings.append(
                SectionIdentityFinding(
                    code="section_missing_groups",
                    severity="info",
                    section=section.name,
                    penalty=0.08,
                    message=f"Section '{section.name}' has no primary or secondary prop groups.",
                )
            )
        if not section.palette:
            missing_data_penalty += 0.05
            findings.append(
                SectionIdentityFinding(
                    code="section_missing_palette",
                    severity="info",
                    section=section.name,
                    penalty=0.05,
                    message=f"Section '{section.name}' has no palette intent.",
                )
            )

    return max(0.0, round(1.0 - min(1.0, missing_data_penalty), 4))


def _score_contrast(sections: Sequence[SectionView], findings: list[SectionIdentityFinding]) -> float:
    if len(sections) < 2:
        findings.append(
            SectionIdentityFinding(
                code="not_enough_sections_for_contrast",
                severity="info",
                message="At least two sections are needed to measure section contrast.",
                penalty=0.25,
            )
        )
        return 0.75 if sections else 0.0

    deltas = [_section_delta(left, right) for left, right in zip(sections, sections[1:])]
    average_delta = sum(deltas) / len(deltas)

    for index, delta in enumerate(deltas):
        if delta < 0.18:
            section = sections[index + 1]
            findings.append(
                SectionIdentityFinding(
                    code="weak_adjacent_section_contrast",
                    severity="warning",
                    section=section.name,
                    penalty=0.08,
                    message=(
                        f"Section '{section.name}' is visually similar to the previous section "
                        f"based on intensity, density, groups, palette, and motion intent."
                    ),
                )
            )

    # Deltas around 0.35+ are usually enough to read as a meaningful section
    # change in this advisory model.
    return round(min(1.0, average_delta / 0.35), 4)


def _score_intensity_shape(sections: Sequence[SectionView], findings: list[SectionIdentityFinding]) -> float:
    if not sections:
        return 0.0

    penalty = 0.0
    for section in sections:
        expected_low, expected_high = SECTION_KINDS_EXPECTED_INTENSITY.get(
            section.kind, SECTION_KINDS_EXPECTED_INTENSITY["unknown"]
        )
        if section.target_intensity < expected_low or section.target_intensity > expected_high:
            penalty += 0.08
            findings.append(
                SectionIdentityFinding(
                    code="section_intensity_out_of_expected_range",
                    severity="info",
                    section=section.name,
                    penalty=0.08,
                    message=(
                        f"Section '{section.name}' kind '{section.kind}' has target intensity "
                        f"{section.target_intensity:.2f}; expected roughly {expected_low:.2f}-{expected_high:.2f}."
                    ),
                )
            )

    # Reward an overall climb from intro/early material toward later high-energy
    # material, without requiring every section to be louder than the last.
    first = sections[0].target_intensity
    peak = max(section.target_intensity for section in sections)
    early_peak = max(section.target_intensity for section in sections[: max(1, len(sections) // 2)])
    late_peak = max(section.target_intensity for section in sections[max(1, len(sections) // 2) :]) if len(sections) > 1 else peak

    shape_bonus = 0.0
    if peak - first >= 0.25:
        shape_bonus += 0.15
    if late_peak >= early_peak:
        shape_bonus += 0.1

    return round(max(0.0, min(1.0, 0.85 + shape_bonus - penalty)), 4)


def _score_finale(sections: Sequence[SectionView], findings: list[SectionIdentityFinding]) -> float:
    if not sections:
        return 0.0

    finale_candidates = [section for section in sections if section.kind == "finale"]
    finale = finale_candidates[-1] if finale_candidates else sections[-1]

    score = 0.0
    if finale.target_intensity >= 0.85:
        score += 0.45
    else:
        findings.append(
            SectionIdentityFinding(
                code="weak_finale_intensity",
                severity="warning",
                section=finale.name,
                penalty=0.15,
                message=f"Final section '{finale.name}' target intensity is below 0.85.",
            )
        )

    if finale.density_value >= 0.75:
        score += 0.2
    else:
        findings.append(
            SectionIdentityFinding(
                code="weak_finale_density",
                severity="info",
                section=finale.name,
                penalty=0.08,
                message=f"Final section '{finale.name}' density is not high/peak.",
            )
        )

    if len(finale.all_groups) >= 2 or "whole_layout" in finale.all_groups or "whole_house" in finale.all_groups:
        score += 0.2
    else:
        findings.append(
            SectionIdentityFinding(
                code="narrow_finale_coverage",
                severity="info",
                section=finale.name,
                penalty=0.08,
                message=f"Final section '{finale.name}' uses limited prop coverage.",
            )
        )

    if finale.palette:
        score += 0.15

    return round(min(1.0, score), 4)


def score_section_identity(raw_sections: Iterable[Mapping[str, object] | SectionView]) -> SectionIdentityReport:
    """Score whether planned sections have readable visual identities."""

    sections = normalize_sections(raw_sections)
    findings: list[SectionIdentityFinding] = []

    coverage_score = _score_coverage(sections, findings)
    contrast_score = _score_contrast(sections, findings)
    intensity_shape_score = _score_intensity_shape(sections, findings)
    finale_strength_score = _score_finale(sections, findings)

    score = round(
        (0.25 * coverage_score)
        + (0.3 * contrast_score)
        + (0.25 * intensity_shape_score)
        + (0.2 * finale_strength_score),
        4,
    )

    return SectionIdentityReport(
        section_count=len(sections),
        coverage_score=coverage_score,
        contrast_score=contrast_score,
        intensity_shape_score=intensity_shape_score,
        finale_strength_score=finale_strength_score,
        score=score,
        findings=tuple(findings),
    )
