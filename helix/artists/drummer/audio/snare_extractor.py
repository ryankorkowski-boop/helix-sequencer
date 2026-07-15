"""Snare stem adapter.

Consumes separated audio features. Actual DSP backends (librosa,
Demucs, etc.) can plug in later.
"""

from dataclasses import dataclass


@dataclass
class SnareHit:
    time_ms: int
    confidence: float


class SnareExtractor:
    def extract(self, stem_events: list[dict]) -> list[SnareHit]:
        return [
            SnareHit(
                time_ms=int(event["time_ms"]),
                confidence=float(event.get("confidence", 0.0)),
            )
            for event in stem_events
            if event.get("stem") == "snare"
        ]
