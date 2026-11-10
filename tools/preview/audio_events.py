"""Adapters for converting Helix audio analysis events into preview events."""

from .timeline import PreviewEvent, PreviewTimeline


def add_drum_hit(timeline: PreviewTimeline, timestamp: float, instrument: str) -> None:
    timeline.add(
        PreviewEvent(
            time=timestamp,
            action=instrument,
            payload={"source": "drum_analysis"},
        )
    )
