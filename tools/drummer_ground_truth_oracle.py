"""Shared deterministic event oracle for Drummer V3 verification."""
from __future__ import annotations

from dataclasses import dataclass

TARGETS = (
    "KICK",
    "SNARE",
    "HI_HAT",
    "TOM_HIGH",
    "TOM_MID",
    "TOM_FLOOR",
    "CYMBAL_LEFT",
    "CYMBAL_RIGHT",
)


@dataclass(frozen=True, order=True)
class GroundTruthEvent:
    time: float
    target: str
    duration: float


def fixture_events(duration: float = 20.0) -> list[GroundTruthEvent]:
    """Return the canonical 20-second verification schedule.

    The first eight seconds isolate every public component exactly once. The
    remainder adds ordinary kick/snare/hat motion, alternating crashes and
    three-tom fills. At 20 seconds this contains exactly 68 events.
    """
    duration = float(duration)
    events: list[GroundTruthEvent] = []
    for index, target in enumerate(TARGETS):
        time = index + 0.25
        if time < duration:
            events.append(GroundTruthEvent(time, target, min(0.45, duration - time)))

    for second in range(8, 20):
        if second >= duration:
            break
        for offset, target, length in (
            (0.00, "KICK", 0.18),
            (0.25, "HI_HAT", 0.10),
            (0.50, "SNARE", 0.18),
            (0.75, "HI_HAT", 0.10),
        ):
            time = second + offset
            if time < duration:
                events.append(GroundTruthEvent(time, target, min(length, duration - time)))

    for index, second in enumerate((8, 12, 16)):
        if second < duration:
            target = "CYMBAL_LEFT" if index % 2 == 0 else "CYMBAL_RIGHT"
            events.append(GroundTruthEvent(float(second), target, min(0.30, duration - second)))

    for second in (11, 15, 19):
        for offset, target in ((0.00, "TOM_HIGH"), (0.125, "TOM_MID"), (0.25, "TOM_FLOOR")):
            time = second + offset
            if time < duration:
                events.append(GroundTruthEvent(time, target, min(0.18, duration - time)))

    order = {name: index for index, name in enumerate(TARGETS)}
    return sorted(events, key=lambda event: (event.time, order[event.target], event.duration))
