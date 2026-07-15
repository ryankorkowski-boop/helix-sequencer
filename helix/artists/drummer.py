"""Drummer performer artifact.

The drummer is intentionally decomposed into standalone reactive components:
kick, snare, hi-hat, toms, and fills.
"""

from dataclasses import dataclass, field

from helix.preview.timeline import TimelineEvent


@dataclass
class DrumComponent:
    name: str
    target: str
    threshold: float = 0.5

    def react(self, time_ms: int, strength: float) -> TimelineEvent | None:
        if strength < self.threshold:
            return None
        return TimelineEvent(
            start_ms=time_ms,
            duration_ms=120,
            target=self.target,
            effect=self.name,
            intensity=min(1.0, strength),
            metadata={"artist": "drummer", "component": self.name},
        )


@dataclass
class Drummer:
    kick: DrumComponent = field(
        default_factory=lambda: DrumComponent("kick", "10_WHOLE_HOUSE", .55)
    )
    snare: DrumComponent = field(
        default_factory=lambda: DrumComponent("snare", "ARCHES", .6)
    )
    hihat: DrumComponent = field(
        default_factory=lambda: DrumComponent("hihat", "90_ALL_WHITE", .65)
    )
    toms: DrumComponent = field(
        default_factory=lambda: DrumComponent("toms", "MEGA_TREE", .7)
    )
    fills: DrumComponent = field(
        default_factory=lambda: DrumComponent("fills", "10_WHOLE_HOUSE", .75)
    )

    def components(self) -> list[DrumComponent]:
        return [self.kick, self.snare, self.hihat, self.toms, self.fills]

    def analyze_hit(self, component: str, time_ms: int, strength: float):
        for item in self.components():
            if item.name == component:
                return item.react(time_ms, strength)
        return None
