"""Unified audio intelligence adapter that outputs separate timing tracks.

Instead of merging everything, this produces a TimingTrackSet so Helix retains
independent timing/intelligence layers (beats, drops, lyrics, etc.).
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from tools.audio_segment_adapter import wav_to_audio_segments
from tools.audio_timing_tracks import TimingTrack, TimingTrackSet
from tools.style_engine import AudioSegment


CORE_ANALYZER_MODULES = (
    "core.audio_intelligence",
    "core.chronoflow",
    "core.vocal_timeline",
    "core.vocal_emotion",
    "core.lyric_interpreter",
)


def _safe_import(module_name: str) -> Any | None:
    try:
        return import_module(module_name)
    except Exception:
        return None


def _candidate_functions(module: Any) -> list[Callable[..., Any]]:
    names = ("analyze_audio", "analyze", "build_timeline", "detect_events", "detect_lyrics")
    return [getattr(module, name) for name in names if callable(getattr(module, name, None))]


def _call_analyzer(func: Callable[..., Any], wav_path: str | Path) -> Any | None:
    try:
        return func(str(wav_path))
    except Exception:
        return None


def _iter_events(payload: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(payload, Mapping):
        for key in ("segments", "events", "timeline", "lyrics"):
            value = payload.get(key)
            if isinstance(value, list):
                yield from (item for item in value if isinstance(item, Mapping))
    elif isinstance(payload, list):
        yield from (item for item in payload if isinstance(item, Mapping))


def _event_to_segment(event: Mapping[str, Any]) -> AudioSegment:
    start = float(event.get("start", event.get("time", 0.0)))
    duration = float(event.get("duration", 0.5))
    label = str(event.get("label", event.get("type", ""))).lower()

    if "drop" in label:
        event_type = "drop"
    elif "build" in label:
        event_type = "build"
    elif "beat" in label:
        event_type = "beat"
    elif "lyric" in label or "word" in label:
        event_type = "vocal"
    else:
        event_type = "texture"

    return AudioSegment(
        start=start,
        duration=duration,
        section=str(event.get("section", "unknown")),
        event_type=event_type,
        energy=float(event.get("energy", 0.5)),
        beat_strength=float(event.get("beat_strength", 0.5)),
        onset_density=float(event.get("onset_density", 0.5)),
        bass_energy=float(event.get("bass_energy", 0.5)),
        vocal_presence=1.0 if event_type == "vocal" else 0.0,
    )


def analyze_to_timing_tracks(wav_path: str | Path) -> TimingTrackSet:
    base_segments = wav_to_audio_segments(wav_path)

    tracks: list[TimingTrack] = [
        TimingTrack(name="energy", kind="energy", segments=tuple(base_segments), source="wav_rms")
    ]

    for module_name in CORE_ANALYZER_MODULES:
        module = _safe_import(module_name)
        if module is None:
            continue
        for func in _candidate_functions(module):
            payload = _call_analyzer(func, wav_path)
            events = list(_iter_events(payload))
            if not events:
                continue

            segments = tuple(_event_to_segment(event) for event in events)
            tracks.append(
                TimingTrack(
                    name=f"{module_name}.{func.__name__}",
                    kind="analysis",
                    segments=segments,
                    source=module_name,
                )
            )

    return TimingTrackSet(tracks=tuple(tracks))
