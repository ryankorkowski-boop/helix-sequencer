from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core import chronoflow as chronoflow_engine
from core.lazy_imports import LazyModule, optional_import

librosa = LazyModule("librosa")
np = LazyModule("numpy")


@dataclass
class BirdsongRunResult:
    audio_path: Path
    json_path: Path
    csv_path: Path
    ply_path: Path | None
    preview_html_path: Path | None
    mapping_json_path: Path
    frame_count: int
    tempo_bpm: float
    reduction_method: str


def _log(log_fn: Callable[[str], None] | None, message: str) -> None:
    if log_fn is None:
        return
    try:
        log_fn(message)
    except Exception:
        pass


def _norm01(values: Any) -> Any:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size == 0:
        return np.zeros((0,), dtype=float)
    finite = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    lo = float(np.min(finite))
    hi = float(np.max(finite))
    if hi <= lo + 1e-9:
        return np.zeros_like(finite, dtype=float)
    return np.clip((finite - lo) / (hi - lo), 0.0, 1.0)


def _align_curve(values: Any, target_len: int) -> Any:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if target_len <= 0:
        return np.zeros((0,), dtype=float)
    if arr.size == target_len:
        return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    if arr.size == 0:
        return np.zeros((target_len,), dtype=float)
    if arr.size == 1:
        return np.full((target_len,), float(arr[0]), dtype=float)
    src_idx = np.linspace(0.0, 1.0, arr.size)
    dst_idx = np.linspace(0.0, 1.0, target_len)
    return np.interp(dst_idx, src_idx, np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0))


def _rolling_mean(values: Any, width: int) -> Any:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size == 0 or width <= 1:
        return arr
    kernel = np.ones((max(1, int(width)),), dtype=float)
    kernel = kernel / float(np.sum(kernel))
    return np.convolve(arr, kernel, mode="same")


def _optional_basic_pitch_contour(audio_path: Path, frame_times_s: Any) -> tuple[Any, Any]:
    target_len = len(np.asarray(frame_times_s, dtype=float).reshape(-1))
    pitch_hz = np.full((target_len,), np.nan, dtype=float)
    confidence = np.zeros((target_len,), dtype=float)
    inference = optional_import("basic_pitch.inference")
    if inference is None:
        return pitch_hz, confidence
    try:
        predict = getattr(inference, "predict", None)
        if predict is None:
            return pitch_hz, confidence
        model_output, midi_data, _ = predict(str(audio_path))
        if midi_data is None:
            return pitch_hz, confidence
        notes = list(getattr(midi_data, "instruments", []) or [])
        if not notes:
            return pitch_hz, confidence
        frame_times = np.asarray(frame_times_s, dtype=float).reshape(-1)
        for instrument in notes:
            for note in list(getattr(instrument, "notes", []) or []):
                start_s = float(getattr(note, "start", 0.0) or 0.0)
                end_s = max(start_s + 1e-3, float(getattr(note, "end", start_s + 0.1) or (start_s + 0.1)))
                midi = float(getattr(note, "pitch", 60.0) or 60.0)
                velocity = float(getattr(note, "velocity", 80.0) or 80.0) / 127.0
                hz = float(librosa.midi_to_hz(midi))
                mask = (frame_times >= start_s) & (frame_times < end_s)
                pitch_hz[mask] = hz
                confidence[mask] = max(0.0, min(1.0, velocity))
        return pitch_hz, confidence
    except Exception:
        return pitch_hz, confidence


def _estimate_syncopation(onset_curve01: Any, beat_phase01: Any) -> float:
    onset = np.asarray(onset_curve01, dtype=float).reshape(-1)
    phase = np.asarray(beat_phase01, dtype=float).reshape(-1)
    usable = min(onset.size, phase.size)
    if usable <= 4:
        return 0.0
    onbeat_mask = phase[:usable] <= 0.2
    offbeat_mask = (phase[:usable] >= 0.38) & (phase[:usable] <= 0.68)
    if not np.any(offbeat_mask):
        return 0.0
    onbeat_energy = float(np.mean(onset[:usable][onbeat_mask])) if np.any(onbeat_mask) else 0.0
    offbeat_energy = float(np.mean(onset[:usable][offbeat_mask]))
    return float(max(0.0, min(1.0, (offbeat_energy - (onbeat_energy * 0.55)))))


def extract_frame_features(
    audio_path: Path,
    *,
    hop_length: int = 512,
    n_mfcc: int = 13,
    use_basic_pitch: bool = False,
) -> dict[str, Any]:
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    y = np.asarray(y, dtype=float)
    duration_s = float(len(y) / max(1, int(sr)))

    stft = np.asarray(librosa.stft(y, n_fft=2048, hop_length=hop_length), dtype=complex)
    magnitude = np.abs(stft)
    frame_count = int(magnitude.shape[1]) if magnitude.ndim == 2 else 0
    frame_times_s = np.asarray(librosa.frames_to_time(np.arange(frame_count), sr=sr, hop_length=hop_length), dtype=float)

    onset_env = np.asarray(librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length), dtype=float)
    onset_env = _align_curve(onset_env, frame_count)
    onset_frames = np.asarray(
        librosa.onset.onset_detect(
            onset_envelope=onset_env,
            sr=sr,
            hop_length=hop_length,
            units="frames",
            backtrack=False,
        ),
        dtype=int,
    )
    onset_ms = [int(round(float(frame_times_s[idx]) * 1000.0)) for idx in onset_frames if 0 <= int(idx) < frame_count]

    tempo_bpm, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    tempo_arr = np.asarray(tempo_bpm, dtype=float).reshape(-1)
    tempo_value = float(np.mean(tempo_arr)) if tempo_arr.size else 0.0
    beat_frames = np.asarray(beat_frames, dtype=int).reshape(-1)
    beat_ms = [int(round(float(frame_times_s[idx]) * 1000.0)) for idx in beat_frames if 0 <= int(idx) < frame_count]

    centroid = _align_curve(librosa.feature.spectral_centroid(S=magnitude, sr=sr)[0], frame_count)
    bandwidth = _align_curve(librosa.feature.spectral_bandwidth(S=magnitude, sr=sr)[0], frame_count)
    contrast = np.asarray(librosa.feature.spectral_contrast(S=magnitude, sr=sr), dtype=float)
    contrast_mean = _align_curve(np.mean(contrast, axis=0) if contrast.size else np.zeros((frame_count,), dtype=float), frame_count)
    rms = _align_curve(librosa.feature.rms(y=y, hop_length=hop_length)[0], frame_count)
    chroma = np.asarray(librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length), dtype=float)
    if chroma.ndim != 2 or chroma.shape[0] != 12:
        chroma = np.zeros((12, frame_count), dtype=float)
    if chroma.shape[1] != frame_count:
        aligned = np.zeros((12, frame_count), dtype=float)
        for row in range(12):
            aligned[row] = _align_curve(chroma[row], frame_count)
        chroma = aligned

    mfcc = np.asarray(librosa.feature.mfcc(y=y, sr=sr, hop_length=hop_length, n_mfcc=n_mfcc), dtype=float)
    if mfcc.ndim != 2:
        mfcc = np.zeros((n_mfcc, frame_count), dtype=float)
    if mfcc.shape[1] != frame_count:
        aligned = np.zeros((mfcc.shape[0], frame_count), dtype=float)
        for row in range(mfcc.shape[0]):
            aligned[row] = _align_curve(mfcc[row], frame_count)
        mfcc = aligned
    mfcc_delta = np.asarray(librosa.feature.delta(mfcc), dtype=float) if mfcc.size else np.zeros_like(mfcc)

    pitch_hz = np.full((frame_count,), np.nan, dtype=float)
    pitch_conf = np.zeros((frame_count,), dtype=float)
    if use_basic_pitch:
        bp_pitch_hz, bp_conf = _optional_basic_pitch_contour(audio_path, frame_times_s)
        if np.isfinite(bp_pitch_hz).any():
            pitch_hz = _align_curve(bp_pitch_hz, frame_count)
            pitch_conf = _align_curve(bp_conf, frame_count)
    if not np.isfinite(pitch_hz).any():
        pip_pitches, pip_mags = librosa.piptrack(S=magnitude, sr=sr, hop_length=hop_length, fmin=55.0, fmax=2200.0)
        pip_pitches = np.asarray(pip_pitches, dtype=float)
        pip_mags = np.asarray(pip_mags, dtype=float)
        if pip_pitches.ndim == 2 and pip_pitches.shape[1] == frame_count:
            for idx in range(frame_count):
                col = pip_mags[:, idx]
                if col.size <= 0:
                    continue
                peak_idx = int(np.argmax(col))
                peak_hz = float(pip_pitches[peak_idx, idx])
                peak_mag = float(col[peak_idx])
                if peak_hz > 0.0:
                    pitch_hz[idx] = peak_hz
                    pitch_conf[idx] = peak_mag
        pitch_conf = _norm01(pitch_conf)

    pitch_midi = np.full((frame_count,), np.nan, dtype=float)
    valid_pitch = pitch_hz > 0.0
    if np.any(valid_pitch):
        pitch_midi[valid_pitch] = librosa.hz_to_midi(pitch_hz[valid_pitch])
    pitch_midi = np.nan_to_num(pitch_midi, nan=float(np.nanmean(pitch_midi)) if np.isfinite(np.nanmean(pitch_midi)) else 60.0)

    beat_phase = np.zeros((frame_count,), dtype=float)
    beat_density = np.zeros((frame_count,), dtype=float)
    if len(beat_ms) >= 2:
        beat_s = np.asarray(beat_ms, dtype=float) / 1000.0
        for i, t_s in enumerate(frame_times_s):
            idx = int(np.searchsorted(beat_s, t_s))
            left_idx = max(0, idx - 1)
            right_idx = min(len(beat_s) - 1, idx)
            if right_idx <= left_idx:
                continue
            span = max(1e-3, beat_s[right_idx] - beat_s[left_idx])
            beat_phase[i] = max(0.0, min(1.0, (t_s - beat_s[left_idx]) / span))
        beat_density = _rolling_mean((onset_env > float(np.nanpercentile(onset_env, 72))).astype(float), width=12)
    rhythm_stability = 0.0
    if len(beat_ms) >= 4:
        intervals = np.diff(np.asarray(beat_ms, dtype=float))
        rhythm_stability = float(max(0.0, min(1.0, 1.0 - (np.std(intervals) / max(1.0, np.mean(intervals))))))
    syncopation = _estimate_syncopation(_norm01(onset_env), beat_phase)

    feature_columns: list[tuple[str, Any]] = [
        ("rms", rms),
        ("onset_strength", onset_env),
        ("spectral_centroid", centroid),
        ("spectral_bandwidth", bandwidth),
        ("spectral_contrast", contrast_mean),
        ("pitch_midi", pitch_midi),
        ("pitch_confidence", pitch_conf),
        ("beat_phase", beat_phase),
        ("rhythm_density", beat_density),
    ]
    for idx in range(min(n_mfcc, mfcc.shape[0])):
        feature_columns.append((f"mfcc_{idx + 1}", mfcc[idx]))
    for idx in range(min(n_mfcc, mfcc_delta.shape[0])):
        feature_columns.append((f"mfcc_delta_{idx + 1}", mfcc_delta[idx]))
    for idx in range(12):
        feature_columns.append((f"chroma_{idx}", chroma[idx]))

    feature_names = [name for name, _values in feature_columns]
    feature_matrix = np.column_stack([_align_curve(values, frame_count) for _name, values in feature_columns]) if frame_count else np.zeros((0, 0), dtype=float)

    return {
        "audio_path": str(audio_path),
        "sample_rate": int(sr),
        "duration_s": round(duration_s, 6),
        "hop_length": int(hop_length),
        "frame_times_s": frame_times_s,
        "frame_count": int(frame_count),
        "feature_names": feature_names,
        "feature_matrix": np.asarray(feature_matrix, dtype=float),
        "onset_ms": onset_ms,
        "beat_ms": beat_ms,
        "tempo_bpm": float(tempo_value),
        "pitch_midi": pitch_midi,
        "pitch_confidence": pitch_conf,
        "rms": rms,
        "onset_strength": onset_env,
        "spectral_centroid": centroid,
        "spectral_bandwidth": bandwidth,
        "spectral_contrast": contrast_mean,
        "rhythm_stability": float(rhythm_stability),
        "syncopation": float(syncopation),
    }


def reduce_dimensions(feature_matrix: Any, *, use_umap: bool = False) -> dict[str, Any]:
    rows = np.asarray(feature_matrix, dtype=float)
    if rows.ndim != 2 or rows.shape[0] <= 0:
        return {
            "coords_2d": np.zeros((0, 2), dtype=float),
            "coords_3d": np.zeros((0, 3), dtype=float),
            "method": "empty",
            "explained_variance_ratio": [],
            "scaler": {"type": "none"},
        }
    safe = np.nan_to_num(rows, nan=0.0, posinf=0.0, neginf=0.0)
    scaler_module = optional_import("sklearn.preprocessing")
    pca_module = optional_import("sklearn.decomposition")
    if scaler_module is not None and pca_module is not None:
        scaler = scaler_module.StandardScaler()
        scaled = scaler.fit_transform(safe)
        pca3 = pca_module.PCA(n_components=min(3, scaled.shape[0], scaled.shape[1]))
        coords_3d = pca3.fit_transform(scaled)
        if coords_3d.shape[1] < 3:
            coords_3d = np.pad(coords_3d, ((0, 0), (0, 3 - coords_3d.shape[1])), mode="constant")
        pca2 = pca_module.PCA(n_components=min(2, scaled.shape[0], scaled.shape[1]))
        coords_2d = pca2.fit_transform(scaled)
        if coords_2d.shape[1] < 2:
            coords_2d = np.pad(coords_2d, ((0, 0), (0, 2 - coords_2d.shape[1])), mode="constant")
        method = "pca"
        if use_umap:
            umap_module = optional_import("umap")
            if umap_module is not None:
                try:
                    reducer = umap_module.UMAP(n_components=3, random_state=42)
                    coords_3d = np.asarray(reducer.fit_transform(scaled), dtype=float)
                    if coords_3d.shape[1] < 3:
                        coords_3d = np.pad(coords_3d, ((0, 0), (0, 3 - coords_3d.shape[1])), mode="constant")
                    method = "umap"
                except Exception:
                    pass
        return {
            "coords_2d": np.asarray(coords_2d, dtype=float),
            "coords_3d": np.asarray(coords_3d, dtype=float),
            "method": method,
            "explained_variance_ratio": [float(value) for value in getattr(pca3, "explained_variance_ratio_", [])],
            "scaler": {
                "type": "standard",
                "mean": [float(value) for value in np.asarray(getattr(scaler, "mean_", []), dtype=float).tolist()],
                "scale": [float(value) for value in np.asarray(getattr(scaler, "scale_", []), dtype=float).tolist()],
            },
        }
    mean = np.mean(safe, axis=0, keepdims=True)
    std = np.std(safe, axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    normalized = (safe - mean) / std
    _, _s, vh = np.linalg.svd(normalized, full_matrices=False)
    coords_3d = normalized @ vh[: min(3, vh.shape[0])].T
    if coords_3d.shape[1] < 3:
        coords_3d = np.pad(coords_3d, ((0, 0), (0, 3 - coords_3d.shape[1])), mode="constant")
    coords_2d = coords_3d[:, :2]
    return {
        "coords_2d": np.asarray(coords_2d, dtype=float),
        "coords_3d": np.asarray(coords_3d, dtype=float),
        "method": "svd_pca",
        "explained_variance_ratio": [],
        "scaler": {"type": "manual"},
    }


def build_trajectory(features: dict[str, Any], reduction: dict[str, Any]) -> list[dict[str, Any]]:
    times_s = np.asarray(features.get("frame_times_s", []), dtype=float).reshape(-1)
    coords = np.asarray(reduction.get("coords_3d", []), dtype=float)
    if times_s.size <= 0 or coords.size <= 0:
        return []
    usable = min(len(times_s), coords.shape[0])
    intensity = _norm01(features.get("rms", []))
    centroid = _norm01(features.get("spectral_centroid", []))
    contrast = _norm01(features.get("spectral_contrast", []))
    pitch = _norm01(features.get("pitch_midi", []))
    onset = _norm01(features.get("onset_strength", []))
    rhythm_density = _norm01(features.get("feature_matrix", np.zeros((usable, 1), dtype=float))[:, 8] if usable > 0 else [])
    points: list[dict[str, Any]] = []
    for idx in range(usable):
        points.append(
            {
                "frame": int(idx),
                "time_s": round(float(times_s[idx]), 6),
                "time_ms": int(round(float(times_s[idx]) * 1000.0)),
                "x": round(float(coords[idx, 0]), 6),
                "y": round(float(coords[idx, 1]), 6),
                "z": round(float(coords[idx, 2]), 6),
                "intensity": round(float(intensity[idx]) if idx < len(intensity) else 0.0, 5),
                "pitch": round(float(pitch[idx]) if idx < len(pitch) else 0.0, 5),
                "centroid": round(float(centroid[idx]) if idx < len(centroid) else 0.0, 5),
                "contrast": round(float(contrast[idx]) if idx < len(contrast) else 0.0, 5),
                "onset_strength": round(float(onset[idx]) if idx < len(onset) else 0.0, 5),
                "rhythm_density": round(float(rhythm_density[idx]) if idx < len(rhythm_density) else 0.0, 5),
            }
        )
    return points


def _candidate_score(profile: dict[str, float], candidate: dict[str, tuple[float, float]]) -> float:
    score = 0.0
    total = 0.0
    for key, (low, high) in candidate.items():
        weight = 1.0
        value = float(profile.get(key, 0.0))
        total += weight
        if low <= value <= high:
            score += weight
        elif value < low:
            span = max(1e-6, low)
            score += max(0.0, 1.0 - ((low - value) / span)) * weight
        else:
            span = max(1e-6, 1.0 - high)
            score += max(0.0, 1.0 - ((value - high) / span)) * weight
    return score / max(1e-6, total)


def build_dynamic_mapping(features: dict[str, Any], trajectory: list[dict[str, Any]]) -> dict[str, Any]:
    times_s = np.asarray(features.get("frame_times_s", []), dtype=float).reshape(-1)
    onset = _norm01(features.get("onset_strength", []))
    intensity = _norm01(features.get("rms", []))
    pitch = _norm01(features.get("pitch_midi", []))
    centroid = _norm01(features.get("spectral_centroid", []))
    bandwidth = _norm01(features.get("spectral_bandwidth", []))
    contrast = _norm01(features.get("spectral_contrast", []))
    rhythm = _norm01(features.get("feature_matrix", np.zeros((len(times_s), 9), dtype=float))[:, 8] if len(times_s) else [])

    candidates: dict[str, dict[str, dict[str, tuple[float, float]]]] = {
        "megatree": {
            "spiral_rise": {
                "tempo": (0.45, 1.0),
                "pitch_motion": (0.50, 1.0),
                "energy": (0.45, 1.0),
                "contrast": (0.20, 0.95),
                "lookahead_onset": (0.30, 1.0),
            },
            "pulse_rings": {"tempo": (0.25, 0.85), "onset": (0.45, 1.0), "energy": (0.40, 1.0), "spread": (0.10, 0.85)},
        },
        "matrix": {
            "particle_trails": {"spread": (0.45, 1.0), "energy": (0.40, 1.0), "motion": (0.30, 1.0), "contrast": (0.25, 0.95)},
            "lyric_projection": {"vocal": (0.50, 1.0), "energy": (0.20, 0.80), "onset": (0.10, 0.70), "spread": (0.10, 0.80)},
        },
        "arches": {
            "pitch_sweep": {"pitch_motion": (0.45, 1.0), "tempo": (0.30, 1.0), "energy": (0.25, 0.90), "contrast": (0.15, 0.85)},
            "rhythm_chase": {"onset": (0.40, 1.0), "tempo": (0.35, 1.0), "energy": (0.30, 1.0), "spread": (0.10, 0.90)},
        },
        "singing_faces": {
            "viseme_phrase": {"vocal": (0.50, 1.0), "energy": (0.20, 0.90), "onset": (0.10, 0.75), "pitch_motion": (0.10, 1.0)},
            "backup_minimal": {"vocal": (0.20, 0.70), "energy": (0.15, 0.70), "onset": (0.05, 0.60), "tempo": (0.10, 1.0)},
        },
        "ac_channels": {
            "drum_robotics": {"onset": (0.50, 1.0), "energy": (0.35, 1.0), "tempo": (0.35, 1.0), "contrast": (0.25, 1.0)},
            "ambient_ramps": {"onset": (0.0, 0.45), "energy": (0.05, 0.65), "tempo": (0.10, 0.70), "spread": (0.20, 1.0)},
        },
        "snowman_band": {
            "instrument_motion": {"onset": (0.45, 1.0), "pitch_motion": (0.30, 1.0), "energy": (0.35, 1.0), "vocal": (0.10, 1.0)},
            "section_sway": {"onset": (0.05, 0.65), "energy": (0.15, 0.80), "tempo": (0.20, 1.0), "spread": (0.10, 0.95)},
        },
        "camera_path": {
            "forward_flight": {
                "motion": (0.25, 1.0),
                "energy": (0.25, 1.0),
                "contrast": (0.20, 1.0),
                "onset": (0.15, 0.95),
                "lookahead_onset": (0.28, 1.0),
            },
            "orbit_hold": {
                "motion": (0.05, 0.55),
                "energy": (0.10, 0.70),
                "spread": (0.10, 0.90),
                "onset": (0.05, 0.60),
                "history_energy": (0.10, 0.72),
            },
        },
    }

    rows: list[dict[str, Any]] = []
    step = max(1, int(len(times_s) / 240)) if len(times_s) else 1
    for idx in range(0, len(times_s), step):
        prev_idx = max(0, idx - 1)
        next_idx = min(len(times_s) - 1, idx + 1)
        history_start = max(0, idx - 6)
        history_end = idx + 1
        lookahead_start = idx
        lookahead_end = min(len(times_s), idx + 7)
        pitch_motion = abs(float(pitch[next_idx]) - float(pitch[prev_idx])) if len(pitch) else 0.0
        motion = 0.0
        if idx < len(trajectory):
            current = trajectory[idx]
            last = trajectory[prev_idx] if prev_idx < len(trajectory) else current
            motion = float(
                ((float(current.get("x", 0.0)) - float(last.get("x", 0.0))) ** 2)
                + ((float(current.get("y", 0.0)) - float(last.get("y", 0.0))) ** 2)
                + ((float(current.get("z", 0.0)) - float(last.get("z", 0.0))) ** 2)
            ) ** 0.5
        profile = {
            "tempo": max(0.0, min(1.0, float(features.get("tempo_bpm", 0.0)) / 180.0)),
            "energy": float(intensity[idx]) if idx < len(intensity) else 0.0,
            "onset": float(onset[idx]) if idx < len(onset) else 0.0,
            "pitch_motion": max(0.0, min(1.0, pitch_motion * 4.0)),
            "contrast": float(contrast[idx]) if idx < len(contrast) else 0.0,
            "spread": float(bandwidth[idx]) if idx < len(bandwidth) else 0.0,
            "vocal": float(_norm01(features.get("pitch_confidence", []))[idx]) if idx < len(features.get("pitch_confidence", [])) else 0.0,
            "motion": max(0.0, min(1.0, motion)),
            "history_energy": float(np.mean(intensity[history_start:history_end])) if len(intensity) else 0.0,
            "lookahead_onset": float(np.max(onset[lookahead_start:lookahead_end])) if len(onset) else 0.0,
        }
        choice: dict[str, Any] = {"time_ms": int(round(float(times_s[idx]) * 1000.0)), "scores": {}}
        for group, options in candidates.items():
            scored = [
                {"effect": effect_name, "score": round(float(_candidate_score(profile, rules)), 4)}
                for effect_name, rules in options.items()
            ]
            scored.sort(key=lambda item: float(item["score"]), reverse=True)
            choice["scores"][group] = scored
        rows.append(choice)
    return {"time_windows": rows, "candidate_catalog": {group: list(options.keys()) for group, options in candidates.items()}}


def _write_features_csv(path: Path, times_s: Any, feature_names: list[str], matrix: Any) -> None:
    rows = np.asarray(matrix, dtype=float)
    times = np.asarray(times_s, dtype=float).reshape(-1)
    usable = min(len(times), rows.shape[0]) if rows.ndim == 2 else 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_s", *feature_names])
        for idx in range(usable):
            writer.writerow([f"{float(times[idx]):.6f}", *[f"{float(value):.8f}" for value in rows[idx]]])


def _write_trajectory_ply(path: Path, trajectory: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = len(trajectory)
    lines = [
        "ply",
        "format ascii 1.0",
        f"element vertex {count}",
        "property float x",
        "property float y",
        "property float z",
        "property uchar red",
        "property uchar green",
        "property uchar blue",
        "end_header",
    ]
    for point in trajectory:
        intensity = max(0.0, min(1.0, float(point.get("intensity", 0.0))))
        pitch = max(0.0, min(1.0, float(point.get("pitch", 0.0))))
        centroid = max(0.0, min(1.0, float(point.get("centroid", 0.0))))
        red = int(round(80 + (175 * centroid)))
        green = int(round(60 + (145 * intensity)))
        blue = int(round(90 + (165 * pitch)))
        lines.append(
            f"{float(point.get('x', 0.0)):.7f} {float(point.get('y', 0.0)):.7f} {float(point.get('z', 0.0)):.7f} {red} {green} {blue}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _preview_payload(tempo_bpm: float, trajectory: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "audio_intelligence": {"rhythm": {"tempo_bpm": round(float(tempo_bpm), 3)}, "pitch_harmony": {"key": {"label": "N/A"}}},
        "visualizer": {
            "camera": {"future_visibility_ms": 4000, "past_visibility_ms": 1600},
            "events": [],
        },
        "spatial_embedding": {"trajectory": trajectory},
    }


def run_birdsong_mode(
    *,
    audio_path: Path,
    output_dir: Path,
    preview: bool = True,
    export_ply: bool = True,
    use_umap: bool = False,
    use_basic_pitch: bool = False,
    log_fn: Callable[[str], None] | None = None,
) -> BirdsongRunResult:
    _log(log_fn, f"Birdsong: analyzing {audio_path.name}")
    features = extract_frame_features(audio_path, use_basic_pitch=use_basic_pitch)
    reduction = reduce_dimensions(features.get("feature_matrix", np.zeros((0, 0), dtype=float)), use_umap=use_umap)
    trajectory = build_trajectory(features, reduction)
    mapping = build_dynamic_mapping(features, trajectory)

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = audio_path.stem
    json_path = output_dir / f"{stem}.birdsong.json"
    csv_path = output_dir / f"{stem}.birdsong.features.csv"
    ply_path = output_dir / f"{stem}.birdsong.trajectory.ply" if export_ply else None
    preview_path = output_dir / f"{stem}.birdsong.preview.html" if preview else None
    mapping_path = output_dir / f"{stem}.birdsong.mapping.json"

    payload = {
        "mode": "birdsong",
        "audio": {
            "path": str(audio_path),
            "sample_rate": int(features.get("sample_rate", 0)),
            "duration_s": float(features.get("duration_s", 0.0)),
        },
        "analysis": {
            "frame_count": int(features.get("frame_count", 0)),
            "tempo_bpm": round(float(features.get("tempo_bpm", 0.0)), 4),
            "rhythm_stability": round(float(features.get("rhythm_stability", 0.0)), 5),
            "syncopation": round(float(features.get("syncopation", 0.0)), 5),
            "onset_count": len(features.get("onset_ms", [])),
            "beat_count": len(features.get("beat_ms", [])),
            "feature_names": list(features.get("feature_names", [])),
            "reduction": {
                "method": str(reduction.get("method", "")),
                "explained_variance_ratio": [round(float(value), 6) for value in reduction.get("explained_variance_ratio", [])],
                "scaler": reduction.get("scaler", {}),
            },
        },
        "feature_vectors": {
            "time_s": [round(float(value), 6) for value in np.asarray(features.get("frame_times_s", []), dtype=float).tolist()],
            "matrix": np.asarray(features.get("feature_matrix", []), dtype=float).tolist(),
        },
        "spatial_embedding": {
            "coords_2d": np.asarray(reduction.get("coords_2d", []), dtype=float).tolist(),
            "coords_3d": np.asarray(reduction.get("coords_3d", []), dtype=float).tolist(),
            "trajectory": trajectory,
        },
        "mapping_engine": mapping,
        "licensing": {
            "policy": "open_source_only",
            "notes": [
                "No vendor or proprietary sequence code is scraped by this mode.",
                "Feature extraction uses local audio only.",
                "Optional dependencies (Basic Pitch, UMAP) are soft-fail and not required.",
            ],
        },
    }

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    mapping_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    _write_features_csv(csv_path, features.get("frame_times_s", []), list(features.get("feature_names", [])), features.get("feature_matrix", []))
    if ply_path is not None:
        _write_trajectory_ply(ply_path, trajectory)
    if preview_path is not None:
        chronoflow_engine.write_export_html(preview_path, _preview_payload(float(features.get("tempo_bpm", 0.0)), trajectory))

    _log(
        log_fn,
        f"Birdsong: frames={int(features.get('frame_count', 0))}, trajectory={len(trajectory)}, reduction={reduction.get('method', 'n/a')}",
    )
    return BirdsongRunResult(
        audio_path=audio_path,
        json_path=json_path,
        csv_path=csv_path,
        ply_path=ply_path,
        preview_html_path=preview_path,
        mapping_json_path=mapping_path,
        frame_count=int(features.get("frame_count", 0)),
        tempo_bpm=float(features.get("tempo_bpm", 0.0)),
        reduction_method=str(reduction.get("method", "unknown")),
    )
