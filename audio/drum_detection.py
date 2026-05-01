from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import librosa
import numpy as np

from audio.drum_classification import DrumClassifierThresholds, DrumEvent, classify_drum_hit, empty_drum_streams, stream_key_for_type


@dataclass(frozen=True)
class DrumDetectionConfig:
    onset_delta: float = 0.045
    onset_wait: int = 1
    min_gap_ms: int = 22
    low_confidence_min: float = 0.34
    cluster_gap_ms: int = 95
    prefer_recall: bool = True


def _norm01(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return arr
    top = float(np.max(np.abs(arr)))
    return arr / top if top > 1e-9 else np.zeros_like(arr)


def _band_energy(freqs: np.ndarray, spectrum: np.ndarray, low: float, high: float) -> float:
    mask = (freqs >= low) & (freqs < high)
    if not np.any(mask):
        return 0.0
    return float(np.sum(spectrum[mask]))


def _compress_events(events: list[DrumEvent], min_gap_ms: int) -> list[DrumEvent]:
    out: list[DrumEvent] = []
    for event in sorted(events, key=lambda item: (item.timestamp, item.drum_type)):
        if out and event.timestamp_ms - out[-1].timestamp_ms < min_gap_ms and event.drum_type == out[-1].drum_type:
            if event.velocity > out[-1].velocity:
                out[-1] = event
            continue
        out.append(event)
    return out


def _cluster_id(timestamp_ms: int, previous_ms: int | None, current_cluster: int, gap_ms: int) -> tuple[int, int]:
    if previous_ms is None or timestamp_ms - previous_ms > gap_ms:
        current_cluster += 1
    return current_cluster, current_cluster


def detect_drum_event_streams(
    y: np.ndarray,
    sr: int,
    config: DrumDetectionConfig = DrumDetectionConfig(),
) -> dict[str, list[DrumEvent]]:
    y = np.asarray(y, dtype=np.float32).reshape(-1)
    if y.size == 0 or sr <= 0:
        return empty_drum_streams()
    _, perc = librosa.effects.hpss(y)
    hop = 512
    n_fft = 2048
    onset_env = librosa.onset.onset_strength(y=perc, sr=sr, hop_length=hop)
    if onset_env.size == 0:
        return empty_drum_streams()
    frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=hop,
        backtrack=False,
        delta=config.onset_delta,
        wait=max(1, config.onset_wait),
    )
    if frames.size == 0 and config.prefer_recall:
        peaks = librosa.util.peak_pick(_norm01(onset_env), pre_max=1, post_max=1, pre_avg=2, post_avg=2, delta=0.025, wait=1)
        frames = np.asarray(peaks, dtype=int)
    stft = np.abs(librosa.stft(perc, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    rms = librosa.feature.rms(y=perc, hop_length=hop)[0]
    rms01 = _norm01(rms)
    onset01 = _norm01(onset_env)
    raw_events: list[DrumEvent] = []
    previous_ms: int | None = None
    cluster = -1
    for frame in sorted(set(int(frame) for frame in frames if int(frame) < stft.shape[1])):
        spectrum = stft[:, frame]
        total = float(np.sum(spectrum)) + 1e-9
        low = _band_energy(freqs, spectrum, 20, 160)
        mid_low = _band_energy(freqs, spectrum, 160, 700)
        mid = _band_energy(freqs, spectrum, 700, 2500)
        high = _band_energy(freqs, spectrum, 2500, min(sr / 2, 14000))
        centroid = float(librosa.feature.spectral_centroid(S=spectrum.reshape(-1, 1), sr=sr)[0, 0])
        spread = float(librosa.feature.spectral_bandwidth(S=spectrum.reshape(-1, 1), sr=sr)[0, 0])
        decay_slice = rms01[frame : min(len(rms01), frame + 8)]
        decay = float(np.mean(decay_slice)) if decay_slice.size else 0.0
        previous = float(onset01[frame - 1]) if frame > 0 and frame - 1 < len(onset01) else 0.0
        current = float(onset01[frame]) if frame < len(onset01) else 0.0
        sharp = max(0.0, current - previous)
        features = {
            "low_ratio": low / total,
            "mid_low_ratio": mid_low / total,
            "mid_ratio": mid / total,
            "high_ratio": high / total,
            "centroid_hz": centroid,
            "spectral_spread01": min(1.0, spread / max(1.0, sr / 2)),
            "transient_sharpness": min(1.0, sharp),
            "decay_profile": min(1.0, decay),
        }
        drum_type, confidence = classify_drum_hit(
            features,
            DrumClassifierThresholds(low_confidence_min=config.low_confidence_min),
        )
        timestamp = float(librosa.frames_to_time(frame, sr=sr, hop_length=hop))
        timestamp_ms = int(round(timestamp * 1000.0))
        cluster, cluster_id = _cluster_id(timestamp_ms, previous_ms, cluster, config.cluster_gap_ms)
        previous_ms = timestamp_ms
        velocity = max(0.08, min(1.0, (float(rms01[frame]) if frame < len(rms01) else current) * 0.65 + current * 0.35))
        raw_events.append(
            DrumEvent(
                timestamp=round(timestamp, 4),
                velocity=round(velocity, 3),
                confidence=confidence,
                frequency_band_info={key: round(float(value), 4) for key, value in features.items()},
                cluster_id=cluster_id,
                drum_type=drum_type,
            )
        )
    streams = empty_drum_streams()
    for event in _compress_events(raw_events, config.min_gap_ms):
        streams[stream_key_for_type(event.drum_type)].append(event)
    return streams


def detect_drum_event_streams_from_file(
    path: Path,
    config: DrumDetectionConfig = DrumDetectionConfig(),
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, list[DrumEvent]]:
    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)
        streams = detect_drum_event_streams(np.asarray(y, dtype=np.float32), int(sr), config)
        if log_fn is not None:
            counts = {key: len(value) for key, value in streams.items()}
            log_fn(f"Drum intelligence: {counts}")
        return streams
    except Exception as exc:
        if log_fn is not None:
            log_fn(f"Drum intelligence skipped: {exc}")
        return empty_drum_streams()
