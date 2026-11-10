"""Event timeline primitives for Helix preview rendering."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class PreviewEvent:
    """A synchronized animation event.

    Payload may contain instrument-specific information such as:
    {"instrument": "kick", "strength": 0.92}
    """

    time: float
    action: str
    payload: dict[str, Any] = field(default_factory=dict, compare=False)
    strength: float = field(default=1.0, compare=False)
    instrument: str = field(default="generic", compare=False)

    def __post_init__(self) -> None:
        if "strength" in self.payload:
            self.strength = float(self.payload["strength"])
        if "instrument" in self.payload:
            self.instrument = str(self.payload["instrument"])


class PreviewTimeline:
    """Stores and queries ordered preview events."""

    def __init__(self) -> None:
        self.events: list[PreviewEvent] = []

    def add(self, event: PreviewEvent) -> None:
        self.events.append(event)
        self.events.sort()

    def active_at(self, timestamp: float) -> list[PreviewEvent]:
        return [e for e in self.events if e.time <= timestamp]
