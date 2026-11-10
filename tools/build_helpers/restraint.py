"""Advisory density and restraint scoring for Helix sequence planning.

This module is intentionally renderer-neutral. It does not render effects, write XSQ
content, mutate layouts, or reject effects on its own. It gives future planning,
quality-reporting, and shortlist logic a source-agnostic way to identify clutter,
major-hit overuse, strobe misuse, and excessive simultaneous dominance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence


MAJOR_CUE_KINDS = {
    "major_hit",
    "whole_house_hit",
    "section_peak",
    "finale_hit",
    "transition",
}

STROBE_EFFECT_TERMS = ("strobe", "flash", "blinder", "flicker")
WHOLE_LAYOUT_GROUPS = {"whole_layout", "whole_house", "all_models", "all models", "everything"}


@dataclass(frozen=True)
class RestraintRules:
    """Source-agnostic limits for clutter control."""

    max_whole_house_hits_per_section: int = 4
    min_seconds_between_major_hits: float = 2.0
    max_simultaneous_dominant_groups: int = 3
    allow_strobe: bool = True
    strobe_requires_intensity_at_least: float = 0.85
    protect_manual_effects: bool = True


@dataclass(frozen=True)
class CueView:
    """Normalized minimal cue data used by the restraint scorer."""

    time: float
    kind: str
    intensity: float = 0.0
    target_groups: tuple[str, ...] = field(default_factory=tuple)
    effect_family: str = ""
    section: str | None = None
    locked: bool = False
    source: str = "planner"


@dataclass(frozen=True)
class RestraintFinding:
    """One advisory finding produced by the density/restraint scorer."""

    code: str
    severity: str
    message: str
    time: float | None = None
    section: str | None = None
    penalty: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "time": self.time,
            "section": self.section,
            "penalty": self.penalty,
        }


@dataclass(frozen=True)
class RestraintReport:
    """Summarized advisory score for density/restraint checks."""

    cue_count: int
    major_hit_count: int
    whole_house_hit_count: int
    strobe_count: int
    density_penalty: float
    score: float
    findings: tuple[RestraintFinding, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "cue_count": self.cue_count,
            "major_hit_count": self.major_hit_count,
            "whole_house_hit_count": self.whole_house_hit_count,
            "strobe_count": self.strobe_count,
            "density_penalty": self.density_penalty,
            "score": self.score,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def _normalize_group(group: str) -> str:
    return " ".join(group.replace("-", "_").lower().split())


def _is_whole_layout_group(group: str) -> bool:
    normalized = _normalize_group(group)
    return normalized in WHOLE_LAYOUT_GROUPS


def _is_strobe_cue(cue: CueView) -> bool:
    haystack = f"{cue.kind} {cue.effect_family}".lower()
    return any(term in haystack for term in STROBE_EFFECT_TERMS)


def _is_major_cue(cue: CueView) -> bool:
    return cue.kind in MAJOR_CUE_KINDS or cue.intensity >= 0.9 or any(
        _is_whole_layout_group(group) for group in cue.target_groups
    )


def _is_whole_house_cue(cue: CueView) -> bool:
    return any(_is_whole_layout_group(group) for group in cue.target_groups)


def normalize_cue(raw: Mapping[str, object]) -> CueView:
    """Normalize a cue-like mapping into a CueView."""

    target_groups = raw.get("target_groups", ())
    if isinstance(target_groups, str):
        groups: Sequence[str] = (target_groups,)
    elif isinstance(target_groups, Iterable):
        groups = tuple(str(group) for group in target_groups)
    else:
        groups = ()

    return CueView(
        time=float(raw.get("time", 0.0)),
        kind=str(raw.get("kind", "unknown")),
        intensity=float(raw.get("intensity", 0.0)),
        target_groups=tuple(groups),
        effect_family=str(raw.get("effect_family", "")),
        section=str(raw["section"]) if raw.get("section") is not None else None,
        locked=bool(raw.get("locked", False)),
        source=str(raw.get("source", "planner")),
    )


def normalize_cues(raw_cues: Iterable[Mapping[str, object] | CueView]) -> list[CueView]:
    """Normalize cue-like mappings while preserving CueView objects."""

    normalized: list[CueView] = []
    for cue in raw_cues:
        if isinstance(cue, CueView):
            normalized.append(cue)
        else:
            normalized.append(normalize_cue(cue))
    return sorted(normalized, key=lambda item: item.time)


def score_restraint(
    raw_cues: Iterable[Mapping[str, object] | CueView],
    rules: RestraintRules | None = None,
) -> RestraintReport:
    """Score cue density and restraint without changing any render behavior."""

    active_rules = rules or RestraintRules()
    cues = normalize_cues(raw_cues)
    findings: list[RestraintFinding] = []

    major_cues = [cue for cue in cues if _is_major_cue(cue)]
    whole_house_cues = [cue for cue in cues if _is_whole_house_cue(cue)]
    strobe_cues = [cue for cue in cues if _is_strobe_cue(cue)]

    penalty = 0.0

    # Whole-house overuse by section. Unknown sections are grouped together so
    # callers still get useful warnings before section detection is integrated.
    whole_house_by_section: dict[str, list[CueView]] = {}
    for cue in whole_house_cues:
        whole_house_by_section.setdefault(cue.section or "unknown", []).append(cue)

    for section, section_cues in whole_house_by_section.items():
        overage = len(section_cues) - active_rules.max_whole_house_hits_per_section
        if overage > 0:
            section_penalty = min(0.35, 0.05 * overage)
            penalty += section_penalty
            findings.append(
                RestraintFinding(
                    code="whole_house_overuse",
                    severity="warning",
                    section=section,
                    penalty=section_penalty,
                    message=(
                        f"{len(section_cues)} whole-layout hits exceed limit "
                        f"{active_rules.max_whole_house_hits_per_section} in section '{section}'."
                    ),
                )
            )

    # Major-hit spacing.
    previous_major: CueView | None = None
    for cue in major_cues:
        if previous_major is not None:
            gap = cue.time - previous_major.time
            if gap < active_rules.min_seconds_between_major_hits:
                gap_penalty = min(0.2, 0.04 * (active_rules.min_seconds_between_major_hits - gap + 1.0))
                penalty += gap_penalty
                findings.append(
                    RestraintFinding(
                        code="major_hits_too_close",
                        severity="warning",
                        time=cue.time,
                        section=cue.section,
                        penalty=gap_penalty,
                        message=(
                            f"Major hit at {cue.time:.2f}s is only {gap:.2f}s after previous major hit."
                        ),
                    )
                )
        previous_major = cue

    # Simultaneous dominant group check. This treats one cue with too many target
    # groups as a readability risk.
    for cue in cues:
        if len(cue.target_groups) > active_rules.max_simultaneous_dominant_groups and cue.intensity >= 0.75:
            group_penalty = min(0.2, 0.03 * (len(cue.target_groups) - active_rules.max_simultaneous_dominant_groups))
            penalty += group_penalty
            findings.append(
                RestraintFinding(
                    code="too_many_dominant_groups",
                    severity="warning",
                    time=cue.time,
                    section=cue.section,
                    penalty=group_penalty,
                    message=(
                        f"Cue at {cue.time:.2f}s targets {len(cue.target_groups)} groups at high intensity."
                    ),
                )
            )

    # Strobe safety/readability check.
    for cue in strobe_cues:
        if not active_rules.allow_strobe:
            strobe_penalty = 0.1
            penalty += strobe_penalty
            findings.append(
                RestraintFinding(
                    code="strobe_disabled",
                    severity="warning",
                    time=cue.time,
                    section=cue.section,
                    penalty=strobe_penalty,
                    message=f"Strobe-like cue at {cue.time:.2f}s appears while strobe is disabled.",
                )
            )
        elif cue.intensity < active_rules.strobe_requires_intensity_at_least:
            strobe_penalty = 0.05
            penalty += strobe_penalty
            findings.append(
                RestraintFinding(
                    code="strobe_without_peak_energy",
                    severity="info",
                    time=cue.time,
                    section=cue.section,
                    penalty=strobe_penalty,
                    message=(
                        f"Strobe-like cue at {cue.time:.2f}s has intensity {cue.intensity:.2f}, below "
                        f"{active_rules.strobe_requires_intensity_at_least:.2f}."
                    ),
                )
            )

    density_penalty = min(1.0, penalty)
    score = max(0.0, round(1.0 - density_penalty, 4))

    return RestraintReport(
        cue_count=len(cues),
        major_hit_count=len(major_cues),
        whole_house_hit_count=len(whole_house_cues),
        strobe_count=len(strobe_cues),
        density_penalty=round(density_penalty, 4),
        score=score,
        findings=tuple(findings),
    )
