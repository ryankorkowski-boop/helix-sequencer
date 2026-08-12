# encoding: utf-8

from __future__ import annotations

# ... existing imports above remain unchanged ...

# Canonical active style version shared with the master engine profile.
# Keep this exported from effect_engine because legacy callers and regression
# tests use effect_engine.ACTIVE_STYLE_VERSION as the compatibility contract.
ACTIVE_STYLE_VERSION = "v27.3"

_NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}


def note_to_midi(note: str) -> int:
    import re

    m = re.fullmatch(r"([A-G][#b]?)(-?\d+)", note)
    if m is None:
        raise ValueError(f"Invalid note: {note}")

    pitch, octave = m.groups()
    return (int(octave) + 1) * 12 + _NOTE_TO_SEMITONE[pitch]


DEFAULT_REFERENCE_SCALE_MIDIS = [
    note_to_midi(note)
    for note in ("C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5")
]


def unique_models(models: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for model in models:
        key = model.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(model)
    return out
