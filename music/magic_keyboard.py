"""Screen canonical pitched sources for the optional magic keyboard lane."""
from __future__ import annotations

import math
from music.note_events import NoteEvent


def magic_keyboard_events(events, mallet_hits=(), *, duration: float) -> list[NoteEvent]:
    """Retain source note timing; confidence-gate otherwise unclassified notes.

    Known harmonic piano and already-screened mallet cues remain eligible.
    Unclassified/synth/horn lanes require calibrated caller evidence: onset,
    pitch confidence, and percussion exclusion. Never manufacture beat notes.
    """
    selected = []
    for event in events:
        if event.source not in ("piano_stem_harmonic_estimate", "other_stem_screened_mallet_estimate"):
            if event.confidence is None or event.confidence < .75:
                continue
            if not any(term in event.source.lower() for term in ("pitched", "harmonic", "synth", "horn", "bell")):
                continue
            if any(term in event.source.lower() for term in ("drum", "percussion", "noise", "vocal")):
                continue
        selected.append(event)
    selected.extend(NoteEvent(h.get("source_time", h["time"]),
                              h.get("source_time", h["time"]) + .10,
                              h["pitch"], h["velocity"], source="other_stem_screened_mallet_estimate")
                    for h in mallet_hits)
    unique = {}
    for e in selected:
        if not all(math.isfinite(float(v)) for v in (e.start, e.end, e.pitch, e.velocity)):
            continue
        if not 21 <= e.pitch <= 108 or e.end <= e.start or e.start >= duration or e.end <= 0 or e.velocity <= 0:
            continue
        key = (max(0., e.start), min(duration, e.end), e.pitch)
        if key not in unique or unique[key].velocity < e.velocity:
            unique[key] = NoteEvent(*key, min(1., e.velocity), source=e.source, confidence=e.confidence)
    return sorted(unique.values(), key=lambda e: (e.start, e.pitch, e.end))
