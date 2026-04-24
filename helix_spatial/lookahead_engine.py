from __future__ import annotations


def detect_anticipation(upcoming_events: list[dict[str, object]], current_time: float, lookahead_seconds: float = 1.5) -> dict[str, object]:
    hits = [
        event for event in upcoming_events
        if current_time < float(event.get("time", 0.0)) <= current_time + lookahead_seconds
    ]
    if not hits:
        return {"anticipation": False, "cue": "none", "confidence": 0.0}
    first = sorted(hits, key=lambda item: float(item.get("time", 0.0)))[0]
    event_type = str(first.get("type", "upcoming_hit"))
    cue = "pre_hit_dim" if "drop" in event_type or "chorus" in event_type else "charge_up_sweep"
    return {"anticipation": True, "cue": cue, "confidence": 0.72, "event_type": event_type}
