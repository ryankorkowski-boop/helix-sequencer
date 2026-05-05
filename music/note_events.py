from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class NoteEvent:
    start: float
    end: float
    pitch: int
    velocity: float = 1.0
    channel: int | None = None
    source: str = "unknown"
    confidence: float | None = None

    @property
    def start_ms(self) -> int:
        return int(round(self.start * 1000.0))

    @property
    def end_ms(self) -> int:
        return int(round(self.end * 1000.0))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PITCH_CLASS_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def clamp_note_event(event: NoteEvent, note_range_start: int, note_range_end: int) -> NoteEvent | None:
    if int(event.pitch) < int(note_range_start) or int(event.pitch) > int(note_range_end):
        return None
    if event.end <= event.start:
        return None
    return NoteEvent(
        start=max(0.0, float(event.start)),
        end=max(float(event.start) + 0.001, float(event.end)),
        pitch=int(event.pitch),
        velocity=max(0.0, min(1.0, float(event.velocity))),
        channel=event.channel,
        source=event.source,
        confidence=None if event.confidence is None else max(0.0, min(1.0, float(event.confidence))),
    )


def filter_note_range(events: Iterable[NoteEvent], note_range_start: int, note_range_end: int) -> list[NoteEvent]:
    out: list[NoteEvent] = []
    for event in events:
        clamped = clamp_note_event(event, note_range_start, note_range_end)
        if clamped is not None:
            out.append(clamped)
    out.sort(key=lambda item: (item.start, item.pitch, item.end))
    return out


def midi_note_name(pitch: int) -> str:
    pitch_i = int(pitch)
    return f"{PITCH_CLASS_NAMES[pitch_i % 12]}{(pitch_i // 12) - 1}"


def note_events_from_helix_events(events: Iterable[Any], source: str = "helix_polyphonic") -> list[NoteEvent]:
    """Flatten Helix chord-style note events into canonical per-note events."""
    out: list[NoteEvent] = []
    for event in events:
        start_ms = int(getattr(event, "start_ms", getattr(event, "start", 0)) or 0)
        end_ms = int(getattr(event, "end_ms", getattr(event, "end", start_ms + 1)) or (start_ms + 1))
        confidence = getattr(event, "confidence", None)
        for note in list(getattr(event, "notes", []) or []):
            if not isinstance(note, (tuple, list)) or not note:
                continue
            try:
                pitch = int(round(float(note[0])))
                velocity = float(note[1]) if len(note) > 1 else 1.0
            except (TypeError, ValueError):
                continue
            out.append(
                NoteEvent(
                    start=start_ms / 1000.0,
                    end=max(start_ms + 1, end_ms) / 1000.0,
                    pitch=pitch,
                    velocity=max(0.0, min(1.0, velocity)),
                    channel=None,
                    source=source,
                    confidence=None if confidence is None else float(confidence),
                )
            )
    out.sort(key=lambda item: (item.start, item.pitch, item.end))
    return out


def active_notes_at(events: Iterable[NoteEvent], timestamp: float, decay_seconds: float = 0.0) -> list[NoteEvent]:
    t = float(timestamp)
    out = []
    for event in events:
        if event.start <= t <= event.end + max(0.0, decay_seconds):
            out.append(event)
    return sorted(out, key=lambda item: (item.pitch, item.start))
