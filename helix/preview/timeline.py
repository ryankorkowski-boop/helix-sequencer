"""Timeline primitives used by preview engines."""

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(order=True)
class TimelineEvent:
    """A scheduled visual event."""

    start_ms: int
    duration_ms: int = 100
    target: str = "10_WHOLE_HOUSE"
    effect: str = "on"
    intensity: float = 1.0
    metadata: dict = field(default_factory=dict, compare=False)

    def active(self, timestamp_ms: int) -> bool:
        return self.start_ms <= timestamp_ms < self.start_ms + self.duration_ms


@dataclass
class Timeline:
    """Collection of events with simple frame lookup."""

    events: list[TimelineEvent] = field(default_factory=list)

    def add(self, event: TimelineEvent) -> None:
        self.events.append(event)
        self.events.sort()

    def extend(self, events: Iterable[TimelineEvent]) -> None:
        for event in events:
            self.add(event)

    def at(self, timestamp_ms: int) -> list[TimelineEvent]:
        return [event for event in self.events if event.active(timestamp_ms)]
