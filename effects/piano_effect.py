from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from music.midi_import import import_midi
from music.note_events import NoteEvent, filter_note_range, midi_note_name, note_events_from_helix_events
from render.keyboard_geometry import generate_keyboard_geometry
from render.piano_renderer import PianoRenderConfig, render_frame


PianoEffectConfig = PianoRenderConfig


def load_note_events(
    *,
    midi_path: Path | str | None = None,
    helix_note_events: Iterable[Any] | None = None,
    note_range_start: int = 21,
    note_range_end: int = 108,
) -> list[NoteEvent]:
    events: list[NoteEvent] = []
    if midi_path is not None:
        events.extend(import_midi(midi_path).events)
    if helix_note_events is not None:
        events.extend(note_events_from_helix_events(helix_note_events))
    return filter_note_range(events, note_range_start, note_range_end)


def suitability_score(model: Any, mode: str = "true_piano") -> dict[str, Any]:
    name = str(getattr(model, "name", model if isinstance(model, str) else "") or "").lower()
    model_type = str(getattr(model, "type", getattr(model, "model_type", "")) or "").lower()
    semantic = str(getattr(model, "semantic_type", "") or "").lower()
    text = " ".join([name, model_type, semantic])
    score = 0.25
    route = "note_bucket"
    if "keyboard" in text or "piano" in text or "notes" in text:
        score = 0.96
        route = "literal_keyboard"
    elif "matrix" in text or "image" in text or "custom" in text:
        score = 0.90 if mode == "true_piano" else 0.86
        route = "matrix_keyboard" if mode == "true_piano" else "abstract_note_grid"
    elif "mega" in text or "tree" in text:
        score = 0.68
        route = "abstract_note_bands"
    elif "arch" in text:
        score = 0.62
        route = "note_travel"
    elif "ac" in text or "white" in text:
        score = 0.42
        route = "coarse_note_buckets"
    return {"score": round(score, 3), "route": route, "mode": mode}


def note_bucket_activations(events: Iterable[NoteEvent], bucket_count: int, note_range_start: int, note_range_end: int) -> list[dict[str, Any]]:
    bucket_count = max(1, int(bucket_count))
    span = max(1, int(note_range_end) - int(note_range_start))
    out: list[dict[str, Any]] = []
    for event in events:
        frac = max(0.0, min(1.0, (event.pitch - note_range_start) / span))
        bucket = min(bucket_count - 1, int(round(frac * (bucket_count - 1))))
        out.append(
            {
                "bucket": bucket,
                "pitch": event.pitch,
                "note": midi_note_name(event.pitch),
                "start_ms": event.start_ms,
                "end_ms": event.end_ms,
                "velocity": round(event.velocity, 3),
                "source": event.source,
            }
        )
    return sorted(out, key=lambda item: (item["start_ms"], item["bucket"], item["pitch"]))


def build_piano_effect_plan(
    events: Iterable[NoteEvent],
    config: PianoEffectConfig = PianoEffectConfig(),
    *,
    frame_times: Iterable[float] | None = None,
    bucket_count: int = 16,
    target_models: Iterable[Any] = (),
) -> dict[str, Any]:
    filtered = filter_note_range(events, config.note_range_start, config.note_range_end)
    if frame_times is None:
        starts = [event.start for event in filtered]
        frame_times = sorted(set(starts[:240]))
    geometry = generate_keyboard_geometry(
        config.note_range_start,
        config.note_range_end,
        show_sharps_flats=config.show_sharps_flats,
        orientation=config.orientation,
    )
    frames = [render_frame(filtered, timestamp, config) for timestamp in frame_times]
    return {
        "schema": "helix.piano_effect.v1",
        "config": asdict(config),
        "note_events": [event.to_dict() for event in filtered],
        "keyboard_geometry": geometry.to_dict(),
        "frames": frames,
        "abstract_note_bar_activations": [
            frame for frame in frames if frame.get("mode") == "bars"
        ],
        "note_bucket_activations": note_bucket_activations(
            filtered,
            bucket_count=bucket_count,
            note_range_start=config.note_range_start,
            note_range_end=config.note_range_end,
        ),
        "model_suitability": [
            {"model": str(getattr(model, "name", model)), **suitability_score(model, config.mode)}
            for model in target_models
        ],
        "debug": debug_note_timeline(filtered),
    }


def debug_note_timeline(events: Iterable[NoteEvent]) -> dict[str, Any]:
    events_list = sorted(events, key=lambda item: (item.start, item.pitch, item.end))
    if not events_list:
        return {"event_count": 0, "active_range": None, "timeline": []}
    return {
        "event_count": len(events_list),
        "active_range": {
            "lowest_pitch": min(event.pitch for event in events_list),
            "highest_pitch": max(event.pitch for event in events_list),
            "start_ms": min(event.start_ms for event in events_list),
            "end_ms": max(event.end_ms for event in events_list),
        },
        "timeline": [
            f"{event.start_ms}-{event.end_ms} {midi_note_name(event.pitch)} v={event.velocity:.2f} src={event.source}"
            for event in events_list[:300]
        ],
    }
