"""Standalone snare artifact component."""

from dataclasses import dataclass

from helix.preview.timeline import TimelineEvent


@dataclass
class Snare:
    target: str = "ARCHES"
    threshold: float = 0.55

    def react(self, time_ms: int, confidence: float) -> TimelineEvent | None:
        if confidence < self.threshold:
            return None
        return TimelineEvent(
            start_ms=time_ms,
            duration_ms=100,
            target=self.target,
            effect="snare_hit",
            intensity=min(confidence, 1.0),
            metadata={
                "artifact": "drummer",
                "component": "snare",
            },
        )
