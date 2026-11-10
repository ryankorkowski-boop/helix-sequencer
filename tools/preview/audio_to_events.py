"""Convert analyzed audio events into preview timeline events.

This module intentionally keeps audio analysis separate from rendering. Real
analyzers can feed beat/onset/stem data into these adapters.
"""

from collections.abc import Iterable

from .timeline import PreviewEvent, PreviewTimeline



def events_from_hits(hits: Iterable[dict]) -> PreviewTimeline:
    """Build a preview timeline from normalized audio hit dictionaries.

    Expected input:
        {
            "time": 1.25,
            "instrument": "kick",
            "strength": 0.85
        }
    """
    timeline = PreviewTimeline()

    for hit in hits:
        instrument = str(hit.get("instrument", "generic"))
        strength = float(hit.get("strength", 1.0))

        timeline.add(
            PreviewEvent(
                time=float(hit.get("time", 0.0)),
                action=instrument,
                instrument=instrument,
                strength=strength,
                payload={
                    "source": "audio_analysis",
                    "instrument": instrument,
                    "strength": strength,
                },
            )
        )

    return timeline



def merge_audio_events(timeline: PreviewTimeline, hits: Iterable[dict]) -> PreviewTimeline:
    """Append audio events to an existing preview timeline."""
    for event in events_from_hits(hits).events:
        timeline.add(event)
    return timeline
