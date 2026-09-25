from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from audio.musical_event_model import MusicalEvent, clamp01


@dataclass(frozen=True)
class MusicalIntelligenceConfig:
    """Controls musical salience and adaptive timing without touching XSQ output."""

    importance_confidence_weight: float = 0.35
    importance_strength_weight: float = 0.40
    importance_role_weight: float = 0.25
    timing_min_gap_ms: int = 45
    timing_onset_window_ms: int = 90
    chord_window_ms: int = 85


_ROLE_WEIGHT = {
    "downbeat": 1.0,
    "kick": 0.82,
    "snare": 0.78,
    "crash": 0.92,
    "cymbal": 0.82,
    "tom": 0.72,
    "bass": 0.76,
    "guitar": 0.70,
    "keyboard": 0.80,
    "piano": 0.80,
    "singer": 0.74,
    "vocal": 0.74,
    "melody": 0.86,
}


def event_role_weight(event: MusicalEvent) -> float:
    text = " ".join(
        str(value or "").lower()
        for value in (event.kind, event.instrument, event.metadata.get("role"))
    )
    for role, weight in _ROLE_WEIGHT.items():
        if role in text:
            return weight
    return 0.50


def score_musical_importance(
    event: MusicalEvent,
    *,
    is_downbeat: bool = False,
    config: MusicalIntelligenceConfig = MusicalIntelligenceConfig(),
) -> float:
    """Return deterministic salience used to prioritize musical moments."""

    confidence = clamp01(event.confidence)
    strength = clamp01(event.strength)
    role = 1.0 if is_downbeat else event_role_weight(event)
    score = (
        confidence * config.importance_confidence_weight
        + strength * config.importance_strength_weight
        + role * config.importance_role_weight
    )
    return round(clamp01(score), 4)


def annotate_importance(
    events: Iterable[MusicalEvent],
    *,
    downbeats_ms: Iterable[int] = (),
    config: MusicalIntelligenceConfig = MusicalIntelligenceConfig(),
) -> list[MusicalEvent]:
    downbeats = {int(value) for value in downbeats_ms}
    annotated: list[MusicalEvent] = []
    for event in events:
        importance = score_musical_importance(
            event,
            is_downbeat=event.time_ms in downbeats or bool(event.metadata.get("downbeat")),
            config=config,
        )
        metadata = dict(event.metadata)
        metadata["musical_importance"] = importance
        annotated.append(
            MusicalEvent(
                time_ms=event.time_ms,
                kind=event.kind,
                confidence=event.confidence,
                strength=event.strength,
                source=event.source,
                instrument=event.instrument,
                duration_ms=event.duration_ms,
                pitch_midi=event.pitch_midi,
                metadata=metadata,
            )
        )
    return annotated


def build_adaptive_timing_events(
    events: Iterable[MusicalEvent],
    *,
    beat_ms: Iterable[int] = (),
    config: MusicalIntelligenceConfig = MusicalIntelligenceConfig(),
) -> list[MusicalEvent]:
    """Create an adaptive timing layer from musical events.

    Strong musical events are retained individually, while nearby weak events
    are allowed to share a timing window. This preserves fills and fast strokes
    instead of blindly quantizing everything to a beat grid.
    """

    source = sorted(events, key=lambda item: (item.time_ms, -item.confidence))
    beats = [int(value) for value in beat_ms]
    candidates: list[MusicalEvent] = []
    for event in source:
        importance = float(event.metadata.get("musical_importance", score_musical_importance(event, config=config)))
        if importance < 0.30 and not event.metadata.get("downbeat"):
            continue
        candidates.append(event)

    selected: list[MusicalEvent] = []
    for event in candidates:
        if not selected:
            selected.append(event)
            continue
        previous = selected[-1]
        gap = event.time_ms - previous.time_ms
        if gap >= config.timing_min_gap_ms:
            selected.append(event)
            continue
        current_importance = float(event.metadata.get("musical_importance", 0.0))
        previous_importance = float(previous.metadata.get("musical_importance", 0.0))
        if current_importance > previous_importance and gap <= config.timing_onset_window_ms:
            selected[-1] = event

    timing_events: list[MusicalEvent] = []
    for event in selected:
        nearest_beat = min((abs(event.time_ms - beat) for beat in beats), default=None)
        metadata = dict(event.metadata)
        metadata.update({
            "timing_role": "adaptive_musical_event",
            "nearest_beat_distance_ms": nearest_beat,
            "timing_density": "beat" if nearest_beat is not None and nearest_beat <= 35 else "event",
        })
        timing_events.append(
            MusicalEvent(
                time_ms=event.time_ms,
                kind="timing_musical",
                confidence=event.confidence,
                strength=event.strength,
                source="helix.musical_intelligence",
                instrument=event.instrument,
                duration_ms=event.duration_ms,
                pitch_midi=event.pitch_midi,
                metadata=metadata,
            )
        )
    return timing_events


def detect_chord_groups(
    events: Iterable[MusicalEvent],
    *,
    window_ms: int = 85,
) -> list[MusicalEvent]:
    """Group simultaneous pitched normalized events into renderer-neutral chords."""

    pitched = [
        event for event in events
        if event.pitch_midi is not None and event.confidence >= 0.35
    ]
    pitched.sort(key=lambda item: item.time_ms)
    groups: list[list[MusicalEvent]] = []
    for event in pitched:
        if not groups or event.time_ms - groups[-1][0].time_ms > window_ms:
            groups.append([event])
        else:
            groups[-1].append(event)

    chords: list[MusicalEvent] = []
    for group in groups:
        pitches = sorted({round(float(item.pitch_midi), 2) for item in group})
        if len(pitches) < 2:
            continue
        confidence = max(item.confidence for item in group)
        strength = max(item.strength for item in group)
        metadata = {
            "pitches_midi": pitches,
            "note_count": len(pitches),
            "source_event_count": len(group),
            "musical_importance": round(clamp01(
                0.45 * confidence + 0.35 * strength + 0.20 * min(1.0, len(pitches) / 4.0)
            ), 4),
        }
        chords.append(
            MusicalEvent(
                time_ms=min(item.time_ms for item in group),
                kind="harmony_chord",
                confidence=confidence,
                strength=strength,
                source="helix.musical_intelligence",
                instrument="keyboard",
                duration_ms=max(item.duration_ms for item in group),
                pitch_midi=pitches[0],
                metadata=metadata,
            )
        )
    return chords


def summarize(events: Iterable[MusicalEvent]) -> dict[str, object]:
    counts: dict[str, int] = defaultdict(int)
    importance_values: list[float] = []
    for event in events:
        counts[event.kind] += 1
        if "musical_importance" in event.metadata:
            importance_values.append(float(event.metadata["musical_importance"]))
    return {
        "event_kind_counts": dict(sorted(counts.items())),
        "important_event_count": sum(value >= 0.70 for value in importance_values),
        "mean_musical_importance": round(
            sum(importance_values) / max(1, len(importance_values)), 4
        ),
    }


def detect_melody_runs(
    events: Iterable[MusicalEvent],
    *,
    min_notes: int = 3,
    max_gap_ms: int = 180,
) -> list[MusicalEvent]:
    """Detect directional runs in normalized pitched events without assigning effects."""
    notes = [
        event for event in events
        if event.kind == "note_event"
        and event.pitch_midi is not None
        and event.confidence >= 0.45
    ]
    notes.sort(key=lambda item: item.time_ms)
    runs: list[tuple[list[MusicalEvent], int]] = []
    current: list[MusicalEvent] = []
    direction = 0

    def flush() -> None:
        nonlocal current, direction
        if len(current) >= min_notes and direction:
            runs.append((current, direction))
        current = []
        direction = 0

    for event in notes:
        if not current:
            current = [event]
            continue
        prev = current[-1]
        gap = event.time_ms - prev.time_ms
        step = float(event.pitch_midi) - float(prev.pitch_midi)
        step_dir = 1 if step > 0 else -1 if step < 0 else 0

        if gap > max_gap_ms or step_dir == 0:
            flush()
            current = [event]
            continue
        if direction == 0:
            direction = step_dir
            current.append(event)
            continue
        if step_dir != direction:
            flush()
            current = [prev, event]
            direction = step_dir
            continue
        current.append(event)

    flush()

    out: list[MusicalEvent] = []
    for run, run_direction in runs:
        direction_name = "ascending" if run_direction > 0 else "descending"
        confidence = sum(item.confidence for item in run) / len(run)
        strength = max(item.strength for item in run)
        pitches = [int(round(float(item.pitch_midi))) for item in run]
        out.append(
            MusicalEvent(
                time_ms=run[0].time_ms,
                kind="melody_run",
                confidence=clamp01(confidence),
                strength=clamp01(strength),
                source="helix.musical_intelligence",
                instrument="keyboard",
                duration_ms=max(item.time_ms + item.duration_ms for item in run) - run[0].time_ms,
                pitch_midi=float(pitches[0]),
                metadata={
                    "direction": direction_name,
                    "note_count": len(run),
                    "pitches_midi": pitches,
                    "musical_importance": round(clamp01(0.45 * confidence + 0.40 * strength + 0.15), 4),
                    "span_ms": run[-1].time_ms - run[0].time_ms,
                },
            )
        )
    return out

def direction_for_run(run: list[MusicalEvent]) -> int:
    if len(run) < 2:
        return 0
    delta = float(run[-1].pitch_midi) - float(run[0].pitch_midi)
    return 1 if delta > 0 else -1 if delta < 0 else 0
