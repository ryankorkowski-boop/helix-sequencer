from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class MusicalEvent:
    """Renderer-neutral musical event produced by audio intelligence."""

    time_ms: int
    kind: str
    confidence: float
    strength: float = 0.0
    source: str = "helix_audio"
    instrument: str | None = None
    duration_ms: int = 0
    pitch_midi: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = round(clamp01(self.confidence), 4)
        payload["strength"] = round(clamp01(self.strength), 4)
        return payload


@dataclass
class MusicalEventMap:
    """Normalized event collection shared by sequencer consumers."""

    duration_ms: int
    events: list[MusicalEvent] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def add(self, event: MusicalEvent) -> None:
        self.events.append(event)

    def sort(self) -> None:
        self.events.sort(key=lambda event: (event.time_ms, event.kind, -event.confidence))

    def by_kind(self, kind: str) -> list[MusicalEvent]:
        return [event for event in self.events if event.kind == kind]

    def high_confidence(self, threshold: float = 0.7) -> list[MusicalEvent]:
        threshold = clamp01(threshold)
        return [event for event in self.events if event.confidence >= threshold]

    def to_dict(self) -> dict[str, Any]:
        self.sort()
        return {
            "schema": "helix.musical_event_map.v1",
            "duration_ms": int(self.duration_ms),
            "providers": list(self.providers),
            "events": [event.to_dict() for event in self.events],
            "diagnostics": dict(self.diagnostics),
        }
