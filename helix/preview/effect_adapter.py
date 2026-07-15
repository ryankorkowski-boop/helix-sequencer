"""Bridge between Helix effects and preview timeline events."""

from dataclasses import dataclass
from typing import Any, Iterable

from .timeline import Timeline, TimelineEvent


@dataclass
class EffectPlacement:
    """Normalized effect placement for preview rendering."""

    channel: str
    start_ms: int
    end_ms: int
    level: float = 1.0
    effect: str = "on"


class EffectPreviewAdapter:
    """Convert engine effect placements into preview timeline events."""

    def __init__(self, timeline: Timeline | None = None) -> None:
        self.timeline = timeline or Timeline()

    def add_effect(self, placement: EffectPlacement) -> None:
        self.timeline.add(
            TimelineEvent(
                time_ms=placement.start_ms,
                action=placement.effect,
                payload={
                    "channel": placement.channel,
                    "level": placement.level,
                    "end_ms": placement.end_ms,
                },
            )
        )

    def extend(self, effects: Iterable[EffectPlacement]) -> Timeline:
        for effect in effects:
            self.add_effect(effect)
        return self.timeline

    def from_dict(self, effect: dict[str, Any]) -> None:
        self.add_effect(EffectPlacement(**effect))
