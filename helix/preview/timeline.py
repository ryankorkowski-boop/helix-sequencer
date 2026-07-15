"""Timeline primitives for Helix preview rendering."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class TimelineEvent:
    """A scheduled visual event."""

    time_ms: int
    action: str
    payload: dict[str, Any] = field(default_factory=dict, compare=False)


class Timeline:
    """Simple ordered event timeline."""

    def __init__(self) -> None:
        self.events: list[TimelineEvent] = []

    def add(self, event: TimelineEvent) -> None:
        self.events.append(event)
        self.events.sort()

    def at(self, time_ms: int) -> list[TimelineEvent]:
        return [e for e in self.events if e.time_ms == time_ms]

    def between(self, start_ms: int, end_ms: int) -> list[TimelineEvent]:
        return [e for e in self.events if start_ms <= e.time_ms <= end_ms]
