"""Audio analysis event adapters for preview generation."""

from dataclasses import dataclass

from .timeline import TimelineEvent


@dataclass
class AudioHit:
    time_ms: int
    energy: float
    band: str = "full"


def hit_to_event(hit: AudioHit, channel: str = "ALL") -> TimelineEvent:
    """Convert an audio hit into a preview light event."""

    return TimelineEvent(
        time_ms=hit.time_ms,
        action="pulse",
        payload={"channel": channel, "level": max(0.0, min(1.0, hit.energy))},
    )
