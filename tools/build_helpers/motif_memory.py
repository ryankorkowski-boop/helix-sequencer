"""Advisory motif-memory scoring for Helix sequence planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

MOTIF_FAMILIES = {"spiral", "sweep", "pulse", "burst", "shimmer", "sparkle", "strobe", "wash", "chase", "vocal", "percussion", "call_response", "finale_cascade"}
RECURRING_SECTION_KINDS = {"chorus", "verse", "drop", "bridge", "solo", "refrain"}


@dataclass(frozen=True)
class MotifView:
    name: str
    section: str = ""
    section_kind: str = "unknown"
    family: str = "unknown"
    palette: str = ""
    primary_groups: tuple[str, ...] = field(default_factory=tuple)
    effect_family: str = ""
    intensity_range: tuple[float, float] = (0.0, 1.0)
    start: float = 0.0
    end: float = 0.0
    variation: str = ""

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def identity_key(self) -> tuple[str, str, str]:
        primary = self.primary_groups[0] if self.primary_groups else ""
        family = self.family if self.family != "unknown" else self.effect_family
        return (family, self.palette, primary)


@dataclass(frozen=True)
class MotifFinding:
    code: str
    severity: str
    message: str
    motif: str | None = None
    section: str | None = None
    penalty: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "severity": self.severity, "message": self.message, "motif": self.motif, "section": self.section, "penalty": self.penalty}


@dataclass(frozen=True)
class MotifMemoryReport:
    motif_count: int
    recurring_section_kind_count: int
    identity_reuse_score: float
    variation_score: float
    coverage_score: float
    overfragmentation_score: float
    score: float
    findings: tuple[MotifFinding, ...]

    def as_dict(self) -> dict[str, object]:
        return {"motif_count": self.motif_count, "recurring_section_kind_count": self.recurring_section_kind_count, "identity_reuse_score": self.identity_reuse_score, "variation_score": self.variation_score, "coverage_score": self.coverage_score, "overfragmentation_score": self.overfragmentation_score, "score": self.score, "findings": [finding.as_dict() for finding in self.findings]}


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


def _normalize_family(value: str) -> str:
    token = _normalize_token(value)
    for family in MOTIF_FAMILIES:
        if family in token:
            return family
    return token or "unknown"


def normalize_motif(raw: Mapping[str, object] | MotifView) -> MotifView:
    if isinstance(raw, MotifView):
        return raw
    intensity_range_raw = raw.get("intensity_range", (0.0, 1.0))
    if isinstance(intensity_range_raw, Sequence) and not isinstance(intensity_range_raw, str) and len(intensity_range_raw) >= 2:
        intensity_range = (float(intensity_range_raw[0]), float(intensity_range_raw[1]))
    else:
        intensity = float(raw.get("intensity", 0.5))
        intensity_range = (max(0.0, intensity - 0.1), min(1.0, intensity + 0.1))
    family_source = str(raw.get("family", raw.get("effect_family", "unknown")))
    return MotifView(name=str(raw.get("name", raw.get("motif_name", "unnamed_motif"))), section=str(raw.get("section", raw.get("section_name", ""))), section_kind=_normalize_token(str(raw.get("section_kind", raw.get("kind", "unknown")))), family=_normalize_family(family_source), palette=_normalize_token(str(raw.get("palette", ""))) if raw.get("palette") else "", primary_groups=_as_string_tuple(raw.get("primary_groups", raw.get("target_groups"))), effect_family=_normalize_family(str(raw.get("effect_family", family_source))), intensity_range=intensity_range, start=float(raw.get("start", raw.get("time", 0.0))), end=float(raw.get("end", raw.get("time", 0.0))), variation=str(raw.get("variation", "")))


def normalize_motifs(raw_motifs: Iterable[Mapping[str, object] | MotifView]) -> list[MotifView]:
    return sorted((normalize_motif(motif) for motif in raw_motifs), key=lambda motif: motif.start)


def _similarity(left: MotifView, right: MotifView) -> float:
    score = 0.0
    if left.family == right.family:
        score += 0.35
    if left.palette and left.palette == right.palette:
        score += 0.25
    if left.primary_groups and right.primary_groups and set(left.primary_groups) & set(right.primary_groups):
        score += 0.25
    if abs((sum(left.intensity_range) / 2.0) - (sum(right.intensity_range) / 2.0)) <= 0.2:
        score += 0.15
    return min(1.0, score)


def _score_coverage(motifs: Sequence[MotifView], findings: list[MotifFinding]) -> float:
    if not motifs:
        findings.append(MotifFinding(code="no_motifs", severity="warning", message="No motifs were provided, so motif memory cannot be measured.", penalty=1.0))
        return 0.0
    penalty = 0.0
    for motif in motifs:
        if not motif.section_kind or motif.section_kind == "unknown":
            penalty += 0.06
            findings.append(MotifFinding(code="motif_missing_section_kind", severity="warning", message="Motif is missing a usable section kind.", motif=motif.name, penalty=0.06))
        if motif.family == "unknown" and not motif.effect_family:
            penalty += 0.08
            findings.append(MotifFinding(code="motif_missing_family", severity="warning", message="Motif is missing a usable family or effect family.", motif=motif.name, penalty=0.08))
        if not motif.primary_groups:
            penalty += 0.06
            findings.append(MotifFinding(code="motif_missing_groups", severity="warning", message="Motif is missing primary target groups.", motif=motif.name, penalty=0.06))
    return round(max(0.0, 1.0 - min(1.0, penalty)), 4)


def _group_by_section_kind(motifs: Sequence[MotifView]) -> dict[str, list[MotifView]]:
    grouped: dict[str, list[MotifView]] = {}
    for motif in motifs:
        grouped.setdefault(motif.section_kind or "unknown", []).append(motif)
    return grouped


def _score_identity_reuse(motifs: Sequence[MotifView], findings: list[MotifFinding]) -> tuple[float, int]:
    grouped = _group_by_section_kind(motifs)
    recurring = {kind: items for kind, items in grouped.items() if len(items) > 1 and (kind in RECURRING_SECTION_KINDS or kind != "unknown")}
    if not recurring:
        findings.append(MotifFinding(code="no_recurring_motif_sections", severity="info", message="No repeated section kinds with motifs were found; motif reuse cannot be strongly evaluated.", penalty=0.1))
        return (0.75 if motifs else 0.0, 0)
    scores = []
    for items in recurring.values():
        first = items[0]
        similarities = [_similarity(first, item) for item in items[1:]]
        scores.append(sum(similarities) / len(similarities) if similarities else 1.0)
    score = round(sum(scores) / len(scores), 4)
    if score < 0.45:
        findings.append(MotifFinding(code="weak_motif_reuse", severity="warning", message="Repeated section kinds do not reuse enough visual identity.", penalty=0.12))
    return (score, len(recurring))


def _intensity_overlap(left: MotifView, right: MotifView) -> float:
    lo = max(left.intensity_range[0], right.intensity_range[0])
    hi = min(left.intensity_range[1], right.intensity_range[1])
    span = max(left.intensity_range[1], right.intensity_range[1]) - min(left.intensity_range[0], right.intensity_range[0])
    return 0.0 if hi <= lo or span <= 0 else (hi - lo) / span


def _score_variation(motifs: Sequence[MotifView], findings: list[MotifFinding]) -> float:
    recurring = {kind: items for kind, items in _group_by_section_kind(motifs).items() if len(items) > 1}
    if not recurring:
        return 0.75 if motifs else 0.0
    scores = []
    for kind, items in recurring.items():
        pair_scores = []
        for left, right in zip(items, items[1:]):
            near_copy = left.family == right.family and left.palette == right.palette and set(left.primary_groups) == set(right.primary_groups) and _intensity_overlap(left, right) >= 0.8 and left.variation == right.variation
            if near_copy:
                pair_scores.append(0.4)
            else:
                pair_scores.append(min(1.0, 1.0 - (0.45 * _similarity(left, right)) + (0.2 if right.variation and right.variation != left.variation else 0.0)))
        raw_score = sum(pair_scores) / len(pair_scores) if pair_scores else 0.75
        scores.append(raw_score)
        if raw_score < 0.55:
            findings.append(MotifFinding(code="motif_repeats_without_variation", severity="info", section=kind, penalty=0.08, message=f"Repeated section kind '{kind}' reuses motif identity with little variation."))
    return round(sum(scores) / len(scores), 4)


def _score_overfragmentation(motifs: Sequence[MotifView], findings: list[MotifFinding]) -> float:
    if not motifs:
        return 0.0
    ratio = len({motif.identity_key for motif in motifs}) / len(motifs)
    score = round(max(0.0, min(1.0, 1.15 - ratio)), 4)
    if score < 0.5 and len(motifs) >= 4:
        findings.append(MotifFinding(code="motif_overfragmentation", severity="warning", message="Motifs are too fragmented to establish recurring visual identity.", penalty=0.12))
    return score


def score_motif_memory(raw_motifs: Iterable[Mapping[str, object] | MotifView]) -> MotifMemoryReport:
    motifs = normalize_motifs(raw_motifs)
    findings: list[MotifFinding] = []
    coverage_score = _score_coverage(motifs, findings)
    identity_reuse_score, recurring_count = _score_identity_reuse(motifs, findings)
    variation_score = _score_variation(motifs, findings)
    overfragmentation_score = _score_overfragmentation(motifs, findings)
    score = round((0.25 * coverage_score) + (0.35 * identity_reuse_score) + (0.2 * variation_score) + (0.2 * overfragmentation_score), 4)
    return MotifMemoryReport(motif_count=len(motifs), recurring_section_kind_count=recurring_count, identity_reuse_score=identity_reuse_score, variation_score=variation_score, coverage_score=coverage_score, overfragmentation_score=overfragmentation_score, score=score, findings=tuple(findings))
