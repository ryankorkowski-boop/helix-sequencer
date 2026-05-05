from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from core.lazy_imports import LazyModule, optional_import

librosa = LazyModule("librosa")
np = LazyModule("numpy")

_DEFAULT_MELBANKS = (
    ("low", 20.0, 350.0, 24),
    ("mid", 20.0, 2000.0, 24),
    ("high", 20.0, 15000.0, 24),
)
_DEFAULT_PIANO_ROOT = "C2"
_DEFAULT_PIANO_KEYS = 61
_DEFAULT_PIANO_BINS_PER_OCTAVE = 12


def _log(log_fn: Callable[[str], None] | None, message: str) -> None:
    if log_fn is None:
        return
    try:
        log_fn(message)
    except Exception:
        pass


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return default


def _clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _norm01(values: Any) -> Any:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size == 0:
        return np.zeros((0,), dtype=float)
    safe = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    lo = float(np.min(safe))
    hi = float(np.max(safe))
    if hi <= lo + 1e-9:
        return np.zeros_like(safe, dtype=float)
    return np.clip((safe - lo) / (hi - lo), 0.0, 1.0)


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
    src = np.linspace(0.0, 1.0, arr.size)
    dst = np.linspace(0.0, 1.0, target_len)
    return np.interp(dst, src, np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0))


def _moving_average(values: Any, kernel_size: int) -> Any:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size == 0 or kernel_size <= 1:
        return arr
    kernel = np.ones((kernel_size,), dtype=float) / float(kernel_size)
    return np.convolve(arr, kernel, mode="same")


def _mean_between(frame_times_s: Any, values: Any, start_ms: int, end_ms: int) -> float:
    ts = np.asarray(frame_times_s, dtype=float).reshape(-1)
    arr = np.asarray(values, dtype=float).reshape(-1)
    usable = min(ts.size, arr.size)
    if usable <= 0:
        return 0.0
    start_s = max(0.0, float(start_ms) / 1000.0)
    end_s = max(start_s + 1e-3, float(end_ms) / 1000.0)
    mask = (ts[:usable] >= start_s) & (ts[:usable] < end_s)
    if not np.any(mask):
        idx = int(np.searchsorted(ts[:usable], start_s))
        idx = int(_clamp(idx, 0, usable - 1))
        return float(arr[idx])
    return float(np.mean(arr[:usable][mask]))


def _availability() -> dict[str, bool]:
    return {
        "librosa": True,
        "numpy": True,
        "scipy": optional_import("scipy") is not None,
        "scikit_learn": optional_import("sklearn.decomposition") is not None,
        "essentia": optional_import("essentia.standard") is not None,
        "aubio": optional_import("aubio") is not None,
        "basic_pitch": optional_import("basic_pitch") is not None,
    }


def _load_stereo(audio_path: Path | None, audio: Any, target_len: int) -> dict[str, Any]:
    left_energy = np.zeros((target_len,), dtype=float)
    right_energy = np.zeros((target_len,), dtype=float)
    balance = np.zeros((target_len,), dtype=float)
    width = np.zeros((target_len,), dtype=float)
    y = None
    sr = _safe_int(getattr(audio, "sr", 0), 0)
    if audio_path is not None and audio_path.exists():
        try:
            y, loaded_sr = librosa.load(str(audio_path), sr=sr if sr > 0 else None, mono=False)
            sr = _safe_int(loaded_sr, sr)
        except Exception:
            y = None
    if y is None:
        raw = np.asarray(getattr(audio, "y", []), dtype=float)
        if raw.ndim == 1:
            return {
                "available": False,
                "left_energy01": left_energy,
                "right_energy01": right_energy,
                "balance": balance,
                "width01": width,
                "samples": np.vstack([raw, raw]) if raw.size else np.zeros((2, 0), dtype=float),
            }
        y = raw
    arr = np.asarray(y, dtype=float)
    if arr.ndim == 1:
        arr = np.vstack([arr, arr])
    if arr.shape[0] < 2:
        arr = np.vstack([arr[0], arr[0]])
    hop = 512
    try:
        left = np.asarray(librosa.feature.rms(y=arr[0], hop_length=hop)[0], dtype=float)
        right = np.asarray(librosa.feature.rms(y=arr[1], hop_length=hop)[0], dtype=float)
    except Exception:
        return {
            "available": False,
            "left_energy01": left_energy,
            "right_energy01": right_energy,
            "balance": balance,
            "width01": width,
            "samples": arr,
        }
    denom = np.maximum(1e-6, np.abs(left) + np.abs(right))
    left_energy = _align_curve(_norm01(left), target_len)
    right_energy = _align_curve(_norm01(right), target_len)
    balance = _align_curve((right - left) / denom, target_len)
    width = _align_curve(_norm01(np.abs(right - left) / denom), target_len)
    return {
        "available": True,
        "left_energy01": left_energy,
        "right_energy01": right_energy,
        "balance": balance,
        "width01": width,
        "samples": arr,
        "sample_rate": sr,
    }


def _melbank_payload(signal_y: Any, sr: int, target_len: int) -> dict[str, Any]:
    y = np.asarray(signal_y, dtype=float).reshape(-1)
    if y.size == 0 or sr <= 0:
        return {"banks": [], "dominance": {}, "frame_times_s": []}
    banks: list[dict[str, Any]] = []
    dominance_curves: dict[str, Any] = {}
    hop = 512
    n_fft = 4096
    for name, fmin, fmax, bins in _DEFAULT_MELBANKS:
        try:
            mel = np.asarray(
                librosa.feature.melspectrogram(
                    y=y,
                    sr=sr,
                    n_fft=n_fft,
                    hop_length=hop,
                    n_mels=bins,
                    fmin=fmin,
                    fmax=min(float(sr) * 0.5, fmax),
                    power=2.0,
                ),
                dtype=float,
            )
        except Exception:
            mel = np.zeros((bins, target_len), dtype=float)
        if mel.ndim != 2:
            mel = np.zeros((bins, target_len), dtype=float)
        if mel.shape[1] != target_len:
            aligned = np.zeros((mel.shape[0], target_len), dtype=float)
            for row in range(mel.shape[0]):
                aligned[row] = _align_curve(mel[row], target_len)
            mel = aligned
        centers = np.asarray(
            librosa.mel_frequencies(n_mels=int(mel.shape[0]), fmin=fmin, fmax=min(float(sr) * 0.5, fmax)),
            dtype=float,
        )
        mean_curve = _moving_average(_norm01(np.mean(mel, axis=0)), 5)
        dominant_bins = np.argmax(mel, axis=0) if mel.size else np.zeros((target_len,), dtype=int)
        dominant_hz = [round(float(centers[int(idx)]), 2) for idx in dominant_bins[: min(target_len, 256)]]
        banks.append(
            {
                "name": name,
                "bounds_hz": [round(float(fmin), 2), round(float(min(float(sr) * 0.5, fmax)), 2)],
                "bin_count": int(mel.shape[0]),
                "center_frequencies_hz": [round(float(value), 2) for value in centers[:64]],
                "energy_curve": [round(float(value), 4) for value in mean_curve[:640]],
                "dominant_frequencies_hz": dominant_hz,
            }
        )
        dominance_curves[name] = np.asarray(mean_curve, dtype=float)
    return {
        "banks": banks,
        "dominance": dominance_curves,
    }


def _build_piano_roll(signal_y: Any, sr: int, target_len: int) -> dict[str, Any]:
    y = np.asarray(signal_y, dtype=float).reshape(-1)
    if y.size == 0 or sr <= 0 or target_len <= 0:
        return {
            "keys": [],
            "frame_times_s": [],
            "polyphony_curve01": [],
            "dominant_key_curve": [],
            "lane_group_energy": {"low": [], "mid": [], "high": []},
        }
    try:
        fmin = float(librosa.note_to_hz(_DEFAULT_PIANO_ROOT))
        cqt = np.asarray(
            np.abs(
                librosa.cqt(
                    y=y,
                    sr=sr,
                    hop_length=512,
                    fmin=fmin,
                    n_bins=_DEFAULT_PIANO_KEYS,
                    bins_per_octave=_DEFAULT_PIANO_BINS_PER_OCTAVE,
                )
            ),
            dtype=float,
        )
    except Exception:
        cqt = np.zeros((_DEFAULT_PIANO_KEYS, target_len), dtype=float)
        fmin = 65.406
    if cqt.shape[1] != target_len:
        aligned = np.zeros((cqt.shape[0], target_len), dtype=float)
        for row in range(cqt.shape[0]):
            aligned[row] = _align_curve(cqt[row], target_len)
        cqt = aligned
    energies = np.asarray(cqt, dtype=float)
    key_labels = [
        str(librosa.midi_to_note(36 + idx))
        for idx in range(int(min(_DEFAULT_PIANO_KEYS, energies.shape[0])))
    ]
    total = np.sum(energies, axis=0) + 1e-9
    active_counts = np.sum((energies / np.maximum(1e-9, np.max(energies, axis=0, keepdims=True))) >= 0.28, axis=0)
    polyphony_curve = _norm01(active_counts)
    dominant_idx = np.argmax(energies, axis=0) if energies.size else np.zeros((target_len,), dtype=int)
    dominant_key_curve = [key_labels[int(idx)] for idx in dominant_idx[: min(target_len, 640)]]
    thirds = np.array_split(np.arange(energies.shape[0]), 3)
    lane_group_energy = {}
    group_names = ("low", "mid", "high")
    for name, indexes in zip(group_names, thirds):
        curve = np.sum(energies[indexes], axis=0) / total
        lane_group_energy[name] = [round(float(value), 4) for value in _moving_average(_norm01(curve), 5)[:640]]
    key_means = np.mean(energies, axis=1) if energies.size else np.zeros((_DEFAULT_PIANO_KEYS,), dtype=float)
    ranked = np.argsort(key_means)[::-1][:8]
    top_keys = [
        {"note": key_labels[int(idx)], "strength": round(float(_norm01(key_means)[int(idx)]), 4)}
        for idx in ranked
    ]
    return {
        "keys": key_labels,
        "root_hz": round(float(fmin), 4),
        "polyphony_curve01": [round(float(value), 4) for value in polyphony_curve[:640]],
        "dominant_key_curve": dominant_key_curve,
        "lane_group_energy": lane_group_energy,
        "top_keys": top_keys,
    }


def _build_transport(
    frame_times_s: Any,
    audio: Any,
    multiband: Any,
    stereo: dict[str, Any],
    piano_roll: dict[str, Any],
    onset_ms: list[int] | None,
) -> dict[str, Any]:
    frame_count = len(np.asarray(frame_times_s, dtype=float).reshape(-1))
    intensity = _align_curve(getattr(audio, "rms01", []), frame_count)
    brightness = _align_curve(getattr(multiband, "spectral_centroid01", []), frame_count)
    width = _align_curve(stereo.get("width01", []), frame_count)
    balance = _align_curve(stereo.get("balance", []), frame_count)
    polyphony = _align_curve(piano_roll.get("polyphony_curve01", []), frame_count)
    horizon_glow = _moving_average(np.roll(intensity, -2) if frame_count else intensity, 7)
    arrival = _norm01((0.42 * intensity) + (0.22 * brightness) + (0.20 * polyphony) + (0.16 * width))
    spiral_radius = np.clip((0.24 + (0.52 * intensity) + (0.18 * width) + (0.12 * brightness)), 0.0, 1.0)
    center_bias = np.clip(1.0 - np.abs(balance), 0.0, 1.0)
    note_hit = np.zeros((frame_count,), dtype=float)
    for mark in onset_ms or []:
        idx = int(np.searchsorted(np.asarray(frame_times_s, dtype=float), float(mark) / 1000.0))
        if 0 <= idx < frame_count:
            note_hit[idx] = 1.0
    note_hit = _moving_average(note_hit, 5)
    return {
        "arrival_curve": np.asarray(arrival, dtype=float),
        "horizon_glow_curve": np.asarray(_norm01(horizon_glow), dtype=float),
        "spiral_radius_curve": np.asarray(spiral_radius, dtype=float),
        "center_bias_curve": np.asarray(center_bias, dtype=float),
        "note_hit_curve": np.asarray(_norm01(note_hit), dtype=float),
    }


def build_helixualizer_plan(
    *,
    audio_path: Path | None,
    audio: Any,
    multiband: Any,
    note_events: list[Any] | None = None,
    beat_ms: list[int] | None = None,
    onset_ms: list[int] | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    frame_times_s = np.asarray(getattr(audio, "times_s", []), dtype=float).reshape(-1)
    frame_count = frame_times_s.size
    stereo = _load_stereo(audio_path, audio, frame_count)
    stereo_samples = np.asarray(stereo.get("samples", np.zeros((2, 0), dtype=float)), dtype=float)
    mono = (
        np.asarray(np.mean(stereo_samples[:2], axis=0), dtype=float)
        if stereo_samples.ndim == 2 and stereo_samples.shape[0] >= 2
        else np.asarray(getattr(audio, "y", []), dtype=float).reshape(-1)
    )
    sr = _safe_int(stereo.get("sample_rate", getattr(audio, "sr", 0)), _safe_int(getattr(audio, "sr", 0), 0))
    melbanks = _melbank_payload(mono, sr, frame_count)
    piano_roll = _build_piano_roll(mono, sr, frame_count)
    transport = _build_transport(frame_times_s, audio, multiband, stereo, piano_roll, onset_ms)
    low_curve = _align_curve((melbanks.get("dominance", {}) or {}).get("low", []), frame_count)
    mid_curve = _align_curve((melbanks.get("dominance", {}) or {}).get("mid", []), frame_count)
    high_curve = _align_curve((melbanks.get("dominance", {}) or {}).get("high", []), frame_count)
    lane_groups = piano_roll.get("lane_group_energy", {}) or {}
    low_keys = _align_curve(lane_groups.get("low", []), frame_count)
    mid_keys = _align_curve(lane_groups.get("mid", []), frame_count)
    high_keys = _align_curve(lane_groups.get("high", []), frame_count)
    onset_density = _safe_float(len(onset_ms or []), 0.0) / max(1.0, _safe_float(getattr(audio, "dur_s", 0.0), 1.0))
    note_density = _safe_float(len(note_events or []), 0.0) / max(1.0, _safe_float(getattr(audio, "dur_s", 0.0), 1.0))
    xlights_projection = {
        "recommended_routes": {
            "sub_bass": ["mega", "gt", "trees", "columns"],
            "bass": ["mega", "canes_combo", "trees", "line"],
            "mid": ["arches", "line", "matrices"],
            "high": ["matrices", "spinners", "stars", "snowflakes"],
            "vocals": ["matrices", "faces", "center props"],
        },
        "matrix_depth_curve": [round(float(value), 4) for value in _norm01((0.58 * high_curve) + (0.42 * transport["arrival_curve"]))[:640]],
        "supertree_spin_curve": [round(float(value), 4) for value in _norm01((0.54 * mid_curve) + (0.46 * _align_curve(stereo.get("width01", []), frame_count)))[:640]],
        "candy_cane_bar_curve": [round(float(value), 4) for value in _norm01((0.52 * low_keys) + (0.28 * mid_keys) + (0.20 * transport["note_hit_curve"]))[:640]],
        "piano_lane_groups": {
            "low": [round(float(value), 4) for value in low_keys[:640]],
            "mid": [round(float(value), 4) for value in mid_keys[:640]],
            "high": [round(float(value), 4) for value in high_keys[:640]],
        },
    }
    payload = {
        "enabled": True,
        "title": "Helixualizer",
        "analysis_tools": {
            "sources": [
                "LedFx-style perceptual melbanks",
                "Pianolizer-style piano key lanes",
                "projectM-style core-to-renderer separation",
                "stereo split analysis",
            ],
            "availability": _availability(),
        },
        "perceptual_bands": {
            "frame_count": frame_count,
            "banks": melbanks.get("banks", []),
        },
        "frame_times_s": [round(float(value), 5) for value in frame_times_s[:640]],
        "stereo_image": {
            "available": bool(stereo.get("available", False)),
            "left_energy_curve": [round(float(value), 4) for value in _align_curve(stereo.get("left_energy01", []), frame_count)[:640]],
            "right_energy_curve": [round(float(value), 4) for value in _align_curve(stereo.get("right_energy01", []), frame_count)[:640]],
            "balance_curve": [round(float(value), 4) for value in _align_curve(stereo.get("balance", []), frame_count)[:640]],
            "width_curve": [round(float(value), 4) for value in _align_curve(stereo.get("width01", []), frame_count)[:640]],
        },
        "piano_roll": piano_roll,
        "transport": {
            "arrival_curve": [round(float(value), 4) for value in transport["arrival_curve"][:640]],
            "horizon_glow_curve": [round(float(value), 4) for value in transport["horizon_glow_curve"][:640]],
            "spiral_radius_curve": [round(float(value), 4) for value in transport["spiral_radius_curve"][:640]],
            "center_bias_curve": [round(float(value), 4) for value in transport["center_bias_curve"][:640]],
            "note_hit_curve": [round(float(value), 4) for value in transport["note_hit_curve"][:640]],
        },
        "xlights_projection": xlights_projection,
        "debug": {
            "frame_count": frame_count,
            "beat_count": len(beat_ms or []),
            "onset_density": round(float(onset_density), 4),
            "note_density": round(float(note_density), 4),
        },
    }
    _log(
        log_fn,
        "Helixualizer: "
        f"melbanks={len(payload['perceptual_bands']['banks'])}, "
        f"keys={len(payload['piano_roll'].get('keys', []))}, "
        f"stereo={payload['stereo_image']['available']}",
    )
    return payload


def suggest_player_piano_neighbors(
    helixualizer_payload: dict[str, Any] | None,
    *,
    start_ms: int,
    end_ms: int,
    cue: str,
    mix: float,
) -> list[int]:
    if not helixualizer_payload:
        return []
    frame_times = np.asarray(helixualizer_payload.get("frame_times_s", []), dtype=float).reshape(-1)
    if frame_times.size == 0:
        return []
    transport = helixualizer_payload.get("transport", {}) or {}
    projection = helixualizer_payload.get("xlights_projection", {}) or {}
    arrival = _mean_between(frame_times, transport.get("arrival_curve", []), start_ms, end_ms)
    bars = _mean_between(frame_times, projection.get("candy_cane_bar_curve", []), start_ms, end_ms)
    low = _mean_between(frame_times, (projection.get("piano_lane_groups", {}) or {}).get("low", []), start_ms, end_ms)
    high = _mean_between(frame_times, (projection.get("piano_lane_groups", {}) or {}).get("high", []), start_ms, end_ms)
    spread = 0
    if cue in {"build", "vocal"}:
        spread += 1
    if mix >= 0.55 and (arrival >= 0.46 or bars >= 0.44):
        spread += 1
    if mix >= 0.90 and cue not in {"hat"} and max(low, high) >= 0.52:
        spread += 1
    spread = int(_clamp(spread, 0, 2))
    if spread <= 0:
        return []
    offsets = list(range(-spread, 0)) + list(range(1, spread + 1))
    return offsets
