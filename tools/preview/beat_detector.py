"""Lightweight beat/onset adapter for the Helix preview engine.

This module accepts analyzer output and normalizes it into events. DSP backends
(librosa, essentia, Vamp, etc.) can plug into this interface later.
"""

from collections.abc import Iterable



def normalize_beats(beats: Iterable[float], strength: float = 1.0) -> list[dict]:
    """Convert beat timestamps into normalized preview hits."""
    return [
        {
            "time": float(timestamp),
            "instrument": "beat",
            "strength": max(0.0, min(1.0, strength)),
        }
        for timestamp in beats
    ]



def normalize_onsets(onsets: Iterable[dict]) -> list[dict]:
    """Normalize generic onset detector output.

    Expected:
        {"time": 1.2, "energy": 0.8}
    """
    events = []
    for onset in onsets:
        events.append(
            {
                "time": float(onset.get("time", 0.0)),
                "instrument": "onset",
                "strength": float(onset.get("energy", 1.0)),
            }
        )
    return events
