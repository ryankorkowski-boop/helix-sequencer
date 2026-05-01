from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class InstrumentEvent:
    performer: str
    event_type: str
    start_ms: int
    end_ms: int
    intensity: float
    confidence: float
    pitch_midi: float | None = None
    note_count: int = 0
    source: str = "instrument_detection"
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _event_start_ms(event: Any) -> int:
    return max(0, int(getattr(event, "start_ms", 0) or 0))


def _event_end_ms(event: Any, fallback_ms: int = 180) -> int:
    start_ms = _event_start_ms(event)
    return max(start_ms + 40, int(getattr(event, "end_ms", start_ms + fallback_ms) or (start_ms + fallback_ms)))


def _extract_midis(event: Any) -> list[float]:
    midis: list[float] = []
    for note in list(getattr(event, "notes", []) or []):
        if isinstance(note, (list, tuple)) and note:
            try:
                midis.append(float(note[0]))
            except (TypeError, ValueError):
                continue
        else:
            try:
                midis.append(float(getattr(note, "pitch")))
            except (AttributeError, TypeError, ValueError):
                continue
    if not midis and hasattr(event, "pitch"):
        try:
            midis.append(float(getattr(event, "pitch")))
        except (TypeError, ValueError):
            pass
    return midis


def _velocity(event: Any, default: float = 0.62) -> float:
    values: list[float] = []
    for note in list(getattr(event, "notes", []) or []):
        if isinstance(note, (list, tuple)) and len(note) > 1:
            try:
                values.append(float(note[1]))
            except (TypeError, ValueError):
                continue
    if hasattr(event, "velocity"):
        try:
            values.append(float(getattr(event, "velocity")))
        except (TypeError, ValueError):
            pass
    return _clamp(max(values) if values else default)


def _nearest_low_pitch(note_events: Iterable[Any], target_ms: int, default: float = 43.0) -> float:
    best_pitch = default
    best_distance: int | None = None
    for event in note_events:
        midis = _extract_midis(event)
        if not midis:
            continue
        start_ms = _event_start_ms(event)
        end_ms = _event_end_ms(event)
        distance = 0 if start_ms <= target_ms <= end_ms else min(abs(target_ms - start_ms), abs(target_ms - end_ms))
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_pitch = min(midis)
    return best_pitch


def derive_guitar_events(
    note_events: Iterable[Any],
    *,
    onset_ms: Iterable[int] = (),
    beat_ms: Iterable[int] = (),
) -> tuple[list[InstrumentEvent], Mapping[str, Any]]:
    events: list[InstrumentEvent] = []
    previous_signature: tuple[int, ...] | None = None
    for raw in sorted(note_events, key=_event_start_ms):
        midis = _extract_midis(raw)
        if not midis:
            continue
        start_ms = _event_start_ms(raw)
        end_ms = _event_end_ms(raw)
        duration = end_ms - start_ms
        note_count = len(midis)
        signature = tuple(sorted(int(round(pitch)) for pitch in midis))
        velocity = _velocity(raw)
        if note_count >= 2:
            event_type = "strum"
            reason = "polyphonic_note_cluster"
        elif duration >= 520:
            event_type = "sustained_note"
            reason = "long_note_duration"
        else:
            event_type = "picking"
            reason = "single_note_onset"
        if previous_signature is not None and signature != previous_signature and start_ms - events[-1].start_ms > 90:
            events.append(
                InstrumentEvent(
                    "guitarist",
                    "chord_change",
                    max(0, start_ms - 55),
                    start_ms + 120,
                    _clamp(velocity * 0.72),
                    0.62,
                    max(midis),
                    note_count,
                    "note_signature_change",
                    "pitch_set_changed",
                )
            )
        previous_signature = signature
        events.append(
            InstrumentEvent(
                "guitarist",
                event_type,
                start_ms,
                end_ms if event_type == "sustained_note" else min(end_ms, start_ms + 260),
                velocity,
                0.78 if note_count >= 2 else 0.68,
                max(midis),
                note_count,
                "note_events",
                reason,
            )
        )
    fallback_used = False
    if not events:
        fallback_marks = list(onset_ms) or list(beat_ms)
        for idx, mark in enumerate(sorted(set(int(value) for value in fallback_marks))[:256]):
            if idx % 2 and len(fallback_marks) > 8:
                continue
            fallback_used = True
            events.append(
                InstrumentEvent(
                    "guitarist",
                    "strum" if idx % 4 == 0 else "picking",
                    max(0, mark),
                    max(0, mark) + 160,
                    0.42 if idx % 4 else 0.56,
                    0.34,
                    None,
                    0,
                    "rhythm_energy_fallback",
                    "no_note_events_available",
                )
            )
    return events, {
        "fallback_mode": "rhythm_energy" if fallback_used else "note_events",
        "event_count": len(events),
        "sources": sorted({event.source for event in events}),
    }


def derive_bass_events(
    bass_peaks: Iterable[int],
    note_events: Iterable[Any],
    *,
    beat_ms: Iterable[int] = (),
) -> tuple[list[InstrumentEvent], Mapping[str, Any]]:
    note_list = list(note_events)
    peak_list = sorted(set(int(value) for value in bass_peaks))
    events: list[InstrumentEvent] = []
    for idx, mark in enumerate(peak_list):
        pitch = _nearest_low_pitch(note_list, mark)
        events.append(
            InstrumentEvent(
                "bassist",
                "pluck",
                max(0, mark),
                max(0, mark) + 220,
                0.72 if idx % 4 == 0 else 0.58,
                0.7,
                pitch,
                1,
                "bass_peak_events",
                "low_mid_peak",
            )
        )
    for raw in sorted(note_list, key=_event_start_ms):
        midis = _extract_midis(raw)
        if not midis:
            continue
        pitch = min(midis)
        if pitch > 59:
            continue
        start_ms = _event_start_ms(raw)
        end_ms = _event_end_ms(raw)
        if end_ms - start_ms >= 460:
            events.append(
                InstrumentEvent(
                    "bassist",
                    "sustained_note",
                    start_ms,
                    end_ms,
                    _clamp(_velocity(raw) * 0.74),
                    0.58,
                    pitch,
                    1,
                    "low_note_duration",
                    "bass_sustain_from_note_event",
                )
            )
    fallback_used = False
    if not events:
        for idx, mark in enumerate(sorted(set(int(value) for value in beat_ms))[:128]):
            if idx % 2:
                continue
            fallback_used = True
            events.append(
                InstrumentEvent(
                    "bassist",
                    "pluck",
                    max(0, mark),
                    max(0, mark) + 200,
                    0.38,
                    0.3,
                    43.0,
                    0,
                    "beat_fallback",
                    "no_bass_peaks_or_low_notes",
                )
            )
    events.sort(key=lambda event: (event.start_ms, event.event_type))
    return events, {
        "fallback_mode": "beat" if fallback_used else ("bass_peaks_and_notes" if peak_list and note_list else "partial_input"),
        "event_count": len(events),
        "sources": sorted({event.source for event in events}),
    }
