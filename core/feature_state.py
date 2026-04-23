from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Mapping


@dataclass(frozen=True)
class FeatureStateFrame:
    frame_index: int
    time_s: float
    energy: float
    energy_smooth: float
    onset: float
    centroid: float
    low: float
    mid: float
    high: float
    beat_phase: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "frame_index": self.frame_index,
            "time_s": self.time_s,
            "energy": self.energy,
            "energy_smooth": self.energy_smooth,
            "onset": self.onset,
            "centroid": self.centroid,
            "low": self.low,
            "mid": self.mid,
            "high": self.high,
            "beat_phase": self.beat_phase,
        }


class FeatureState:
    """Smoothed temporal feature state with bounded history."""

    def __init__(self, history_size: int = 128, ema_alpha: float = 0.2) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be > 0")
        if not 0.0 < ema_alpha <= 1.0:
            raise ValueError("ema_alpha must be in (0, 1]")
        self.history_size = int(history_size)
        self.ema_alpha = float(ema_alpha)

        self.energy = 0.0
        self.energy_smooth = 0.0
        self.onset = 0.0
        self.centroid = 0.0
        self.low = 0.0
        self.mid = 0.0
        self.high = 0.0
        self.beat_phase = 0.0

        self.history: deque[FeatureStateFrame] = deque(maxlen=self.history_size)

    def update(
        self,
        frame_index: int,
        *,
        energy: float,
        onset: float,
        centroid: float,
        low: float,
        mid: float,
        high: float,
        beat_phase: float,
        time_s: float,
    ) -> FeatureStateFrame:
        self.energy = max(0.0, _safe_float(energy))
        self.energy_smooth = _ema(self.energy, self.energy_smooth, self.ema_alpha)
        self.onset = max(0.0, _safe_float(onset))
        self.centroid = max(0.0, _safe_float(centroid))
        self.low = max(0.0, _safe_float(low))
        self.mid = max(0.0, _safe_float(mid))
        self.high = max(0.0, _safe_float(high))
        self.beat_phase = _clamp01(_safe_float(beat_phase))

        frame = FeatureStateFrame(
            frame_index=int(frame_index),
            time_s=max(0.0, _safe_float(time_s)),
            energy=self.energy,
            energy_smooth=self.energy_smooth,
            onset=self.onset,
            centroid=self.centroid,
            low=self.low,
            mid=self.mid,
            high=self.high,
            beat_phase=self.beat_phase,
        )
        self.history.append(frame)
        return frame

    def update_from_mapping(self, frame_index: int, values: Mapping[str, object], *, time_s: float) -> FeatureStateFrame:
        return self.update(
            frame_index,
            energy=_safe_float(values.get("energy", 0.0)),
            onset=_safe_float(values.get("onset", 0.0)),
            centroid=_safe_float(values.get("centroid", 0.0)),
            low=_safe_float(values.get("low", 0.0)),
            mid=_safe_float(values.get("mid", 0.0)),
            high=_safe_float(values.get("high", 0.0)),
            beat_phase=_safe_float(values.get("beat_phase", 0.0)),
            time_s=time_s,
        )


def build_feature_state_sequence(
    features: Mapping[str, object],
    *,
    fps: float = 40.0,
    history_size: int = 128,
    ema_alpha: float = 0.2,
) -> list[FeatureStateFrame]:
    energy_series = _coerce_series(features.get("energy"))
    centroid_series = _coerce_series(features.get("centroid"))
    frame_count = max(len(energy_series), len(centroid_series))
    if frame_count == 0:
        return []

    tempo = _safe_float(features.get("tempo", 0.0))
    fps_safe = fps if fps > 0 else 40.0

    energy = [_series_value(energy_series, i) for i in range(frame_count)]
    centroid = [_series_value(centroid_series, i) for i in range(frame_count)]

    onsets = estimate_onset_series(energy)
    low, mid, high = estimate_band_series(energy, centroid)
    beat_phases = compute_beat_phase_series(frame_count, fps=fps_safe, tempo_bpm=tempo)

    state = FeatureState(history_size=history_size, ema_alpha=ema_alpha)
    out: list[FeatureStateFrame] = []
    for i in range(frame_count):
        out.append(
            state.update(
                i,
                energy=energy[i],
                onset=onsets[i],
                centroid=centroid[i],
                low=low[i],
                mid=mid[i],
                high=high[i],
                beat_phase=beat_phases[i],
                time_s=float(i) / float(fps_safe),
            )
        )
    return out


def serialize_feature_state_sequence(frames: list[FeatureStateFrame]) -> list[dict[str, float | int]]:
    return [frame.to_dict() for frame in frames]


def estimate_onset_series(energy: list[float]) -> list[float]:
    if not energy:
        return []
    deltas = [0.0]
    for i in range(1, len(energy)):
        delta = max(0.0, energy[i] - energy[i - 1])
        deltas.append(delta)
    peak = max(deltas) if deltas else 0.0
    if peak <= 0.0:
        return [0.0 for _ in deltas]
    return [value / peak for value in deltas]


def estimate_band_series(energy: list[float], centroid: list[float]) -> tuple[list[float], list[float], list[float]]:
    low: list[float] = []
    mid: list[float] = []
    high: list[float] = []

    for i in range(len(energy)):
        e = max(0.0, energy[i])
        c_norm = _clamp01((centroid[i] if i < len(centroid) else 0.0) / 8000.0)

        low_w = max(0.0, 1.0 - (1.25 * c_norm))
        high_w = max(0.0, (1.25 * c_norm) - 0.25)
        mid_w = max(0.0, 1.0 - (abs(c_norm - 0.5) * 2.0))

        total = low_w + mid_w + high_w
        if total <= 0.0:
            low.append(e)
            mid.append(0.0)
            high.append(0.0)
            continue

        low.append(e * (low_w / total))
        mid.append(e * (mid_w / total))
        high.append(e * (high_w / total))

    return (low, mid, high)


def compute_beat_phase_series(frame_count: int, *, fps: float, tempo_bpm: float) -> list[float]:
    if frame_count <= 0:
        return []
    if fps <= 0 or tempo_bpm <= 0:
        return [0.0 for _ in range(frame_count)]

    beat_seconds = 60.0 / tempo_bpm
    if beat_seconds <= 0.0:
        return [0.0 for _ in range(frame_count)]

    out: list[float] = []
    for i in range(frame_count):
        time_s = float(i) / float(fps)
        phase = (time_s / beat_seconds) % 1.0
        out.append(_clamp01(phase))
    return out


def _ema(value: float, previous: float, alpha: float) -> float:
    return (alpha * value) + ((1.0 - alpha) * previous)


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    if not math.isfinite(out):
        return default
    return out


def _coerce_series(value: object) -> list[float]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_safe_float(item) for item in value]


def _series_value(series: list[float], index: int) -> float:
    if not series:
        return 0.0
    if index < len(series):
        return series[index]
    return series[-1]


def _clamp01(value: float) -> float:
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        return 1.0
    return value
