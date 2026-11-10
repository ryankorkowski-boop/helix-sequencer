"""Adapter for PR14-era stem/instrument intelligence.

Reconnects richer separated musical event streams to the new StemRouter without
requiring one exact legacy API shape. Outputs separated StemEvent lists.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.stem_routing import StemEvent


DRUM_STREAM_TO_EVENT = {
    "kick_events": "kick",
    "snare_events": "snare",
    "tom_events": "tom",
    "toms_events": "tom",
    "hihat_events": "hi_hat",
    "hi_hat_events": "hi_hat",
    "cymbal_events": "cymbal",
    "crash_events": "cymbal",
    "ride_events": "cymbal",
    "drum_bus_events": "drum_bus",
}


def _safe_import(module_name: str) -> Any | None:
    try:
        return import_module(module_name)
    except Exception:
        return None


def _call_first_available(module: Any, names: tuple[str, ...], wav_path: str | Path) -> Any | None:
    for name in names:
        fn = getattr(module, name, None)
        if not callable(fn):
            continue
        try:
            return fn(Path(wav_path))
        except TypeError:
            try:
                return fn(str(wav_path))
            except Exception:
                continue
        except Exception:
            continue
    return None


def _start_seconds(obj: Any) -> float:
    for key in ("timestamp", "start", "time"):
        if isinstance(obj, Mapping) and key in obj:
            return float(obj[key])
        if hasattr(obj, key):
            return float(getattr(obj, key))
    for key in ("start_ms", "timestamp_ms"):
        if isinstance(obj, Mapping) and key in obj:
            return float(obj[key]) / 1000.0
        if hasattr(obj, key):
            return float(getattr(obj, key)) / 1000.0
    return 0.0


def _duration_seconds(obj: Any, default: float = 0.12) -> float:
    start = _start_seconds(obj)
    if isinstance(obj, Mapping):
        if "duration" in obj:
            return max(0.001, float(obj["duration"]))
        if "end" in obj:
            return max(0.001, float(obj["end"]) - start)
        if "end_ms" in obj:
            return max(0.001, float(obj["end_ms"]) / 1000.0 - start)
    if hasattr(obj, "duration"):
        return max(0.001, float(getattr(obj, "duration")))
    if hasattr(obj, "end_ms"):
        return max(0.001, float(getattr(obj, "end_ms")) / 1000.0 - start)
    return default


def _intensity(obj: Any, default: float = 0.5) -> float:
    for key in ("velocity", "intensity", "energy", "confidence", "strength"):
        if isinstance(obj, Mapping) and key in obj:
            return max(0.0, min(1.0, float(obj[key])))
        if hasattr(obj, key):
            return max(0.0, min(1.0, float(getattr(obj, key))))
    return default


def _text(obj: Any, *keys: str) -> str | None:
    for key in keys:
        if isinstance(obj, Mapping) and obj.get(key):
            return str(obj[key])
        if hasattr(obj, key) and getattr(obj, key):
            return str(getattr(obj, key))
    return None


def _iter_events(payload: Any) -> Iterable[Any]:
    if payload is None:
        return
    if isinstance(payload, Mapping):
        for key in ("events", "segments", "timeline", "lyrics", "vocals", "notes", "instrument_events"):
            value = payload.get(key)
            if isinstance(value, list):
                yield from value
        if any(key in payload for key in ("start", "time", "timestamp", "start_ms")):
            yield payload
        return
    if isinstance(payload, list):
        yield from payload
        return
    if hasattr(payload, "__dict__"):
        yield from _iter_events(vars(payload))


def drum_streams_to_stem_events(streams: Mapping[str, Iterable[Any]]) -> list[StemEvent]:
    events: list[StemEvent] = []
    for stream_name, items in streams.items():
        fallback_type = DRUM_STREAM_TO_EVENT.get(str(stream_name), "drum_bus")
        for item in items or []:
            event_type = _text(item, "drum_type", "event_type", "type") or fallback_type
            events.append(
                StemEvent(
                    start=round(_start_seconds(item), 4),
                    duration=round(_duration_seconds(item), 4),
                    stem="drums",
                    event_type=event_type,
                    intensity=round(_intensity(item), 3),
                )
            )
    return sorted(events, key=lambda event: event.start)


def instrument_payload_to_stem_events(payload: Any) -> list[StemEvent]:
    events: list[StemEvent] = []
    for item in _iter_events(payload):
        performer = (_text(item, "performer", "instrument", "stem") or "").lower()
        event_type = _text(item, "event_type", "type", "label") or "hit"
        pitch = None
        if isinstance(item, Mapping) and item.get("pitch_midi") is not None:
            pitch = float(item["pitch_midi"])
        elif hasattr(item, "pitch_midi") and getattr(item, "pitch_midi") is not None:
            pitch = float(getattr(item, "pitch_midi"))
        if "bass" in performer:
            stem = "bass"
        elif "guitar" in performer:
            stem = "guitar"
        elif "drum" in performer:
            stem = "drums"
        else:
            continue
        events.append(
            StemEvent(
                start=round(_start_seconds(item), 4),
                duration=round(_duration_seconds(item, default=0.2), 4),
                stem=stem,
                event_type=event_type,
                intensity=round(_intensity(item), 3),
                pitch=pitch,
            )
        )
    return sorted(events, key=lambda event: event.start)


def vocal_payload_to_stem_events(payload: Any) -> list[StemEvent]:
    events: list[StemEvent] = []
    for item in _iter_events(payload):
        role = (_text(item, "voice_role", "role", "singer", "performer") or "lead").lower()
        lyric = _text(item, "lyric", "lyrics", "text", "word", "phrase")
        event_type = _text(item, "event_type", "type", "label") or "vocal"
        if "female" in role:
            stem = "female_vocals"
        elif "backup" in role or "harmony" in role or "choir" in role:
            stem = "backup_vocals"
        else:
            stem = "lead_vocals"
        events.append(
            StemEvent(
                start=round(_start_seconds(item), 4),
                duration=round(_duration_seconds(item, default=0.3), 4),
                stem=stem,
                event_type=event_type,
                intensity=round(_intensity(item), 3),
                lyric=lyric,
                voice_role=role,
            )
        )
    return sorted(events, key=lambda event: event.start)


def detect_pr14_stem_events(wav_path: str | Path) -> dict[str, list[StemEvent]]:
    separated: dict[str, list[StemEvent]] = {
        "drums": [],
        "guitar": [],
        "bass": [],
        "lead_vocals": [],
        "female_vocals": [],
        "backup_vocals": [],
    }

    drum_module = _safe_import("audio.drum_detection")
    if drum_module is not None:
        payload = _call_first_available(drum_module, ("detect_drum_event_streams_from_file", "detect_drum_event_streams"), wav_path)
        if isinstance(payload, Mapping):
            separated["drums"].extend(drum_streams_to_stem_events(payload))

    for module_name in ("core.audio_intelligence", "core.chronoflow"):
        module = _safe_import(module_name)
        if module is None:
            continue
        payload = _call_first_available(module, ("derive_guitar_events", "derive_bass_events", "analyze_audio", "analyze"), wav_path)
        for event in instrument_payload_to_stem_events(payload):
            separated.setdefault(event.stem, []).append(event)

    for module_name in ("core.vocal_timeline", "core.vocal_emotion", "core.lyric_interpreter"):
        module = _safe_import(module_name)
        if module is None:
            continue
        payload = _call_first_available(module, ("detect_lyrics", "interpret_lyrics", "detect_vocals", "analyze", "build_timeline"), wav_path)
        for event in vocal_payload_to_stem_events(payload):
            separated.setdefault(event.stem, []).append(event)

    return {key: sorted(value, key=lambda event: event.start) for key, value in separated.items()}
