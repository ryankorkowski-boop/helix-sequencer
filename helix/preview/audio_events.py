"""Adapters for converting audio analysis output into preview events."""

from .timeline import TimelineEvent


def beat_event(time_ms: int, target: str = "10_WHOLE_HOUSE", strength: float = 1.0) -> TimelineEvent:
    """Create a short beat pulse event."""
    return TimelineEvent(
        start_ms=time_ms,
        duration_ms=120,
        target=target,
        effect="pulse",
        intensity=max(0.0, min(1.0, strength)),
    )


def energy_event(time_ms: int, energy: float, target: str) -> TimelineEvent:
    """Map normalized audio energy to a light intensity event."""
    return TimelineEvent(
        start_ms=time_ms,
        duration_ms=250,
        target=target,
        effect="level",
        intensity=max(0.0, min(1.0, energy)),
    )
