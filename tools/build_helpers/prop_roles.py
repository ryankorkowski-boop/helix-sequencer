"""Advisory prop-role inference for Helix sequence planning.

This module is intentionally renderer-neutral. It does not change effect placement,
write XSQ data, or mutate layouts. It gives the existing engine and future scoring
layers a small, source-agnostic vocabulary for understanding what a model is good
at based on its name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class PropRoleHint:
    """A lightweight role hint for a layout model or group name."""

    name: str
    role: str
    best_for: tuple[str, ...] = field(default_factory=tuple)
    energy_capacity: str = "medium"
    confidence: float = 0.5
    matched_terms: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "role": self.role,
            "best_for": list(self.best_for),
            "energy_capacity": self.energy_capacity,
            "confidence": self.confidence,
            "matched_terms": list(self.matched_terms),
        }


# Ordered from most specific to broadest. The first confident match wins.
ROLE_RULES: tuple[dict[str, object], ...] = (
    {
        "terms": ("snowman singer", "singer", "singing face", "face"),
        "role": "singer",
        "best_for": ("vocals", "lyric_phrases", "call_and_response"),
        "energy_capacity": "medium",
    },
    {
        "terms": ("drummer", "drum", "percussion"),
        "role": "percussion",
        "best_for": ("drum_hits", "downbeats", "rhythmic_accents"),
        "energy_capacity": "medium",
    },
    {
        "terms": ("guitarist", "guitar", "bassist", "bass"),
        "role": "character",
        "best_for": ("rhythm", "bass_pulses", "call_and_response"),
        "energy_capacity": "medium",
    },
    {
        "terms": ("mega tree", "megatree", "tree 360", "spiral tree"),
        "role": "centerpiece",
        "best_for": ("spirals", "bursts", "color_washes", "finale"),
        "energy_capacity": "high",
    },
    {
        "terms": ("roofline", "roof line", "house outline", "outline", "eaves"),
        "role": "outline",
        "best_for": ("sweeps", "structure", "section_identity"),
        "energy_capacity": "medium",
    },
    {
        "terms": ("arch", "arches"),
        "role": "accent",
        "best_for": ("chases", "rhythm", "motion"),
        "energy_capacity": "medium",
    },
    {
        "terms": ("mini tree", "minitree", "mini-tree"),
        "role": "accent",
        "best_for": ("fills", "sparkles", "section_support"),
        "energy_capacity": "medium",
    },
    {
        "terms": ("strobe", "strobes", "flood", "blinder"),
        "role": "strobe",
        "best_for": ("high_energy_hits", "finale", "accent_punctuation"),
        "energy_capacity": "high",
    },
    {
        "terms": ("snowman", "coro", "character", "prop"),
        "role": "character",
        "best_for": ("foreground_motion", "novelty", "call_and_response"),
        "energy_capacity": "medium",
    },
    {
        "terms": ("matrix", "panel", "screen"),
        "role": "background",
        "best_for": ("textures", "visual_backdrop", "color_fields"),
        "energy_capacity": "high",
    },
    {
        "terms": ("whole house", "whole layout", "all models", "everything"),
        "role": "foreground",
        "best_for": ("major_hits", "transitions", "finale"),
        "energy_capacity": "high",
    },
)

DEFAULT_HINT = {
    "role": "fill",
    "best_for": ("support", "background_fill"),
    "energy_capacity": "low",
}


def _normalize_name(name: str) -> str:
    return " ".join(name.replace("_", " ").replace("-", " ").lower().split())


def infer_prop_role(name: str) -> PropRoleHint:
    """Infer an advisory role from a model/group name.

    The result is only a hint. Callers should treat it as scoring/planning input,
    not as a hard routing command.
    """

    normalized = _normalize_name(name)
    for rule in ROLE_RULES:
        terms = tuple(rule["terms"])  # type: ignore[arg-type]
        matched = tuple(term for term in terms if term in normalized)
        if matched:
            return PropRoleHint(
                name=name,
                role=str(rule["role"]),
                best_for=tuple(rule["best_for"]),  # type: ignore[arg-type]
                energy_capacity=str(rule["energy_capacity"]),
                confidence=min(0.95, 0.65 + (0.1 * len(matched))),
                matched_terms=matched,
            )

    return PropRoleHint(
        name=name,
        role=str(DEFAULT_HINT["role"]),
        best_for=tuple(DEFAULT_HINT["best_for"]),  # type: ignore[arg-type]
        energy_capacity=str(DEFAULT_HINT["energy_capacity"]),
        confidence=0.25,
        matched_terms=(),
    )


def infer_prop_roles(names: Iterable[str]) -> list[PropRoleHint]:
    """Infer advisory role hints for multiple model/group names."""

    return [infer_prop_role(name) for name in names]


def summarize_roles(names: Iterable[str]) -> dict[str, list[dict[str, object]]]:
    """Group inferred hints by role for simple reports and future scoring."""

    grouped: dict[str, list[dict[str, object]]] = {}
    for hint in infer_prop_roles(names):
        grouped.setdefault(hint.role, []).append(hint.as_dict())
    return grouped
