"""Screen canonical pitched sources for the optional magic keyboard lane."""
from __future__ import annotations

import math
import re
from music.note_events import NoteEvent


# A pitch estimate is not evidence that its player was a keyboardist.
# Retain the already-screened legacy feeds while recognizing explicit
# keyboard/mallet track roles. Unclassified notes still need a confidence gate.
DIRECT_KEYBOARD_SOURCES = frozenset({
    "keyboard", "keys", "piano", "electric_piano", "organ", "synth",
    "synthesizer", "bell", "bells", "celesta", "glockenspiel",
    "xylophone", "marimba", "vibraphone", "mallet", "mallets",
})
TRUSTED_PITCHED_SOURCES = frozenset({
    "piano_stem_harmonic_estimate", "other_stem_screened_mallet_estimate",
    "helix_harmonic_polyphony",
})
OTHER_PERFORMER_TOKENS = frozenset({
    "guitar", "bass", "drum", "drums", "percussion", "vocal", "vocals",
    "voice", "singing", "kick", "snare", "hihat", "hat", "tom", "cymbal",
})


def _other_performer_source(source: str) -> bool:
    """Exclude assigned instrument lanes BEFORE considering pitch confidence."""
    return bool(OTHER_PERFORMER_TOKENS.intersection(
        re.split(r"[^a-z0-9]+", source.lower())
    ))


def magic_keyboard_events(events, mallet_hits=(), *, duration: float) -> list[NoteEvent]:
    """Retain source note timing; confidence-gate otherwise unclassified notes.

    Known harmonic piano and already-screened mallet cues remain eligible.
    Unclassified/synth/horn lanes require calibrated caller evidence: onset,
    pitch confidence, and percussion exclusion. Never manufacture beat notes.
    """
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be finite and positive")
    selected = []
    for event in events:
        source = str(event.source or "").strip().lower().replace("-", "_").replace(" ", "_")
        # Guard even high-confidence composite labels like
        # "electric_guitar_harmonic" and "bass_pitched_onset".
        if _other_performer_source(source):
            continue
        if source not in TRUSTED_PITCHED_SOURCES | DIRECT_KEYBOARD_SOURCES:
            if event.confidence is None or not math.isfinite(event.confidence) or event.confidence < .75:
                continue
            if not any(term in source for term in ("pitched", "harmonic", "synth", "horn", "bell")):
                continue
            if "noise" in source:
                continue
        selected.append(event)
    selected.extend(NoteEvent(h["source_time"] if "source_time" in h else h["time"],
                              (h["source_time"] if "source_time" in h else h["time"]) + .10,
                              h["pitch"], h["velocity"], source="other_stem_screened_mallet_estimate")
                    for h in mallet_hits)
    unique = {}
    for e in selected:
        if not all(math.isfinite(float(v)) for v in (e.start, e.end, e.pitch, e.velocity)):
            continue
        if e.pitch != int(e.pitch) or not 21 <= e.pitch <= 108 or e.end <= e.start or e.start >= duration or e.end <= 0 or e.velocity <= 0:
            continue
        key = (max(0., e.start), min(duration, e.end), e.pitch)
        if key not in unique or unique[key].velocity < e.velocity:
            unique[key] = NoteEvent(*key, min(1., e.velocity), source=e.source, confidence=e.confidence)
    return sorted(unique.values(), key=lambda e: (e.start, e.pitch, e.end))
