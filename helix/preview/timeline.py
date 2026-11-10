"""Timeline primitives for preview animation events."""

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(order=True)
class AnimationEvent:
    time_ms: int
    action: str
    intensity: float = 1.0
    metadata: dict = field(default_factory=dict, compare=False)


class Timeline:
    def __init__(self, events: Iterable[AnimationEvent] = ()):
        self.events = sorted(events)

    def add(self, event: AnimationEvent):
        self.events.append(event)
        self.events.sort()

    def events_at(self, time_ms: int):
        return [e for e in self.events if e.time_ms == time_ms]
