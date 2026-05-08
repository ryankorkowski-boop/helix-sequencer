"""Report-only showcase palette-arc metrics.

These metrics operate only on synthetic, internal, or permissioned section traces.
They measure cinematic color progression (warm/cool drift, palette continuity,
contrast rhythm) without ingesting third-party copyrighted material.

This module is report-only and does not influence generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


WARM_COLORS = {"red", "orange", "amber", "warm_white", "pink"}
COOL_COLORS = {"blue", "cyan", "green", "teal", "cool_white", "purple"}
NEUTRAL_COLORS = {"white", "soft_white", "gold"}


@dataclass(frozen=True)
class PaletteSectionTrace:
    name: str
    kind: str = "unknown"
    start: float = 0.0
    end: float = 0.0
    colors: tuple[str, ...] = ()
    palette: str = ""
    contrast_level: float = 0.5  # 0..1

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "start": self.start,
            "end": self.end,
            "colors": list(self.colors),
            "palette": self.palette,
            "contrast_level": self.contrast_level,
        }


@dataclass(frozen=True)
class PaletteArcFinding:
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
class PaletteArcReport:
    section_count: int
    warm_cool_flow_score: float
    palette_continuity_score: float
    contrast_rhythm_score: float
    abrupt_palette_shift_penalty: float
    showcase_palette_score: float
    raw_metrics: dict[str, float] = field(default_factory=dict)
    findings: tuple[PaletteArcFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "section_count": self.section_count,
            "warm_cool_flow_score": self.warm_cool_flow_score,
            "palette_continuity_score": self.palette_continuity_score,
            "contrast_rhythm_score": self.contrast_rhythm_score,
            "abrupt_palette_shift_penalty": self.abrupt_palette_shift_penalty,
            "showcase_palette_score": self.showcase_palette_score,
            "raw_metrics": self.raw_metrics,
            "findings": [f.as_dict() for f in self.findings],
        }


def score_palette_arc(raw_sections: Iterable[Mapping[str, object] | PaletteSectionTrace]) -> PaletteArcReport:
    sections = sorted((normalize_section(s) for s in raw_sections), key=lambda s: s.start)
    findings: list[PaletteArcFinding] = []

    if not sections:
        finding = PaletteArcFinding(
            code="no_palette_sections",
            severity="warning",
            message="No section traces were provided for palette arc analysis.",
            penalty=1.0,
        )
        return PaletteArcReport(
            section_count=0,
            warm_cool_flow_score=0.0,
            palette_continuity_score=0.0,
            contrast_rhythm_score=0.0,
            abrupt_palette_shift_penalty=1.0,
            showcase_palette_score=0.0,
            findings=(finding,),
        )

    warm_cool_flow_score = _score_warm_cool_flow(sections, findings)
    palette_continuity_score = _score_palette_continuity(sections, findings)
    contrast_rhythm_score = _score_contrast_rhythm(sections, findings)
    abrupt_palette_shift_penalty = _score_abrupt_shifts(sections, findings)

    showcase_palette_score = round(
        max(
            0.0,
            (0.3 * warm_cool_flow_score)
            + (0.3 * palette_continuity_score)
            + (0.25 * contrast_rhythm_score)
            + (0.15 * (1.0 - abrupt_palette_shift_penalty)),
        ),
        4,
    )

    return PaletteArcReport(
        section_count=len(sections),
        warm_cool_flow_score=warm_cool_flow_score,
        palette_continuity_score=palette_continuity_score,
        contrast_rhythm_score=contrast_rhythm_score,
        abrupt_palette_shift_penalty=abrupt_palette_shift_penalty,
        showcase_palette_score=showcase_palette_score,
        raw_metrics={
            "unique_palettes": float(len({s.palette for s in sections if s.palette})),
            "avg_contrast": round(sum(s.contrast_level for s in sections) / len(sections), 4),
        },
        findings=tuple(findings),
    )


def normalize_section(raw: Mapping[str, object] | PaletteSectionTrace) -> PaletteSectionTrace:
    if isinstance(raw, PaletteSectionTrace):
        return raw

    colors = raw.get("colors") or []
    return PaletteSectionTrace(
        name=str(raw.get("name", "unnamed_section")),
        kind=str(raw.get("kind", "unknown")),
        start=float(raw.get("start", 0.0)),
        end=float(raw.get("end", 0.0)),
        colors=tuple(str(c).lower() for c in colors),
        palette=str(raw.get("palette", "")),
        contrast_level=_clamp01(float(raw.get("contrast_level", 0.5))),
    )


def _temperature_score(section: PaletteSectionTrace) -> float:
    warm = sum(1 for c in section.colors if c in WARM_COLORS)
    cool = sum(1 for c in section.colors if c in COOL_COLORS)
    total = warm + cool
    if total == 0:
        return 0.5
    return warm / total  # 0=cool heavy, 1=warm heavy


def _score_warm_cool_flow(sections, findings):
    if len(sections) < 2:
        return 0.8

    deltas = []
    prev = _temperature_score(sections[0])
    for s in sections[1:]:
        current = _temperature_score(s)
        deltas.append(abs(current - prev))
        prev = current

    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0
    score = max(0.0, 1.0 - avg_delta)
    if avg_delta > 0.6:
        findings.append(
            PaletteArcFinding(
                code="extreme_warm_cool_swings",
                severity="info",
                message="Large warm/cool swings between sections detected.",
                penalty=0.1,
            )
        )
    return round(score, 4)


def _score_palette_continuity(sections, findings):
    if len(sections) < 2:
        return 0.8

    continuity = 0
    total = 0
    for a, b in zip(sections, sections[1:]):
        total += 1
        if a.palette and a.palette == b.palette:
            continuity += 1
        elif set(a.colors) & set(b.colors):
            continuity += 0.5
        else:
            findings.append(
                PaletteArcFinding(
                    code="palette_reset",
                    severity="info",
                    message=f"Palette reset between '{a.name}' and '{b.name}'.",
                    penalty=0.05,
                )
            )
    return round(continuity / total if total else 1.0, 4)


def _score_contrast_rhythm(sections, findings):
    contrasts = [s.contrast_level for s in sections]
    if not contrasts:
        return 0.0

    variation = max(contrasts) - min(contrasts)
    score = min(1.0, variation + 0.3)  # reward dynamic range
    return round(score, 4)


def _score_abrupt_shifts(sections, findings):
    penalty_count = 0
    total = 0
    for a, b in zip(sections, sections[1:]):
        total += 1
        temp_delta = abs(_temperature_score(a) - _temperature_score(b))
        if temp_delta > 0.75 and not (set(a.colors) & set(b.colors)):
            penalty_count += 1
            findings.append(
                PaletteArcFinding(
                    code="abrupt_palette_shift",
                    severity="warning",
                    message=f"Abrupt palette shift between '{a.name}' and '{b.name}'.",
                    penalty=0.1,
                )
            )
    return round(penalty_count / total if total else 0.0, 4)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
