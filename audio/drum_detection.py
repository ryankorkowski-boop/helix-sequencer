"""Compatibility entry points backed by the canonical V3 typed-event detector."""
from pathlib import Path
from typing import Callable
import librosa
import numpy as np
from audio.archive.drum_detection_legacy import DrumDetectionConfig
from audio.drum_classification import DrumEvent, empty_drum_streams, stream_key_for_type
from audio.drummer_v3 import analyze_drummer_samples


def detect_drum_event_streams(y: np.ndarray, sr: int, config: DrumDetectionConfig | None = None) -> dict[str, list[DrumEvent]]:
    streams = empty_drum_streams()
    if np.asarray(y).size == 0 or sr <= 0:
        return streams
    kwargs = {} if config is None else {"onset_delta": config.onset_delta}
    events, _ = analyze_drummer_samples(y, sr, **kwargs)
    for event in events:
        streams[stream_key_for_type(event.drum_type)].append(event)
    return streams


def detect_drum_event_streams_from_file(path: Path, config: DrumDetectionConfig | None = None, log_fn: Callable[[str], None] | None = None) -> dict[str, list[DrumEvent]]:
    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)
        streams = detect_drum_event_streams(y, sr, config)
        if log_fn is not None:
            log_fn(f"Drum intelligence (canonical V3): { {key: len(value) for key, value in streams.items()} }")
        return streams
    except Exception as exc:
        if log_fn is not None:
            log_fn(f"Drum intelligence skipped: {exc}")
        return empty_drum_streams()
