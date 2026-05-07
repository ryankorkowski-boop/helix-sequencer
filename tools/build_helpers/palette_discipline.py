"""Advisory palette-discipline scoring for Helix sequence planning.

This module is renderer-neutral. It does not render effects, write XSQ content,
mutate layouts, recolor existing effects, or promote/reject variants by itself.
It gives future reporting and shortlist logic a source-agnostic way to detect
color chaos, weak palette continuity, and style/palette mismatch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence


PALETTE_FAMILIES: dict[str, tuple[str, ...]] = {
    "classic_christmas": ("red", "green", "warm_white", "gold"),
    "classic_christmas_bright": ("red", "green", "white", "gold"),
    "classic_christmas_finale": ("red", "green", "white", "gold", "sparkle"),
    "winter_soft": ("blue", "cyan", "white", "silver"),
    "winter_bright": ("blue", "white", "cyan", "silver"),
    "warm_elegant": ("warm_white", "gold", "champagne", "amber"),
    "rock": ("red", "amber", "white", "blackout"),
    "edm_neon": ("cyan", "magenta", "purple", "blue", "white"),
    "comedy_bright": ("red", "green", "blue", "yellow", "pink", "white"),
    "spooky": ("orange", "purple", "green", "blackout"),
    "patriotic": ("red", "white", "blue"),
}

STYLE_ALLOWED_PALETTES: dict[str, tuple[str, ...]] = {
    "general": tuple(PALETTE_FAMILIES),
    "showcase": (
        "classic_christmas",
        "classic_christmas_bright",
        "classic_christmas_finale",
        "winter_soft",
        "winter_bright",
        "warm_elegant",
        "rock",
        "edm_neon",
        "patriotic",
    ),
    "vendor": (
        "classic_christmas",
        "classic_christmas_bright",
        "classic_christmas_finale",
        "winter_soft",
        "warm_elegant",
        "patriotic",
    ),
    "classic_christmas": (
        "classic_christmas",
        "classic_christmas_bright",
        "classic_christmas_finale",
        "warm_elegant",
    ),
    "edm": ("edm_neon", "winter_bright", "comedy_bright"),
    "rock": ("rock", "warm_elegant", "classic_christmas_bright"),
    "ballad": ("winter_soft", "warm_elegant", "classic_christmas"),
    "comedy": ("comedy_bright", "classic_christmas_bright", "edm_neon"),
    "spooky": ("spooky", "warm_elegant"),
    "patriotic": ("patriotic", "warm_elegant"),
}

CHAOS_TOLERANT_STYLES = {"edm", "comedy"}
CHAOS_TOLERANT_PALETTES = {"edm_neon", "comedy_bright"}


@dataclass(frozen=True)
class PaletteSectionView:
    """Normalized minimal section data used by palette scoring."""

    name: str
    kind: str = "unknown"
    palette: str = ""
    colors: tuple[str, ...] = field(default_factory=tuple)
    start: float = 0.0
    end: float = 0.0


@dataclass(frozen=True)
class PaletteFinding:
    """One advisory palette-discipline finding."""

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
class PaletteDisciplineReport:
    """Summarized advisory palette-discipline score."""

    section_count: int
    palette_count: int
    palette_consistency_score: float
    style_alignment_score: float
    color_churn_score: float
    motif_reuse_score: float
    score: float
    findings: tuple[PaletteFinding, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "section_count": self.section_count,
            "palette_count": self.palette_count,
            "palette_consistency_score": self.palette_consistency_score,
            "style_alignment_score": self.style_alignment_score,
            "color_churn_score": self.color_churn_score,
            "motif_reuse_score": self.motif_reuse_score,
            "score": self.score,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def _normalize_token(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (_normalize_token(value),)
    if isinstance(value, Iterable):
        return tuple(_normalize_token(str(item)) for item in value if str(item).strip())
    return ()


def normalize_palette_section(raw: Mapping[str, object] | PaletteSectionView) -> PaletteSectionView:
    """Normalize a section-like mapping while preserving PaletteSectionView objects."""

    if isinstance(raw, PaletteSectionView):
        return raw

    palette = _normalize_token(str(raw.get("palette", ""))) if raw.get("palette") else ""
    colors = _as_string_tuple(raw.get("colors"))
    if not colors and palette in PALETTE_FAMILIES:
        colors = PALETTE_FAMILIES[palette]

    return PaletteSectionView(
        name=str(raw.get("name", raw.get("kind", "unknown"))),
        kind=str(raw.get("kind", "unknown")),
        palette=palette,
        colors=colors,
        start=float(raw.get("start", 0.0)),
        end=float(raw.get("end", 0.0)),
    )


def normalize_palette_sections(
    raw_sections: Iterable[Mapping[str, object] | PaletteSectionView],
) -> list[PaletteSectionView]:
    """Normalize and sort sections by start time."""

    return sorted((normalize_palette_section(section) for section in raw_sections), key=lambda section: section.start)


def _jaccard_similarity(left: Sequence[str], right: Sequence[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    union = left_set | right_set
    if not union:
        return 1.0
    return len(left_set & right_set) / len(union)


def _score_palette_consistency(
    sections: Sequence[PaletteSectionView],
    findings: list[PaletteFinding],
) -> float:
    if not sections:
        findings.append(
            PaletteFinding(
                code="no_sections",
                severity="warning",
                message="No sections were provided, so palette discipline cannot be measured.",
                penalty=1.0,
            )
        )
        return 0.0

    missing_penalty = 0.0
    for section in sections:
        if not section.palette and not section.colors:
            missing_penalty += 0.12
            findings.append(
                PaletteFinding(
                    code="missing_palette_intent",
                    severity="warning",
                    section=section.name,
                    penalty=0.12,
                    message=f"Section '{section.name}' has no palette or color intent.",
                )
            )

    palette_names = [section.palette for section in sections if section.palette]
    unique_palettes = set(palette_names)

    churn_penalty = 0.0
    if len(unique_palettes) > max(2, len(sections) // 2 + 1):
        churn_penalty = min(0.3, 0.05 * (len(unique_palettes) - 2))
        findings.append(
            PaletteFinding(
                code="too_many_palettes",
                severity="warning",
                penalty=churn_penalty,
                message=(
                    f"Plan uses {len(unique_palettes)} distinct palettes across {len(sections)} sections; "
                    "this may read as color churn unless stylistically intentional."
                ),
            )
        )

    return round(max(0.0, 1.0 - min(1.0, missing_penalty + churn_penalty)), 4)


def _score_style_alignment(
    sections: Sequence[PaletteSectionView],
    style: str,
    findings: list[PaletteFinding],
) -> float:
    if not sections:
        return 0.0

    normalized_style = _normalize_token(style or "general")
    allowed = STYLE_ALLOWED_PALETTES.get(normalized_style, STYLE_ALLOWED_PALETTES["general"])
    mismatches = 0
    palette_sections = 0

    for section in sections:
        if not section.palette:
            continue
        palette_sections += 1
        if section.palette not in allowed:
            mismatches += 1
            findings.append(
                PaletteFinding(
                    code="palette_style_mismatch",
                    severity="info",
                    section=section.name,
                    penalty=0.08,
                    message=(
                        f"Section '{section.name}' uses palette '{section.palette}', which is not in "
                        f"the usual allowed set for style '{normalized_style}'."
                    ),
                )
            )

    if palette_sections == 0:
        return 0.0
    return round(max(0.0, 1.0 - (mismatches / palette_sections)), 4)


def _score_color_churn(
    sections: Sequence[PaletteSectionView],
    style: str,
    findings: list[PaletteFinding],
) -> float:
    if len(sections) < 2:
        return 1.0 if sections else 0.0

    normalized_style = _normalize_token(style or "general")
    tolerant = normalized_style in CHAOS_TOLERANT_STYLES
    similarities = []
    abrupt_changes = 0

    for left, right in zip(sections, sections[1:]):
        similarity = _jaccard_similarity(left.colors, right.colors)
        similarities.append(similarity)
        palette_tolerant = left.palette in CHAOS_TOLERANT_PALETTES or right.palette in CHAOS_TOLERANT_PALETTES
        if similarity < 0.2 and not tolerant and not palette_tolerant:
            abrupt_changes += 1
            findings.append(
                PaletteFinding(
                    code="abrupt_color_family_change",
                    severity="warning",
                    section=right.name,
                    penalty=0.08,
                    message=(
                        f"Section '{right.name}' changes color family sharply from the previous section."
                    ),
                )
            )

    if not similarities:
        return 1.0

    average_similarity = sum(similarities) / len(similarities)
    # Good discipline allows contrast while avoiding constant unrelated color
    # resets. Scores peak when adjacent sections retain at least some continuity.
    base = 0.75 + (0.25 * min(1.0, average_similarity / 0.35))
    if tolerant:
        base = max(base, 0.85)
    return round(max(0.0, min(1.0, base - (0.08 * abrupt_changes))), 4)


def _score_motif_reuse(sections: Sequence[PaletteSectionView], findings: list[PaletteFinding]) -> float:
    if not sections:
        return 0.0

    sections_by_kind: dict[str, list[PaletteSectionView]] = {}
    for section in sections:
        sections_by_kind.setdefault(section.kind, []).append(section)

    repeated_kinds = {kind: items for kind, items in sections_by_kind.items() if len(items) > 1}
    if not repeated_kinds:
        return 0.85

    kind_scores: list[float] = []
    for kind, items in repeated_kinds.items():
        first = items[0]
        similarities = [_jaccard_similarity(first.colors, item.colors) for item in items[1:]]
        kind_score = sum(similarities) / len(similarities) if similarities else 1.0
        kind_scores.append(kind_score)
        if kind_score < 0.35:
            findings.append(
                PaletteFinding(
                    code="weak_recurring_section_palette_motif",
                    severity="info",
                    penalty=0.08,
                    message=(
                        f"Repeated section kind '{kind}' does not reuse much palette/color identity."
                    ),
                )
            )

    return round(min(1.0, max(0.0, sum(kind_scores) / len(kind_scores))), 4)


def score_palette_discipline(
    raw_sections: Iterable[Mapping[str, object] | PaletteSectionView],
    style: str = "general",
) -> PaletteDisciplineReport:
    """Score whether planned sections have readable palette discipline."""

    sections = normalize_palette_sections(raw_sections)
    findings: list[PaletteFinding] = []

    palette_consistency_score = _score_palette_consistency(sections, findings)
    style_alignment_score = _score_style_alignment(sections, style, findings)
    color_churn_score = _score_color_churn(sections, style, findings)
    motif_reuse_score = _score_motif_reuse(sections, findings)

    palette_count = len({section.palette for section in sections if section.palette})
    score = round(
        (0.3 * palette_consistency_score)
        + (0.25 * style_alignment_score)
        + (0.25 * color_churn_score)
        + (0.2 * motif_reuse_score),
        4,
    )

    return PaletteDisciplineReport(
        section_count=len(sections),
        palette_count=palette_count,
        palette_consistency_score=palette_consistency_score,
        style_alignment_score=style_alignment_score,
        color_churn_score=color_churn_score,
        motif_reuse_score=motif_reuse_score,
        score=score,
        findings=tuple(findings),
    )
