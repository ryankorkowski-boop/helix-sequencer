"""Compatibility entry points backed by the canonical V3 typed-event detector."""
from pathlib import Path
from typing import Callable
import librosa
import numpy as np
from audio.drummer_v3 import DrumDetectionConfig
from audio.drum_classification import DrumEvent, empty_drum_streams, stream_key_for_type
from audio.drummer_v3 import analyze_drummer_samples


def detect_drum_event_streams(y: np.ndarray, sr: int, config: DrumDetectionConfig | None = None) -> dict[str, list[DrumEvent]]:
    streams = empty_drum_streams()
    if np.asarray(y).size == 0 or sr <= 0:
        return streams
    kwargs = {} if config is None else {"config": config}
    events, _ = analyze_drummer_samples(y, sr, **kwargs)
    for event in events:
        streams[stream_key_for_type(event.drum_type)].append(event)
    return streams


def detect_drum_event_streams_from_file(
    path: Path,
    config: DrumDetectionConfig | None = None,
    log_fn: Callable[[str], None] | None = None,
    *,
    separated_stem: bool = False,
) -> dict[str, list[DrumEvent]]:
    """Detect typed drum events from a file.

    ``separated_stem`` declares that ``path`` is an isolated drum stem. Only then
    are ride and floor-tom co-hits recovered, and only then do detector errors
    propagate: a production stem that cannot be analysed must not silently
    become an empty drum performance.
    """
    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)
        y = np.asarray(y, dtype=np.float32)
        sr = int(sr)
        streams = detect_drum_event_streams(y, sr, config)
        if separated_stem:
            from audio.drum_stem_cohits import detect_stem_cohits
            existing = [event for events in streams.values() for event in events]
            added, report = detect_stem_cohits(y, sr, existing)
            for event in added:
                streams[stream_key_for_type(event.drum_type)].append(event)
            for key, events in streams.items():
                streams[key] = sorted(events, key=lambda item: item.timestamp)
            if log_fn is not None:
                log_fn(f"Drum stem co-hits: measured={report['measured']} added={report['added']} deduped={report['deduped']}")
        if log_fn is not None:
            log_fn(f"Drum intelligence (canonical V3): { {key: len(value) for key, value in streams.items()} }")
        return streams
    except Exception as exc:
        if separated_stem:
            raise
        if log_fn is not None:
            log_fn(f"Drum intelligence skipped: {exc}")
        return empty_drum_streams()
