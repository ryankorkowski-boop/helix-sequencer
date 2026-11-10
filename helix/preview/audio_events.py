"""Convert Helix audio analysis events into animation triggers."""

from .timeline import AnimationEvent


def drum_events_to_animation(drum_events):
    """Map drum stem detections into reusable animation actions.

    Expected input items may contain time_ms, instrument, and velocity.
    """
    mapping = {
        "crash_left": "left_crash",
        "crash_right": "right_crash",
        "hihat": "hi_hat",
        "snare": "snare",
        "tom_left": "left_tom",
        "tom_right": "right_tom",
        "kick": "kick",
    }
    result = []
    for event in drum_events:
        action = mapping.get(event.get("instrument"))
        if action:
            result.append(AnimationEvent(
                time_ms=event["time_ms"],
                action=action,
                intensity=event.get("velocity", 1.0),
            ))
    return result
