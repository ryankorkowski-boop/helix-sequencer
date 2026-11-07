"""Conservative source ownership for pitched performance cues.

Unknown sources are deliberately not assigned to a performer. This module is
opt-in until end-to-end production parity and source-quality tests are complete.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

Performer = Literal["bassist", "guitarist", "keyboardist", "lead_singer", "harmony_singer"]
Origin = Literal["detected", "estimated", "fallback"]


@dataclass(frozen=True)
class SourceOwnership:
    performer: Performer | None
    confidence: float
    origin: Origin
    source_id: str = ""

    def __post_init__(self) -> None:
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.origin not in ("detected", "estimated", "fallback"):
            raise ValueError("invalid provenance origin")
        if self.performer not in (None, "bassist", "guitarist", "keyboardist", "lead_singer", "harmony_singer"):
            raise ValueError("invalid performer")
        if self.origin == "fallback" and self.performer is not None:
            raise ValueError("fallback cannot assert performer identity")

    def permitted(self, threshold: float = 0.7) -> bool:
        if not isfinite(threshold) or not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        return (
            self.performer is not None
            and self.origin != "fallback"
            and self.confidence >= threshold
        )


def resolve_owner(
    detected: SourceOwnership | None,
    estimated: SourceOwnership | None = None,
    *,
    threshold: float = 0.7,
) -> SourceOwnership:
    """Prefer reliable detected ownership; never promote unknown to keyboard.

    Estimates may be used only when they independently meet the confidence gate.
    This deliberately does not infer an instrument from pitch alone.
    """
    if not isfinite(threshold) or not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be finite and between 0 and 1")
    if detected is not None and detected.origin == "detected" and detected.permitted(threshold):
        return detected
    if estimated is not None and estimated.origin == "estimated" and estimated.permitted(threshold):
        return estimated
    return SourceOwnership(None, 0.0, "fallback")


def ownership_from_stem(source_stem: str, confidence: float) -> SourceOwnership:
    """Map only explicitly instrument-labeled stems, not generic pitched audio.

    A stem label is evidence of routing intent, not independently verified
    acoustic source identity; therefore its provenance is estimated.
    """
    normalized = str(source_stem or "").strip().lower().replace("-", "_")
    mapping: dict[str, Performer] = {
        "bass": "bassist",
        "bass_guitar": "bassist",
        "electric_bass": "bassist",
        "guitar": "guitarist",
        "electric_guitar": "guitarist",
        "acoustic_guitar": "guitarist",
        "piano": "keyboardist",
        "keyboard": "keyboardist",
        "keys": "keyboardist",
        "synth": "keyboardist",
    }
    performer = mapping.get(normalized)
    if performer is None:
        return SourceOwnership(None, 0.0, "fallback", source_id=normalized)
    try:
        bounded_confidence = float(confidence)
    except (TypeError, ValueError):
        bounded_confidence = 0.0
    if not isfinite(bounded_confidence):
        bounded_confidence = 0.0
    return SourceOwnership(performer, max(0.0, min(1.0, bounded_confidence)), "estimated", source_id=normalized)
