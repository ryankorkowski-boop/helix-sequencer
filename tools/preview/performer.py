"""Map audio events into performer animation events."""

from collections.abc import Iterable

from .performance_rules import action_for_instrument



def performer_events(audio_events: Iterable[dict]) -> list[dict]:
    """Create animation-ready performer actions."""
    output = []

    for event in audio_events:
        output.append(
            {
                "time": float(event.get("time", 0.0)),
                "action": action_for_instrument(str(event.get("instrument", "generic"))),
                "strength": float(event.get("strength", 1.0)),
                "instrument": event.get("instrument", "generic"),
            }
        )

    return output
