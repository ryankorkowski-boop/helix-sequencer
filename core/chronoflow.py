from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable

from core import helixualizer as helixualizer_engine
from core.lazy_imports import LazyModule, optional_import

librosa = LazyModule("librosa")
np = LazyModule("numpy")
signal = LazyModule("scipy.signal")

_NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


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


def _part_label(part: Any) -> str:
    return str(getattr(part, "label", "UNKNOWN")).upper()


def _part_start_ms(part: Any) -> int:
    return _safe_int(getattr(part, "start_ms", 0), 0)


def _part_end_ms(part: Any) -> int:
    start = _part_start_ms(part)
    return max(start + 1, _safe_int(getattr(part, "end_ms", start + 1), start + 1))


def _norm01(values: Any) -> Any:
    arr = np.asarray(values, dtype=float)
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


def _moving_average(values: Any, kernel_size: int) -> Any:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size == 0 or kernel_size <= 1:
        return arr
    kernel = np.ones((kernel_size,), dtype=float) / float(kernel_size)
    return np.convolve(arr, kernel, mode="same")


def _smooth_curve(values: Any, preferred_window: int = 9, order: int = 2) -> Any:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size < 5:
        return arr
    window = min(preferred_window, arr.size if arr.size % 2 == 1 else arr.size - 1)
    if window < 5:
        return arr
    try:
        return signal.savgol_filter(arr, window_length=window, polyorder=min(order, window - 2), mode="interp")
    except Exception:
        return _moving_average(arr, max(3, min(window, 5)))


def _hex_color(rgb: tuple[float, float, float]) -> str:
    r = int(_clamp(round(rgb[0]), 0, 255))
    g = int(_clamp(round(rgb[1]), 0, 255))
    b = int(_clamp(round(rgb[2]), 0, 255))
    return f"#{r:02X}{g:02X}{b:02X}"


def _mix_hex(base_rgb: tuple[int, int, int], accent_rgb: tuple[int, int, int], amount: float) -> str:
    blend = _clamp(amount, 0.0, 1.0)
    out = (
        ((1.0 - blend) * base_rgb[0]) + (blend * accent_rgb[0]),
        ((1.0 - blend) * base_rgb[1]) + (blend * accent_rgb[1]),
        ((1.0 - blend) * base_rgb[2]) + (blend * accent_rgb[2]),
    )
    return _hex_color(out)


def _note_name(pc: int) -> str:
    return _NOTE_NAMES[int(pc) % 12]


def _sample_curve_at_time(frame_times_s: Any, curve: Any, target_ms: int) -> float:
    ts = np.asarray(frame_times_s, dtype=float).reshape(-1)
    vals = np.asarray(curve, dtype=float).reshape(-1)
    usable = min(ts.size, vals.size)
    if usable == 0:
        return 0.0
    idx = int(np.searchsorted(ts[:usable], float(target_ms) / 1000.0))
    idx = int(_clamp(idx, 0, usable - 1))
    return float(vals[idx])


def _mean_between(frame_times_s: Any, curve: Any, start_ms: int, end_ms: int) -> float:
    ts = np.asarray(frame_times_s, dtype=float).reshape(-1)
    vals = np.asarray(curve, dtype=float).reshape(-1)
    usable = min(ts.size, vals.size)
    if usable == 0:
        return 0.0
    start_s = max(0.0, float(start_ms) / 1000.0)
    end_s = max(start_s + 1e-3, float(end_ms) / 1000.0)
    mask = (ts[:usable] >= start_s) & (ts[:usable] < end_s)
    if not np.any(mask):
        return _sample_curve_at_time(ts[:usable], vals[:usable], start_ms)
    return float(np.mean(vals[:usable][mask]))


def _groove_metrics(beat_ms: list[int], onset_ms: list[int]) -> dict[str, float]:
    if len(beat_ms) < 4:
        return {"swing_ratio": 1.0, "groove_tightness": 0.0}
    deviations: list[float] = []
    interval_stability: list[float] = []
    for idx in range(len(beat_ms) - 1):
        st = beat_ms[idx]
        en = beat_ms[idx + 1]
        interval = max(1, en - st)
        interval_stability.append(interval)
        midpoint = st + (interval / 2.0)
        candidates = [mark for mark in onset_ms if st < mark < en]
        if not candidates:
            continue
        best = min(candidates, key=lambda mark: abs(mark - midpoint))
        deviations.append((best - midpoint) / float(interval))
    if not deviations:
        return {"swing_ratio": 1.0, "groove_tightness": 0.0}
    swing = 1.0 + float(np.mean(np.clip(np.asarray(deviations, dtype=float), -0.45, 0.45)))
    intervals = np.asarray(interval_stability, dtype=float)
    tightness = 1.0 - _clamp(float(np.std(intervals) / max(1.0, np.mean(intervals))), 0.0, 1.0)
    return {
        "swing_ratio": round(_clamp(swing, 0.55, 1.45), 4),
        "groove_tightness": round(_clamp(tightness, 0.0, 1.0), 4),
    }


def _load_stereo_field(audio_path: Path | None, frame_times_s: Any, sr: int) -> dict[str, Any]:
    target_len = len(np.asarray(frame_times_s, dtype=float).reshape(-1))
    balance = np.zeros((target_len,), dtype=float)
    width = np.zeros((target_len,), dtype=float)
    left_energy = np.zeros((target_len,), dtype=float)
    right_energy = np.zeros((target_len,), dtype=float)
    if audio_path is None or not audio_path.exists():
        return {
            "available": False,
            "left_energy01": left_energy,
            "right_energy01": right_energy,
            "balance": balance,
            "width01": width,
            "summary": {"left_mean": 0.0, "right_mean": 0.0, "width_mean": 0.0},
        }
    try:
        y, loaded_sr = librosa.load(str(audio_path), sr=sr if sr > 0 else None, mono=False)
    except Exception:
        return {
            "available": False,
            "left_energy01": left_energy,
            "right_energy01": right_energy,
            "balance": balance,
            "width01": width,
            "summary": {"left_mean": 0.0, "right_mean": 0.0, "width_mean": 0.0},
        }
    arr = np.asarray(y, dtype=float)
    if arr.ndim == 1:
        arr = np.vstack([arr, arr])
    if arr.shape[0] < 2:
        arr = np.vstack([arr[0], arr[0]])
    hop = 512
    left = librosa.feature.rms(y=np.asarray(arr[0], dtype=float), hop_length=hop)[0]
    right = librosa.feature.rms(y=np.asarray(arr[1], dtype=float), hop_length=hop)[0]
    denom = np.maximum(1e-6, np.abs(left) + np.abs(right))
    balance_curve = (right - left) / denom
    width_curve = np.abs(right - left) / denom
    left_energy = _align_curve(_norm01(left), target_len)
    right_energy = _align_curve(_norm01(right), target_len)
    balance = _align_curve(balance_curve, target_len)
    width = _align_curve(_norm01(width_curve), target_len)
    return {
        "available": True,
        "left_energy01": left_energy,
        "right_energy01": right_energy,
        "balance": balance,
        "width01": width,
        "summary": {
            "left_mean": round(float(np.mean(left_energy)), 4) if left_energy.size else 0.0,
            "right_mean": round(float(np.mean(right_energy)), 4) if right_energy.size else 0.0,
            "width_mean": round(float(np.mean(width)), 4) if width.size else 0.0,
        },
    }


def _fill_pitch_midi(pitch_hz: Any, target_len: int) -> tuple[Any, Any]:
    if target_len <= 0:
        return np.zeros((0,), dtype=float), np.zeros((0,), dtype=float)
    hz = np.asarray(pitch_hz, dtype=float).reshape(-1)
    if hz.size == 0:
        return np.full((target_len,), 60.0, dtype=float), np.zeros((target_len,), dtype=float)
    hz = _align_curve(hz, target_len)
    valid = hz > 0.0
    if not np.any(valid):
        midi = np.full((target_len,), 60.0, dtype=float)
        return midi, np.zeros((target_len,), dtype=float)
    indexes = np.arange(target_len, dtype=float)
    midi = np.full((target_len,), np.nan, dtype=float)
    try:
        midi[valid] = librosa.hz_to_midi(hz[valid])
    except Exception:
        midi[valid] = 60.0
    midi[~valid] = np.interp(indexes[~valid], indexes[valid], midi[valid])
    midi = np.nan_to_num(midi, nan=60.0, posinf=60.0, neginf=60.0)
    return midi, _norm01(midi)


def _compute_chroma(audio: Any, target_len: int) -> tuple[Any, Any]:
    if target_len <= 0:
        return np.zeros((12, 0), dtype=float), np.zeros((12,), dtype=float)
    try:
        chroma = np.asarray(librosa.feature.chroma_cqt(y=np.asarray(audio.y, dtype=float), sr=int(audio.sr), hop_length=512), dtype=float)
    except Exception:
        chroma = np.zeros((12, target_len), dtype=float)
    if chroma.ndim != 2 or chroma.shape[0] != 12:
        chroma = np.zeros((12, target_len), dtype=float)
    if chroma.shape[1] != target_len:
        aligned = np.zeros((12, target_len), dtype=float)
        for row in range(12):
            aligned[row] = _align_curve(chroma[row], target_len)
        chroma = aligned
    return chroma, np.asarray(np.mean(chroma, axis=1), dtype=float)


def _estimate_key(chroma_mean: Any) -> dict[str, Any]:
    vector = np.asarray(chroma_mean, dtype=float).reshape(-1)
    if vector.size != 12:
        vector = np.zeros((12,), dtype=float)
    major_template = np.asarray([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], dtype=float)
    minor_template = np.asarray([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17], dtype=float)
    vector = vector / max(1e-6, float(np.linalg.norm(vector)))
    best_label = "C major"
    best_score = -999.0
    for tonic in range(12):
        maj = np.roll(major_template, tonic)
        minr = np.roll(minor_template, tonic)
        maj_score = float(np.dot(vector, maj / np.linalg.norm(maj)))
        min_score = float(np.dot(vector, minr / np.linalg.norm(minr)))
        if maj_score > best_score:
            best_score = maj_score
            best_label = f"{_note_name(tonic)} major"
        if min_score > best_score:
            best_score = min_score
            best_label = f"{_note_name(tonic)} minor"
    return {"label": best_label, "confidence": round(_clamp((best_score + 1.0) * 0.5, 0.0, 1.0), 4)}


def _estimate_chords(chroma: Any, frame_times_s: Any, beat_ms: list[int], duration_ms: int) -> list[dict[str, Any]]:
    chroma = np.asarray(chroma, dtype=float)
    ts = np.asarray(frame_times_s, dtype=float).reshape(-1)
    if chroma.ndim != 2 or chroma.shape[0] != 12 or ts.size == 0:
        return []
    windows = beat_ms[:] if beat_ms else list(range(0, max(1, duration_ms), 800))
    if not windows or windows[0] != 0:
        windows = [0] + windows
    if windows[-1] < duration_ms:
        windows.append(duration_ms)
    major = np.zeros((12, 12), dtype=float)
    minor = np.zeros((12, 12), dtype=float)
    for root in range(12):
        major[root, root] = 1.0
        major[root, (root + 4) % 12] = 0.85
        major[root, (root + 7) % 12] = 0.7
        minor[root, root] = 1.0
        minor[root, (root + 3) % 12] = 0.85
        minor[root, (root + 7) % 12] = 0.7
    segments: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for idx in range(len(windows) - 1):
        start_ms = int(windows[idx])
        end_ms = max(start_ms + 1, int(windows[idx + 1]))
        start_s = start_ms / 1000.0
        end_s = end_ms / 1000.0
        mask = (ts >= start_s) & (ts < end_s)
        if not np.any(mask):
            continue
        vector = np.asarray(np.mean(chroma[:, mask], axis=1), dtype=float)
        if float(np.max(vector)) <= 1e-6:
            continue
        vector = vector / max(1e-6, float(np.linalg.norm(vector)))
        best_name = "N"
        best_score = -999.0
        for root in range(12):
            major_score = float(np.dot(vector, major[root] / max(1e-6, float(np.linalg.norm(major[root])))))
            minor_score = float(np.dot(vector, minor[root] / max(1e-6, float(np.linalg.norm(minor[root])))))
            if major_score > best_score:
                best_score = major_score
                best_name = f"{_note_name(root)}"
            if minor_score > best_score:
                best_score = minor_score
                best_name = f"{_note_name(root)}m"
        if current and current["label"] == best_name and start_ms <= current["end_ms"] + 20:
            current["end_ms"] = end_ms
            current["confidence"] = max(float(current["confidence"]), round(_clamp((best_score + 1.0) * 0.5, 0.0, 1.0), 4))
            continue
        current = {
            "label": best_name,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "confidence": round(_clamp((best_score + 1.0) * 0.5, 0.0, 1.0), 4),
        }
        segments.append(current)
    return segments[:256]


def _estimate_bassline(bass_peaks: list[int], pitch_midi: Any, frame_times_s: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not bass_peaks:
        return events
    for t_ms in bass_peaks[:240]:
        midi = _sample_curve_at_time(frame_times_s, pitch_midi, t_ms)
        events.append(
            {
                "time_ms": int(t_ms),
                "midi": round(midi, 2),
                "note": _note_name(int(round(midi)) % 12),
            }
        )
    return events


def _essentia_summary(audio_path: Path | None) -> dict[str, Any]:
    module = optional_import("essentia.standard")
    if module is None or audio_path is None or not audio_path.exists():
        return {"available": False, "descriptors": {}}
    loader = getattr(module, "MonoLoader", None)
    danceability = getattr(module, "Danceability", None)
    centroid = getattr(module, "Centroid", None)
    if loader is None or danceability is None or centroid is None:
        return {"available": True, "descriptors": {}}
    try:
        samples = loader(filename=str(audio_path))()
        spectrum = np.abs(np.fft.rfft(np.asarray(samples, dtype=float)))
        danceability_value = float(danceability()(samples))
        centroid_value = float(centroid(range=float(max(1.0, len(spectrum))), array=spectrum))
        return {
            "available": True,
            "descriptors": {
                "danceability": round(danceability_value, 4),
                "spectral_centroid": round(centroid_value, 4),
            },
        }
    except Exception:
        return {"available": True, "descriptors": {}}


def _pca_coordinates(feature_matrix: Any) -> tuple[Any, str]:
    rows = np.asarray(feature_matrix, dtype=float)
    if rows.ndim != 2 or rows.shape[0] == 0:
        return np.zeros((0, 3), dtype=float), "empty"
    safe = np.nan_to_num(rows, nan=0.0, posinf=0.0, neginf=0.0)
    mean = np.mean(safe, axis=0, keepdims=True)
    std = np.std(safe, axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    normalized = (safe - mean) / std
    scaler_module = optional_import("sklearn.preprocessing")
    pca_module = optional_import("sklearn.decomposition")
    if scaler_module is not None and pca_module is not None:
        try:
            scaler = scaler_module.StandardScaler()
            pca = pca_module.PCA(n_components=min(3, normalized.shape[0], normalized.shape[1]))
            coords = pca.fit_transform(scaler.fit_transform(safe))
            if coords.shape[1] < 3:
                coords = np.pad(coords, ((0, 0), (0, 3 - coords.shape[1])), mode="constant")
            return np.asarray(coords[:, :3], dtype=float), "sklearn_pca"
        except Exception:
            pass
    try:
        _u, _s, vh = np.linalg.svd(normalized, full_matrices=False)
        coords = normalized @ vh[: min(3, vh.shape[0])].T
        if coords.shape[1] < 3:
            coords = np.pad(coords, ((0, 0), (0, 3 - coords.shape[1])), mode="constant")
        return np.asarray(coords[:, :3], dtype=float), "svd_pca"
    except Exception:
        return np.zeros((normalized.shape[0], 3), dtype=float), "fallback_zero"


def _dominant_band_for_time(multiband: Any, target_ms: int) -> str:
    checks = (
        ("sub_bass", getattr(multiband, "sub_bass_marks", []), 90),
        ("bass", getattr(multiband, "bass_marks", []), 90),
        ("mid", getattr(multiband, "mid_marks", []), 90),
        ("high", getattr(multiband, "high_marks", []), 90),
    )
    for label, marks, window in checks:
        if any(abs(int(mark) - int(target_ms)) <= window for mark in marks):
            return label
    centroid_curve = getattr(multiband, "spectral_centroid01", None)
    frame_times = getattr(multiband, "frame_times_s", None)
    centroid = _sample_curve_at_time(frame_times, centroid_curve, target_ms)
    if centroid >= 0.72:
        return "high"
    if centroid <= 0.24:
        return "bass"
    return "mid"


def _event_kind(target_ms: int, *, kicks: list[int], snares: list[int], hats: list[int], bass_peaks: list[int], vocal_peaks: list[int], build_lifts: list[int], releases: list[int], default: str) -> str:
    if any(abs(target_ms - mark) <= 80 for mark in releases):
        return "drop"
    if any(abs(target_ms - mark) <= 70 for mark in build_lifts):
        return "build"
    if any(abs(target_ms - mark) <= 40 for mark in kicks):
        return "kick"
    if any(abs(target_ms - mark) <= 55 for mark in snares):
        return "snare"
    if any(abs(target_ms - mark) <= 35 for mark in hats):
        return "hat"
    if any(abs(target_ms - mark) <= 70 for mark in bass_peaks):
        return "bass"
    if any(abs(target_ms - mark) <= 85 for mark in vocal_peaks):
        return "vocal"
    return default


def _lyric_for_time(lyric_events: list[Any], target_ms: int) -> str:
    for event in lyric_events:
        st = _safe_int(getattr(event, "start_ms", 0), 0)
        en = max(st + 1, _safe_int(getattr(event, "end_ms", st + 1), st + 1))
        if st - 120 <= target_ms <= en + 120:
            return str(getattr(event, "text", "") or "").strip()
    return ""


def _event_color(*, kind: str, band: str, intensity: float, brightness: float, mood: str) -> str:
    kind_key = (kind or "melody").lower()
    band_key = (band or "mid").lower()
    mood_key = (mood or "balanced").lower()
    base = {
        "sub_bass": (90, 125, 255),
        "bass": (70, 210, 255),
        "mid": (255, 120, 190),
        "high": (255, 255, 255),
    }.get(band_key, (215, 170, 255))
    accent = {
        "kick": (255, 150, 90),
        "snare": (255, 220, 140),
        "hat": (235, 245, 255),
        "bass": (100, 215, 255),
        "vocal": (255, 120, 210),
        "melody": (255, 180, 150),
        "build": (255, 245, 160),
        "drop": (255, 255, 255),
    }.get(kind_key, (255, 200, 180))
    mood_push = 0.14 if mood_key in {"uplifting", "balanced"} else 0.06 if mood_key in {"calm"} else 0.1
    brightness_push = _clamp((0.35 * intensity) + (0.45 * brightness) + mood_push, 0.15, 1.0)
    return _mix_hex(base, accent, brightness_push)


def _collect_layout_mapping(parsed_layout: Any) -> dict[str, Any]:
    if parsed_layout is None:
        return {}
    roots: list[dict[str, Any]] = []
    for model in getattr(parsed_layout, "models", {}).values():
        if getattr(model, "is_submodel", False):
            continue
        try:
            center = getattr(model, "center")()
        except Exception:
            center = (0.0, 0.0, 0.0)
        roots.append(
            {
                "name": str(getattr(model, "name", "")),
                "type": str(getattr(model, "type", "")).lower(),
                "x": _safe_float(center[0], 0.0),
                "y": _safe_float(center[1], 0.0),
            }
        )
    if not roots:
        return {}
    xs = sorted(item["x"] for item in roots)
    left_cut = xs[max(0, int(len(xs) * 0.33) - 1)]
    right_cut = xs[min(len(xs) - 1, max(0, int(len(xs) * 0.66) - 1))]

    def zone_for_x(x: float) -> str:
        if x <= left_cut:
            return "left"
        if x >= right_cut:
            return "right"
        return "center"

    by_zone = {"left": [], "center": [], "right": []}
    families = {
        "rhythm": [],
        "bass": [],
        "melody": [],
        "vocals": [],
        "pads": [],
    }
    for item in roots:
        zone = zone_for_x(float(item["x"]))
        by_zone[zone].append(item["name"])
        model_type = item["type"]
        if model_type in {"spinner", "pinwheel", "star", "snowflake"}:
            families["rhythm"].append(item["name"])
        elif model_type in {"tree", "column"}:
            families["bass"].append(item["name"])
        elif model_type in {"arch", "line"}:
            families["melody"].append(item["name"])
        elif model_type in {"matrix", "talking_heads", "face", "faces"}:
            families["vocals"].append(item["name"])
        else:
            families["pads"].append(item["name"])
    if not families["rhythm"]:
        families["rhythm"] = families["melody"][:6]
    if not families["bass"]:
        families["bass"] = families["vocals"][:4] or families["pads"][:4]
    if not families["melody"]:
        families["melody"] = families["pads"][:6]
    if not families["vocals"]:
        families["vocals"] = families["melody"][:4] or families["pads"][:4]
    if not families["pads"]:
        families["pads"] = families["melody"][:6] or families["bass"][:4]
    return {
        "stereo_zones": by_zone,
        "cue_routes": {
            "drums": families["rhythm"][:8],
            "bass": families["bass"][:8],
            "melody": families["melody"][:8],
            "vocals": families["vocals"][:8],
            "pads": families["pads"][:8],
        },
        "focus_strategy": {
            "verse": "reduce to melody, vocal, and pad anchors",
            "chorus": "open the full stage and mirror stereo across left and right zones",
            "breakdown": "hold focal props and leave background props breathing",
            "drop": "expand from bass foundations into full-width accents",
        },
    }


def _section_scene_at_time(parts: list[Any], target_ms: int) -> str:
    for part in parts:
        st = _part_start_ms(part)
        en = _part_end_ms(part)
        if st <= target_ms < en:
            return _part_label(part)
    return _part_label(parts[-1]) if parts else "UNKNOWN"


def _trajectory_points(frame_times_s: Any, spatial_x: Any, spatial_y: Any, pitch_norm: Any, brightness: Any, intensity: Any, balance: Any) -> list[dict[str, Any]]:
    ts = np.asarray(frame_times_s, dtype=float).reshape(-1)
    if ts.size == 0:
        return []
    total_ms = max(1.0, float(ts[-1]) * 1000.0)
    sample_count = min(720, ts.size)
    indexes = np.linspace(0, ts.size - 1, sample_count).astype(int)
    points: list[dict[str, Any]] = []
    turns = max(5.5, total_ms / 9500.0)
    for idx in indexes:
        time_ms = int(round(float(ts[idx]) * 1000.0))
        progress = _clamp(float(time_ms) / total_ms, 0.0, 1.0)
        radius = 0.34 + (0.44 * float(intensity[idx])) + (0.28 * float(brightness[idx]))
        theta = (progress * turns * math.tau) + (float(spatial_x[idx]) * 1.6)
        x = (math.cos(theta) * radius) + (float(balance[idx]) * 0.32)
        y = (math.sin(theta) * radius * 0.84) + ((float(pitch_norm[idx]) - 0.5) * 0.82) + (float(spatial_y[idx]) * 0.16)
        points.append(
            {
                "time_ms": time_ms,
                "x": round(x, 5),
                "y": round(y, 5),
                "z": round(progress * total_ms, 5),
                "brightness": round(float(brightness[idx]), 4),
                "intensity": round(float(intensity[idx]), 4),
            }
        )
    return points


def _event_payload(
    *,
    time_ms: int,
    kind: str,
    band: str,
    intensity: float,
    brightness: float,
    pitch_norm: float,
    stereo_balance: float,
    embedding_x: float,
    embedding_y: float,
    duration_ms: int,
    lyric_text: str,
    mood: str,
    section: str,
) -> dict[str, Any]:
    progress = _clamp(float(time_ms) / max(1.0, float(duration_ms)), 0.0, 1.0)
    spiral_turns = max(6.5, float(duration_ms) / 8700.0)
    radius = 0.26 + (0.46 * intensity) + (0.22 * brightness)
    theta = (progress * spiral_turns * math.tau) + (embedding_x * 1.7) + (pitch_norm * 0.9)
    x = (math.cos(theta) * radius) + (stereo_balance * 0.40) + (embedding_x * 0.22)
    y = (math.sin(theta) * radius * 0.88) + ((pitch_norm - 0.5) * 0.95) + (embedding_y * 0.24)
    lifetime_ms = int(round(220.0 + (420.0 * intensity) + (150.0 * brightness)))
    forecast_ms = int(round(160.0 + (380.0 * brightness) + (120.0 * intensity)))
    return {
        "time_ms": int(time_ms),
        "kind": str(kind),
        "band": str(band),
        "section": str(section),
        "position": {
            "x": round(x, 5),
            "y": round(y, 5),
            "z": round(progress * duration_ms, 5),
        },
        "metadata": {
            "amplitude": round(float(intensity), 4),
            "brightness": round(float(brightness), 4),
            "spectral_centroid": round(float(brightness), 4),
            "emission_time_ms": int(time_ms),
            "lifetime_ms": lifetime_ms,
            "forecast_horizon_ms": forecast_ms,
            "lyric_text": lyric_text,
        },
        "rendering": {
            "radius": round(radius, 4),
            "color": _event_color(kind=kind, band=band, intensity=intensity, brightness=brightness, mood=mood),
            "future_alpha": round(_clamp(0.18 + (0.42 * brightness), 0.12, 0.72), 4),
            "present_alpha": round(_clamp(0.65 + (0.32 * intensity), 0.5, 1.0), 4),
            "past_alpha": round(_clamp(0.14 + (0.30 * intensity), 0.08, 0.52), 4),
        },
    }


def _build_chronoflow_events(
    *,
    parts: list[Any],
    note_events: list[Any],
    lyric_events: list[Any],
    frame_times_s: Any,
    pitch_norm_curve: Any,
    brightness_curve: Any,
    intensity_curve: Any,
    balance_curve: Any,
    embedding_x: Any,
    embedding_y: Any,
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    build_lifts: list[int],
    releases: list[int],
    multiband: Any,
    mood: str,
    duration_ms: int,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    resolved_indexes: dict[tuple[int, str], int] = {}
    lead_marks = sorted({int(getattr(event, "start_ms", 0)) for event in note_events if _safe_int(getattr(event, "start_ms", 0), -1) >= 0})
    hats_sparse = [mark for idx, mark in enumerate(sorted(set(hats))) if idx % 2 == 0]
    seeds = (
        [(mark, "kick") for mark in sorted(set(kicks))]
        + [(mark, "snare") for mark in sorted(set(snares))]
        + [(mark, "hat") for mark in hats_sparse]
        + [(mark, "bass") for mark in sorted(set(bass_peaks))]
        + [(mark, "vocal") for mark in sorted(set(vocal_peaks))]
        + [(mark, "build") for mark in sorted(set(build_lifts))]
        + [(mark, "drop") for mark in sorted(set(releases))]
        + [(mark, "melody") for mark in lead_marks]
    )
    seen: set[tuple[int, str]] = set()
    for target_ms, default_kind in seeds:
        key = (int(target_ms), str(default_kind))
        if key in seen or target_ms < 0 or target_ms > duration_ms:
            continue
        seen.add(key)
        section = _section_scene_at_time(parts, target_ms)
        brightness = _sample_curve_at_time(frame_times_s, brightness_curve, target_ms)
        intensity = _sample_curve_at_time(frame_times_s, intensity_curve, target_ms)
        pitch_norm = _sample_curve_at_time(frame_times_s, pitch_norm_curve, target_ms)
        stereo_balance = _sample_curve_at_time(frame_times_s, balance_curve, target_ms)
        spatial_x = _sample_curve_at_time(frame_times_s, embedding_x, target_ms)
        spatial_y = _sample_curve_at_time(frame_times_s, embedding_y, target_ms)
        kind = _event_kind(
            int(target_ms),
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            build_lifts=build_lifts,
            releases=releases,
            default=default_kind,
        )
        band = _dominant_band_for_time(multiband, int(target_ms))
        lyric_text = _lyric_for_time(lyric_events, int(target_ms)) if kind in {"vocal", "melody"} or default_kind in {"vocal", "melody"} else ""
        payload = _event_payload(
            time_ms=int(target_ms),
            kind=kind,
            band=band,
            intensity=intensity,
            brightness=brightness,
            pitch_norm=pitch_norm,
            stereo_balance=stereo_balance,
            embedding_x=spatial_x,
            embedding_y=spatial_y,
            duration_ms=duration_ms,
            lyric_text=lyric_text,
            mood=mood,
            section=section,
        )
        resolved_key = (int(target_ms), str(kind))
        if resolved_key in resolved_indexes:
            existing = events[resolved_indexes[resolved_key]]
            existing_metadata = existing.get("metadata", {}) or {}
            if lyric_text and not str(existing_metadata.get("lyric_text", "")).strip():
                existing_metadata["lyric_text"] = lyric_text
                existing["metadata"] = existing_metadata
            continue
        resolved_indexes[resolved_key] = len(events)
        events.append(payload)
    events.sort(key=lambda item: (int(item["time_ms"]), str(item["kind"])))
    return events[:3200]


def build_timing_track(payload: dict[str, Any], *, limit: int = 1200) -> list[tuple[str, int, int]]:
    if not payload:
        return []
    events = list((payload.get("visualizer", {}) or {}).get("events", []) or [])
    track: list[tuple[str, int, int]] = []
    for event in events[: max(1, limit)]:
        time_ms = _safe_int(event.get("time_ms"), 0)
        metadata = event.get("metadata", {}) or {}
        lifetime = max(60, min(320, _safe_int(metadata.get("lifetime_ms"), 120)))
        label = str(event.get("kind", "event"))
        lyric_text = str(metadata.get("lyric_text", "") or "").strip()
        if lyric_text:
            label = f"{label}:{lyric_text[:18]}"
        elif event.get("band"):
            label = f"{label}:{event.get('band')}"
        track.append((label[:40], time_ms, time_ms + lifetime))
    return track


def build_chronoflow_plan(
    *,
    audio_path: Path | None,
    parsed_layout: Any,
    audio: Any,
    multiband: Any,
    parts: list[Any],
    note_events: list[Any],
    lyric_events: list[Any],
    beat_ms: list[int],
    onset_ms: list[int],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    build_lifts: list[int],
    releases: list[int],
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    frame_times_s = np.asarray(getattr(audio, "times_s", []), dtype=float).reshape(-1)
    frame_count = frame_times_s.size
    duration_ms = max(1, _safe_int(_safe_float(getattr(audio, "dur_s", 0.0), 0.0) * 1000.0, 1))
    helixualizer_payload = helixualizer_engine.build_helixualizer_plan(
        audio_path=audio_path,
        audio=audio,
        multiband=multiband,
        note_events=note_events,
        beat_ms=beat_ms,
        onset_ms=onset_ms,
        log_fn=log_fn,
    )
    intensity_curve = _align_curve(getattr(audio, "rms01", []), frame_count)
    bass_curve = _align_curve(getattr(audio, "bass01", []), frame_count)
    vocal_curve = _align_curve(getattr(audio, "vocal01", []), frame_count)
    brightness_curve = _align_curve(getattr(multiband, "spectral_centroid01", []), frame_count)
    bandwidth_curve = _align_curve(getattr(multiband, "spectral_bandwidth01", []), frame_count)
    contrast_curve = _align_curve(getattr(multiband, "spectral_contrast01", []), frame_count)
    flatness_curve = _align_curve(getattr(multiband, "spectral_flatness01", []), frame_count)
    flux_curve = _align_curve(getattr(multiband, "spectral_flux01", []), frame_count)
    mfcc_motion_curve = _align_curve(getattr(multiband, "mfcc_motion01", []), frame_count)
    chroma_stability_curve = _align_curve(getattr(multiband, "chroma_stability01", []), frame_count)
    tonnetz_curve = _align_curve(getattr(multiband, "tonnetz_motion01", []), frame_count)
    pitch_midi_curve, pitch_norm_curve = _fill_pitch_midi(getattr(audio, "pitch_hz", []), frame_count)
    stereo = _load_stereo_field(audio_path, frame_times_s, _safe_int(getattr(audio, "sr", 0), 0))
    chroma, chroma_mean = _compute_chroma(audio, frame_count)
    key = _estimate_key(chroma_mean)
    chords = _estimate_chords(chroma, frame_times_s, beat_ms, duration_ms)
    bassline = _estimate_bassline(bass_peaks, pitch_midi_curve, frame_times_s)
    groove = _groove_metrics(beat_ms, onset_ms)
    essentia_summary = _essentia_summary(audio_path)

    tonal_spread = _norm01((1.0 - chroma_stability_curve) + tonnetz_curve)
    spectral_skewness_proxy = _norm01(brightness_curve - bandwidth_curve)
    modulation_index = _norm01(np.abs(np.gradient(pitch_norm_curve)) + mfcc_motion_curve) if frame_count else np.zeros((0,), dtype=float)
    feature_matrix = np.column_stack(
        [
            _align_curve(stereo.get("balance", []), frame_count),
            _align_curve(stereo.get("width01", []), frame_count),
            tonal_spread,
            pitch_norm_curve,
            brightness_curve,
            bandwidth_curve,
            contrast_curve,
            flux_curve,
            mfcc_motion_curve,
            bass_curve,
            vocal_curve,
            intensity_curve,
        ]
    ) if frame_count else np.zeros((0, 12), dtype=float)
    latent, backend = _pca_coordinates(feature_matrix)
    latent_x = _norm01(_align_curve(latent[:, 0] if latent.size else [], frame_count))
    latent_y = _norm01(_align_curve(latent[:, 1] if latent.size else [], frame_count))

    spatial_x = np.clip((0.58 * (_align_curve(stereo.get("balance", []), frame_count) * 0.5 + 0.5)) + (0.42 * latent_x), 0.0, 1.0)
    spatial_y = np.clip((0.55 * ((0.62 * pitch_norm_curve) + (0.38 * brightness_curve))) + (0.45 * latent_y), 0.0, 1.0)
    spatial_z = np.linspace(0.0, 1.0, frame_count) if frame_count else np.zeros((0,), dtype=float)
    smoothed_x = _smooth_curve(spatial_x, preferred_window=11)
    smoothed_y = _smooth_curve(spatial_y, preferred_window=11)

    descriptor_summary = dict(getattr(multiband, "descriptor_summary", {}) or {})
    arousal = _clamp(
        (0.46 * float(np.mean(intensity_curve)) if intensity_curve.size else 0.0)
        + (0.24 * float(np.mean(flux_curve)) if flux_curve.size else 0.0)
        + (0.18 * float(np.mean(brightness_curve)) if brightness_curve.size else 0.0)
        + (0.12 * float(np.mean(bass_curve)) if bass_curve.size else 0.0),
        0.0,
        1.0,
    )
    valence = _clamp(
        (0.42 * float(descriptor_summary.get("chroma_stability_mean", 0.0)))
        + (0.28 * (1.0 - float(descriptor_summary.get("tonnetz_motion_mean", 0.0))))
        + (0.18 * float(np.mean(stereo.get("width01", []))) if np.asarray(stereo.get("width01", [])).size else 0.0)
        + (0.12 * float(np.mean(brightness_curve)) if brightness_curve.size else 0.0),
        0.0,
        1.0,
    )
    mood = str(getattr(multiband, "mood_hint", "balanced") or "balanced")
    aggression = _clamp((0.45 * arousal) + (0.30 * float(np.mean(contrast_curve)) if contrast_curve.size else 0.0) + (0.25 * float(np.mean(flux_curve)) if flux_curve.size else 0.0), 0.0, 1.0)
    smoothness = _clamp(1.0 - aggression + (0.16 * float(np.mean(chroma_stability_curve)) if chroma_stability_curve.size else 0.0), 0.0, 1.0)

    events = _build_chronoflow_events(
        parts=parts,
        note_events=note_events,
        lyric_events=lyric_events,
        frame_times_s=frame_times_s,
        pitch_norm_curve=pitch_norm_curve,
        brightness_curve=brightness_curve,
        intensity_curve=intensity_curve,
        balance_curve=stereo.get("balance", []),
        embedding_x=smoothed_x,
        embedding_y=smoothed_y,
        kicks=kicks,
        snares=snares,
        hats=hats,
        bass_peaks=bass_peaks,
        vocal_peaks=vocal_peaks,
        build_lifts=build_lifts,
        releases=releases,
        multiband=multiband,
        mood=mood,
        duration_ms=duration_ms,
    )
    trajectory = _trajectory_points(
        frame_times_s,
        smoothed_x,
        smoothed_y,
        pitch_norm_curve,
        brightness_curve,
        intensity_curve,
        stereo.get("balance", []),
    )
    layout_mapping = _collect_layout_mapping(parsed_layout)

    sections = []
    for part in parts:
        start_ms = _part_start_ms(part)
        end_ms = _part_end_ms(part)
        sections.append(
            {
                "label": _part_label(part),
                "start_ms": start_ms,
                "end_ms": end_ms,
                "intensity_mean": round(_mean_between(frame_times_s, intensity_curve, start_ms, end_ms), 4),
                "brightness_mean": round(_mean_between(frame_times_s, brightness_curve, start_ms, end_ms), 4),
                "stereo_width_mean": round(_mean_between(frame_times_s, stereo.get("width01", []), start_ms, end_ms), 4),
            }
        )

    payload = {
        "enabled": True,
        "analysis_tools": {
            "touchdesigner_inspired_inputs": [
                "amplitude_envelope",
                "onset_grid",
                "fundamental_pitch",
                "chroma",
                "spectral_centroid",
                "spectral_spread",
                "spectral_skewness",
                "spectral_bandwidth",
                "spectral_contrast",
                "spectral_flux",
                "mfcc_motion",
                "temporal_metrics",
                "modulation_indices",
                "oscillator_envelope_mapping",
                "stereo_balance_width",
                "pca_latent_embedding",
                "lyrics_word_hits",
            ],
            "helixualizer_inputs": list((helixualizer_payload.get("analysis_tools", {}) or {}).get("sources", []) or []),
            "engine_stack": {
                "librosa": True,
                "numpy": True,
                "scipy": True,
                "scikit_learn": backend == "sklearn_pca",
                "essentia": bool(essentia_summary.get("available", False)),
            },
            "embedding_backend": backend,
            "essentia": essentia_summary,
        },
        "audio_intelligence": {
            "rhythm": {
                "tempo_bpm": round(_safe_float(getattr(multiband, "tempo_bpm", 0.0), 0.0), 3),
                "beat_grid_ms": [int(mark) for mark in beat_ms[:2000]],
                "onset_count": len(onset_ms),
                "transient_counts": {"kicks": len(kicks), "snares": len(snares), "hats": len(hats)},
                "groove": groove,
            },
            "pitch_harmony": {
                "key": key,
                "chords": chords,
                "melody_contour_midi": [round(float(value), 3) for value in _smooth_curve(pitch_midi_curve, preferred_window=13)[:640]],
                "bassline": bassline,
            },
            "spectral": {
                "mfcc_motion_mean": round(float(np.mean(mfcc_motion_curve)) if mfcc_motion_curve.size else 0.0, 4),
                "centroid_mean": round(float(np.mean(brightness_curve)) if brightness_curve.size else 0.0, 4),
                "spread_mean": round(float(np.mean(tonal_spread)) if tonal_spread.size else 0.0, 4),
                "skewness_proxy_mean": round(float(np.mean(spectral_skewness_proxy)) if spectral_skewness_proxy.size else 0.0, 4),
                "bandwidth_mean": round(float(np.mean(bandwidth_curve)) if bandwidth_curve.size else 0.0, 4),
                "contrast_mean": round(float(np.mean(contrast_curve)) if contrast_curve.size else 0.0, 4),
                "modulation_index_mean": round(float(np.mean(modulation_index)) if modulation_index.size else 0.0, 4),
                "brightness_curve": [round(float(v), 4) for v in brightness_curve[:640]],
            },
            "structure": {
                "sections": sections,
                "build_lifts_ms": [int(mark) for mark in build_lifts[:400]],
                "drops_ms": [int(mark) for mark in releases[:400]],
            },
            "energy_emotion": {
                "intensity_curve": [round(float(v), 4) for v in intensity_curve[:640]],
                "density": round(float(len(onset_ms)) / max(1.0, float(getattr(audio, "dur_s", 1.0))), 4),
                "aggression": round(aggression, 4),
                "smoothness": round(smoothness, 4),
                "tension_release": {
                    "arousal": round(arousal, 4),
                    "valence": round(valence, 4),
                    "mood_hint": mood,
                },
            },
            "stereo_field": {
                "available": bool(stereo.get("available", False)),
                "left_energy_mean": stereo.get("summary", {}).get("left_mean", 0.0),
                "right_energy_mean": stereo.get("summary", {}).get("right_mean", 0.0),
                "width_mean": stereo.get("summary", {}).get("width_mean", 0.0),
                "balance_curve": [round(float(v), 4) for v in _align_curve(stereo.get("balance", []), frame_count)[:640]],
            },
        },
        "spatial_embedding": {
            "axis_mapping": {
                "x": "stereo_balance + tonal_spread",
                "y": "pitch_height + brightness",
                "z": "time_progression",
            },
            "trajectory": trajectory,
            "feature_names": [
                "stereo_balance",
                "stereo_width",
                "tonal_spread",
                "pitch_norm",
                "brightness",
                "bandwidth",
                "contrast",
                "flux",
                "mfcc_motion",
                "bass_energy",
                "vocal_energy",
                "intensity",
            ],
            "continuous_path_points": len(trajectory),
            "xlights_projection": (helixualizer_payload.get("xlights_projection", {}) or {}),
        },
        "helixualizer": helixualizer_payload,
        "visualizer": {
            "title": "Chronoflow Helixualizer",
            "camera": {
                "mode": "forward_time_flight",
                "current_focus": "present_centerline",
                "future_visibility_ms": 4000,
                "past_visibility_ms": 1800,
            },
            "time_layers": {
                "future": "ghosted pulses and translucent foreshadow geometry",
                "present": "bright impact flashes and lyric hits",
                "past": "smoke-like decay ribbons and fading trail particles",
            },
            "mapping": {
                "kick": "forward shockwaves and tunnel compression",
                "snare": "lateral flashes",
                "hat": "spark particles",
                "bass": "low-frequency tunnel floor waves",
                "melody": "spiral arcs and ribbons",
                "vocal": "centerline lyric structures",
                "build": "camera acceleration and tunnel tightening",
                "drop": "burst expansion and white-hot impact",
            },
            "events": events,
            "lyric_hits": [event for event in events if str((event.get("metadata", {}) or {}).get("lyric_text", "")).strip()][:400],
        },
        "layout_mapping": layout_mapping,
        "debug": {
            "section_count": len(parts),
            "event_count": len(events),
            "lyric_count": len(lyric_events),
            "trajectory_count": len(trajectory),
        },
    }
    _log(log_fn, f"Chronoflow: events={len(events)}, trajectory={len(trajectory)}, embedding={backend}")
    return payload


def write_export_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_export_html(path: Path, payload: dict[str, Any]) -> None:
    packed = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Helixualizer Viewer</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg0: #03040a;
      --bg1: #121832;
      --ink: #f4f6ff;
      --muted: #93a0cc;
      --accent: #ffe78a;
    }}
    html, body {{
      margin: 0;
      height: 100%;
      overflow: hidden;
      background:
        radial-gradient(circle at top, rgba(86, 130, 255, 0.16), transparent 34%),
        radial-gradient(circle at bottom, rgba(255, 120, 196, 0.12), transparent 30%),
        linear-gradient(180deg, var(--bg1), var(--bg0));
      color: var(--ink);
      font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    }}
    #hud {{
      position: fixed;
      inset: 0 auto auto 0;
      padding: 18px 20px;
      width: min(420px, calc(100vw - 36px));
      pointer-events: none;
      background: linear-gradient(180deg, rgba(7, 10, 24, 0.82), rgba(7, 10, 24, 0.18));
    }}
    #hud h1 {{
      margin: 0 0 6px;
      font-size: 20px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    #hud p {{
      margin: 6px 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.4;
    }}
    #impact {{
      position: fixed;
      left: 50%;
      bottom: 12%;
      transform: translateX(-50%);
      padding: 10px 18px;
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 999px;
      background: rgba(8, 10, 20, 0.62);
      color: #ffffff;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-size: 15px;
      opacity: 0;
      transition: opacity 140ms ease;
      pointer-events: none;
    }}
    #canvas {{
      width: 100vw;
      height: 100vh;
      display: block;
    }}
  </style>
</head>
<body>
  <canvas id="canvas"></canvas>
  <div id="hud">
    <h1>Helixualizer</h1>
    <p id="meta"></p>
    <p id="status"></p>
  </div>
  <div id="impact"></div>
  <script>
    const payload = {packed};
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    const meta = document.getElementById("meta");
    const status = document.getElementById("status");
    const impact = document.getElementById("impact");
    const events = (payload.visualizer && payload.visualizer.events) || [];
    const pathPoints = (payload.spatial_embedding && payload.spatial_embedding.trajectory) || [];
    const durationMs = Math.max(1, Math.max(...events.map((e) => e.time_ms), ...pathPoints.map((p) => p.time_ms), 1000));
    const aheadMs = (payload.visualizer && payload.visualizer.camera && payload.visualizer.camera.future_visibility_ms) || 4000;
    const behindMs = (payload.visualizer && payload.visualizer.camera && payload.visualizer.camera.past_visibility_ms) || 1800;
    meta.textContent = `${{payload.audio_intelligence.rhythm.tempo_bpm || 0}} BPM | ${{events.length}} events | ${{payload.audio_intelligence.pitch_harmony.key.label || "Unknown key"}}`;

    function resize() {{
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      canvas.width = Math.floor(window.innerWidth * dpr);
      canvas.height = Math.floor(window.innerHeight * dpr);
      canvas.style.width = `${{window.innerWidth}}px`;
      canvas.style.height = `${{window.innerHeight}}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }}

    function project(point, playheadMs) {{
      const width = window.innerWidth;
      const height = window.innerHeight;
      const relMs = point.position.z - playheadMs;
      const depth = relMs / Math.max(1, aheadMs);
      const z = 1.0 + depth * 1.45;
      const scale = 1.0 / Math.max(0.16, z);
      const px = width * 0.5 + (point.position.x * width * 0.42 * scale);
      const py = height * 0.5 - (point.position.y * height * 0.34 * scale);
      return {{ x: px, y: py, scale, relMs }};
    }}

    function drawPath(playheadMs) {{
      ctx.lineWidth = 1;
      ctx.beginPath();
      let started = false;
      for (const point of pathPoints) {{
        const rel = point.z - playheadMs;
        if (rel < -behindMs || rel > aheadMs) continue;
        const scale = 1.0 / Math.max(0.16, 1.0 + (rel / Math.max(1, aheadMs)) * 1.45);
        const x = window.innerWidth * 0.5 + (point.x * window.innerWidth * 0.40 * scale);
        const y = window.innerHeight * 0.5 - (point.y * window.innerHeight * 0.30 * scale);
        if (!started) {{
          ctx.moveTo(x, y);
          started = true;
        }} else {{
          ctx.lineTo(x, y);
        }}
      }}
      ctx.strokeStyle = "rgba(146, 178, 255, 0.18)";
      ctx.stroke();
    }}

    function drawEvent(point, playheadMs) {{
      const projection = project(point, playheadMs);
      if (projection.relMs < -behindMs || projection.relMs > aheadMs) return;
      const meta = point.metadata || {{}};
      const render = point.rendering || {{}};
      let alpha = render.future_alpha || 0.18;
      if (Math.abs(projection.relMs) <= 120) {{
        alpha = render.present_alpha || 1.0;
      }} else if (projection.relMs < 0) {{
        alpha = render.past_alpha || 0.22;
      }}
      const radius = Math.max(1.5, (render.radius || 0.4) * 18 * projection.scale);
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = render.color || "#ffffff";
      ctx.beginPath();
      ctx.arc(projection.x, projection.y, radius, 0, Math.PI * 2);
      ctx.fill();
      if (point.kind === "build") {{
        ctx.strokeStyle = "rgba(255, 245, 180, 0.18)";
        ctx.lineWidth = Math.max(1, radius * 0.28);
        ctx.beginPath();
        ctx.arc(projection.x, projection.y, radius * 2.8, 0, Math.PI * 2);
        ctx.stroke();
      }}
      if (point.kind === "drop" || point.kind === "kick") {{
        ctx.strokeStyle = "rgba(255, 255, 255, 0.22)";
        ctx.lineWidth = Math.max(1, radius * 0.22);
        ctx.beginPath();
        ctx.arc(projection.x, projection.y, radius * 1.8, 0, Math.PI * 2);
        ctx.stroke();
      }}
      ctx.restore();
      if (meta.lyric_text && Math.abs(projection.relMs) <= 120) {{
        impact.textContent = meta.lyric_text;
        impact.style.opacity = "1";
      }}
    }}

    let lastImpactClear = 0;
    const startedAt = performance.now();
    function frame(now) {{
      const elapsed = now - startedAt;
      const playheadMs = elapsed % durationMs;
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

      const gradient = ctx.createLinearGradient(0, 0, 0, window.innerHeight);
      gradient.addColorStop(0, "rgba(9, 12, 28, 0.36)");
      gradient.addColorStop(1, "rgba(2, 3, 8, 0.84)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, window.innerWidth, window.innerHeight);

      drawPath(playheadMs);
      for (const point of events) {{
        drawEvent(point, playheadMs);
      }}
      if (now - lastImpactClear > 160) {{
        impact.style.opacity = "0";
        lastImpactClear = now;
      }}
      status.textContent = `Time ${{Math.floor(playheadMs / 1000)}}s / ${{Math.floor(durationMs / 1000)}}s | Future horizon ${{Math.round(aheadMs / 1000)}}s`;
      requestAnimationFrame(frame);
    }}

    window.addEventListener("resize", resize);
    resize();
    requestAnimationFrame(frame);
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
