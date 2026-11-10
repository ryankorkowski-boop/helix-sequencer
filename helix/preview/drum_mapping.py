"""Bridge Helix analysis events into preview animation events."""


def normalize_drum_event(event):
    """Normalize incoming Helix drum detections.

    Keeps preview independent from the audio analyzer implementation.
    """
    return {
        "time_ms": int(event.get("time_ms", 0)),
        "instrument": event.get("instrument", ""),
        "velocity": float(event.get("velocity", 1.0)),
    }


def normalize_events(events):
    return [normalize_drum_event(event) for event in events]
