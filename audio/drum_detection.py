from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import librosa
import numpy as np

from audio.drum_classification import DrumClassifierThresholds, DrumEvent, empty_drum_streams, score_drum_hit_families, stream_key_for_type


@dataclass(frozen=True)
class DrumDetectionConfig:
    onset_delta: float = 0.045
    onset_wait: int = 1
    min_gap_ms: int = 30
    low_confidence_min: float = 0.34
    multi_hit_confidence_min: float = 0.46
    multi_hit_score_window: float = 0.14
    max_hits_per_onset: int = 3
    spectral_flux_delta: float = 0.05
    band_flux_delta: float = 0.03
    band_flux_candidate_min: float = 0.20
    detector_tolerance_frames: int = 1
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


def _band_centroid(freqs: np.ndarray, spectrum: np.ndarray, low: float, high: float) -> float:
    mask = (freqs >= low) & (freqs < high)
    if not np.any(mask):
        return 0.0
    band = spectrum[mask]
    total = float(np.sum(band))
    if total <= 1e-9:
        return 0.0
    return float(np.sum(freqs[mask] * band) / total)


def _compress_events(events: list[DrumEvent], min_gap_ms: int) -> list[DrumEvent]:
    """Collapse near-duplicate detector candidates independently per family."""
    by_type: dict[str, list[DrumEvent]] = {}
    for event in sorted(events, key=lambda item: (item.timestamp, item.drum_type)):
        bucket = by_type.setdefault(event.drum_type, [])
        if bucket and event.timestamp_ms - bucket[-1].timestamp_ms < min_gap_ms:
            previous = bucket[-1]
            if (event.velocity, event.confidence) > (previous.velocity, previous.confidence):
                bucket[-1] = event
            continue
        bucket.append(event)
    return sorted(
        (event for bucket in by_type.values() for event in bucket),
        key=lambda item: (item.timestamp, item.drum_type),
    )


def _cluster_id(timestamp_ms: int, previous_ms: int | None, current_cluster: int, gap_ms: int) -> tuple[int, int]:
    if previous_ms is None or timestamp_ms - previous_ms > gap_ms:
        current_cluster += 1
    return current_cluster, current_cluster


def _spectral_flux_envelope(stft: np.ndarray) -> np.ndarray:
    """Return normalized positive spectral flux for an STFT magnitude matrix."""
    matrix = np.asarray(stft, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] == 0:
        return np.asarray([], dtype=float)
    flux = np.zeros(matrix.shape[1], dtype=float)
    if matrix.shape[1] > 1:
        positive_delta = np.maximum(0.0, matrix[:, 1:] - matrix[:, :-1])
        flux[1:] = np.sum(positive_delta, axis=0)
    return _norm01(flux)


def _band_flux_envelope(
    stft: np.ndarray,
    freqs: np.ndarray,
    low_hz: float,
    high_hz: float,
) -> np.ndarray:
    """Return normalized positive spectral flux for one frequency band."""
    matrix = np.asarray(stft, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] == 0:
        return np.asarray([], dtype=float)
    mask = (freqs >= float(low_hz)) & (freqs < float(high_hz))
    if not np.any(mask):
        return np.zeros(matrix.shape[1], dtype=float)
    band = matrix[mask, :]
    flux = np.zeros(matrix.shape[1], dtype=float)
    if matrix.shape[1] > 1:
        flux[1:] = np.sum(np.maximum(0.0, band[:, 1:] - band[:, :-1]), axis=0)
    return _norm01(flux)


def _peak_frames(envelope: np.ndarray, *, delta: float, wait: int) -> np.ndarray:
    if envelope.size == 0:
        return np.asarray([], dtype=int)
    return np.asarray(
        librosa.util.peak_pick(
            envelope,
            pre_max=1,
            post_max=1,
            pre_avg=2,
            post_avg=2,
            delta=max(0.0, float(delta)),
            wait=max(1, int(wait)),
        ),
        dtype=int,
    )


def _low_flux_peak_hz(
    original_stft: np.ndarray,
    freqs: np.ndarray,
    frame: int,
) -> float:
    """Estimate the newly arriving low-frequency resonance at one frame."""
    if original_stft.ndim != 2 or frame < 0 or frame >= original_stft.shape[1]:
        return 0.0
    current = original_stft[:, frame]
    if frame > 0:
        delta = np.maximum(0.0, current - original_stft[:, frame - 1])
    else:
        delta = current
    mask = (freqs >= 35.0) & (freqs <= 350.0)
    if not np.any(mask):
        return 0.0
    band = delta[mask]
    if band.size == 0 or float(np.max(band)) <= 1e-9:
        return 0.0
    return float(freqs[mask][int(np.argmax(band))])


def _detector_votes(
    frame: int,
    onset_frames: set[int],
    spectral_flux_frames: set[int],
    tolerance_frames: int,
) -> tuple[float, float, float]:
    """Return onset, spectral-flux and agreement evidence for one candidate."""
    tolerance = max(0, int(tolerance_frames))

    def nearby(candidates: set[int]) -> float:
        return 1.0 if any((frame + offset) in candidates for offset in range(-tolerance, tolerance + 1)) else 0.0

    onset_vote = nearby(onset_frames)
    spectral_flux_vote = nearby(spectral_flux_frames)
    return onset_vote, spectral_flux_vote, onset_vote + spectral_flux_vote


def _select_supported_families(
    scores: dict[str, float],
    config: DrumDetectionConfig,
) -> list[tuple[str, float]]:
    """Select compatible drum families from one onset.

    A single physical onset can contain multiple instruments (for example
    kick + crash). Hi-hat and cymbal are treated as alternative high-band
    decay interpretations so they are never emitted together for one onset.
    """
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] < config.low_confidence_min:
        return []

    selected: list[tuple[str, float]] = [ranked[0]]
    top_score = ranked[0][1]
    high_band_selected = ranked[0][0] in {"hihat", "cymbal"}
    for family, score in ranked[1:]:
        if len(selected) >= max(1, int(config.max_hits_per_onset)):
            break
        if score < config.multi_hit_confidence_min:
            continue
        if (top_score - score) > config.multi_hit_score_window:
            continue
        if family in {"hihat", "cymbal"} and high_band_selected:
            continue
        selected.append((family, score))
        if family in {"hihat", "cymbal"}:
            high_band_selected = True
    return selected


def detect_drum_event_streams(
    y: np.ndarray,
    sr: int,
    config: DrumDetectionConfig = DrumDetectionConfig(),
    *,
    source_label: str = "drum_detection",
) -> dict[str, list[DrumEvent]]:
    y = np.asarray(y, dtype=np.float32).reshape(-1)
    if y.size == 0 or sr <= 0:
        return empty_drum_streams()
    harmonic, perc = librosa.effects.hpss(y)
    hop = 512
    n_fft = 2048
    onset_env = librosa.onset.onset_strength(y=perc, sr=sr, hop_length=hop)
    if onset_env.size == 0:
        return empty_drum_streams()
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=hop,
        backtrack=False,
        delta=config.onset_delta,
        wait=max(1, config.onset_wait),
    )
    if onset_frames.size == 0 and config.prefer_recall:
        peaks = librosa.util.peak_pick(
            _norm01(onset_env),
            pre_max=1,
            post_max=1,
            pre_avg=2,
            post_avg=2,
            delta=0.025,
            wait=1,
        )
        onset_frames = np.asarray(peaks, dtype=int)

    stft = np.abs(librosa.stft(perc, n_fft=n_fft, hop_length=hop))
    original_stft = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    spectral_flux_env = _spectral_flux_envelope(stft)
    spectral_flux_frames = _peak_frames(
        spectral_flux_env,
        delta=config.spectral_flux_delta,
        wait=config.onset_wait,
    )
    low_flux_env = _band_flux_envelope(original_stft, freqs, 20.0, 220.0)
    mid_low_flux_env = _band_flux_envelope(original_stft, freqs, 120.0, 700.0)
    high_flux_env = _band_flux_envelope(original_stft, freqs, 2500.0, min(sr / 2, 14000.0))
    low_flux_frames = _peak_frames(
        low_flux_env,
        delta=config.band_flux_delta,
        wait=config.onset_wait,
    )
    mid_low_flux_frames = _peak_frames(
        mid_low_flux_env,
        delta=config.band_flux_delta,
        wait=config.onset_wait,
    )
    low_flux_frames = np.asarray(
        [
            int(frame)
            for frame in low_flux_frames
            if int(frame) < len(low_flux_env)
            and float(low_flux_env[int(frame)]) >= config.band_flux_candidate_min
        ],
        dtype=int,
    )
    mid_low_flux_frames = np.asarray(
        [
            int(frame)
            for frame in mid_low_flux_frames
            if int(frame) < len(mid_low_flux_env)
            and float(mid_low_flux_env[int(frame)]) >= config.band_flux_candidate_min
        ],
        dtype=int,
    )

    onset_frame_set = {int(frame) for frame in onset_frames}
    spectral_flux_frame_set = {int(frame) for frame in spectral_flux_frames}
    low_flux_frame_set = {int(frame) for frame in low_flux_frames}
    mid_low_flux_frame_set = {int(frame) for frame in mid_low_flux_frames}
    frames = sorted(
        onset_frame_set
        | spectral_flux_frame_set
        | low_flux_frame_set
        | mid_low_flux_frame_set
    )
    harmonic_rms = librosa.feature.rms(y=harmonic, hop_length=hop)[0]
    rms = librosa.feature.rms(y=perc, hop_length=hop)[0]
    rms01 = _norm01(rms)
    onset01 = _norm01(onset_env)
    raw_events: list[DrumEvent] = []
    previous_ms: int | None = None
    cluster = -1
    for frame in (int(frame) for frame in frames if int(frame) < stft.shape[1]):
        spectrum = stft[:, frame]
        total = float(np.sum(spectrum)) + 1e-9
        low = _band_energy(freqs, spectrum, 20, 250)
        mid_low = _band_energy(freqs, spectrum, 160, 700)
        mid = _band_energy(freqs, spectrum, 700, 2500)
        high = _band_energy(freqs, spectrum, 2500, min(sr / 2, 14000))
        centroid = float(librosa.feature.spectral_centroid(S=spectrum.reshape(-1, 1), sr=sr)[0, 0])
        spread = float(librosa.feature.spectral_bandwidth(S=spectrum.reshape(-1, 1), sr=sr)[0, 0])
        flatness = float(librosa.feature.spectral_flatness(S=spectrum.reshape(-1, 1))[0, 0])
        low_centroid = _band_centroid(freqs, spectrum, 20, 700)
        p_rms = float(rms[frame]) if frame < len(rms) else 0.0
        h_rms = float(harmonic_rms[frame]) if frame < len(harmonic_rms) else 0.0
        percussive_ratio = p_rms / max(p_rms + h_rms, 1e-9)

        # Compare the short post-onset RMS to the later tail instead of using
        # absolute RMS. This makes the feature describe the hit's decay shape,
        # which is much more useful for separating hats from sustained crashes.
        attack_slice = rms01[frame : min(len(rms01), frame + 2)]
        tail_slice = rms01[min(len(rms01), frame + 4) : min(len(rms01), frame + 10)]
        attack_level = float(np.mean(attack_slice)) if attack_slice.size else 0.0
        tail_level = float(np.mean(tail_slice)) if tail_slice.size else 0.0
        decay = tail_level / max(attack_level, 1e-6)

        previous = float(onset01[frame - 1]) if frame > 0 and frame - 1 < len(onset01) else 0.0
        current = float(onset01[frame]) if frame < len(onset01) else 0.0
        sharp = max(0.0, current - previous)
        onset_vote, spectral_flux_vote, detector_agreement = _detector_votes(
            frame,
            onset_frame_set,
            spectral_flux_frame_set,
            config.detector_tolerance_frames,
        )
        low_flux_vote = 1.0 if any(
            (frame + offset) in low_flux_frame_set
            for offset in range(-config.detector_tolerance_frames, config.detector_tolerance_frames + 1)
        ) else 0.0
        mid_low_flux_vote = 1.0 if any(
            (frame + offset) in mid_low_flux_frame_set
            for offset in range(-config.detector_tolerance_frames, config.detector_tolerance_frames + 1)
        ) else 0.0
        low_flux_peak = _low_flux_peak_hz(original_stft, freqs, frame)
        low_flux_strength = float(low_flux_env[frame]) if frame < len(low_flux_env) else 0.0
        mid_low_flux_strength = float(mid_low_flux_env[frame]) if frame < len(mid_low_flux_env) else 0.0
        high_flux_strength = float(high_flux_env[frame]) if frame < len(high_flux_env) else 0.0
        features = {
            "low_ratio": low / total,
            "mid_low_ratio": mid_low / total,
            "mid_ratio": mid / total,
            "high_ratio": high / total,
            "centroid_hz": centroid,
            "low_centroid_hz": low_centroid,
            "low_flux_peak_hz": low_flux_peak,
            "low_flux_strength": low_flux_strength,
            "mid_low_flux_strength": mid_low_flux_strength,
            "high_flux_strength": high_flux_strength,
            "spectral_spread01": min(1.0, spread / max(1.0, sr / 2)),
            "spectral_flatness": min(1.0, flatness),
            "percussive_ratio": min(1.0, percussive_ratio),
            "transient_sharpness": min(1.0, sharp),
            "decay_profile": min(1.0, decay),
            "detector_onset": onset_vote,
            "detector_spectral_flux": spectral_flux_vote,
            "detector_low_flux": low_flux_vote,
            "detector_mid_low_flux": mid_low_flux_vote,
            "detector_band_flux_count": low_flux_vote + mid_low_flux_vote,
            "detector_agreement": detector_agreement,
        }
        thresholds = DrumClassifierThresholds(low_confidence_min=config.low_confidence_min)
        family_scores = score_drum_hit_families(features, thresholds)
        supported = _select_supported_families(family_scores, config)
        timestamp = float(librosa.frames_to_time(frame, sr=sr, hop_length=hop))
        timestamp_ms = int(round(timestamp * 1000.0))
        cluster, cluster_id = _cluster_id(timestamp_ms, previous_ms, cluster, config.cluster_gap_ms)
        previous_ms = timestamp_ms
        velocity = max(
            0.08,
            min(
                1.0,
                (float(rms01[frame]) if frame < len(rms01) else current) * 0.65 + current * 0.35,
            ),
        )
        evidence = {key: round(float(value), 4) for key, value in features.items()}
        evidence.update({f"score_{name}": round(float(score), 4) for name, score in family_scores.items()})
        evidence["family_support_count"] = float(len(supported))
        if not supported:
            raw_events.append(
                DrumEvent(
                    timestamp=round(timestamp, 4),
                    velocity=round(velocity, 3),
                    confidence=round(max(family_scores.values(), default=0.0), 3),
                    frequency_band_info=evidence,
                    cluster_id=cluster_id,
                    drum_type="drum_bus",
                    source=source_label,
                )
            )
        else:
            for drum_type, confidence in supported:
                raw_events.append(
                    DrumEvent(
                        timestamp=round(timestamp, 4),
                        velocity=round(velocity, 3),
                        confidence=round(float(confidence), 3),
                        frequency_band_info=evidence,
                        cluster_id=cluster_id,
                        drum_type=drum_type,
                        source=source_label,
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
    *,
    source_label: str = "drum_detection",
) -> dict[str, list[DrumEvent]]:
    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)
        streams = detect_drum_event_streams(
            np.asarray(y, dtype=np.float32),
            int(sr),
            config,
            source_label=source_label,
        )
        if log_fn is not None:
            counts = {key: len(value) for key, value in streams.items()}
            log_fn(f"Drum intelligence: {counts}")
        return streams
    except Exception as exc:
        if log_fn is not None:
            log_fn(f"Drum intelligence skipped: {exc}")
        return empty_drum_streams()
