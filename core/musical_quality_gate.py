"""Opt-in musical-storytelling quality gates.

These metrics are only scored when the producer supplies explicit, auditable
evidence. Missing evidence is not treated as proof of musical quality.
"""
from __future__ import annotations

from typing import Any

METRIC_NAMES = (
    "section_differentiation",
    "phrase_fidelity",
    "instrument_ownership",
    "meaningful_silence",
    "theme_recurrence",
)


def evaluate_storytelling(evidence: dict[str, Any]) -> dict[str, float | None]:
    """Normalize explicit [0, 1] observations; return None for unknown."""
    result: dict[str, float | None] = {}
    for name in METRIC_NAMES:
        raw = evidence.get(name)
        if raw is None or isinstance(raw, bool):
            result[name] = None
            continue
        try:
            value = float(raw)
        except (ValueError, TypeError):
            result[name] = None
            continue
        result[name] = value if 0.0 <= value <= 1.0 else None
    return result


def storytelling_gate(
    evidence: dict[str, Any],
    *,
    minimum: float = 0.55,
    require_complete: bool = True,
) -> tuple[bool, dict[str, float | None]]:
    """Reject low-quality or unverified candidates without changing legacy scoring."""
    if not 0.0 <= minimum <= 1.0:
        raise ValueError("minimum must be between zero and one")
    scores = evaluate_storytelling(evidence)
    if require_complete and any(value is None for value in scores.values()):
        return False, scores
    known = [value for value in scores.values() if value is not None]
    if not known:
        return False, scores
    return min(known) >= minimum, scores
