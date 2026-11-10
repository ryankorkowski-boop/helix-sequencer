from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Mapping


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class AudioFeatureFrame:
    energy: float = 0.0
    onset: float = 0.0
    centroid: float = 0.0
    bands: tuple[float, float, float] = (0.0, 0.0, 0.0)
    beat_phase: float = 0.0

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "AudioFeatureFrame":
        bands_raw = raw.get("bands", (raw.get("low", 0.0), raw.get("mid", 0.0), raw.get("high", 0.0)))
        bands = tuple(float(value) for value in bands_raw)  # type: ignore[arg-type]
        if len(bands) != 3:
            raise ValueError("bands must contain low, mid, high")
        return cls(
            energy=float(raw.get("energy", 0.0)),
            onset=float(raw.get("onset", 0.0)),
            centroid=float(raw.get("centroid", 0.0)),
            bands=bands,
            beat_phase=float(raw.get("beat_phase", 0.0)),
        )


@dataclass
class FeatureState:
    smoothing_alpha: float = 0.2
    history_size: int = 128
    energy: float = 0.0
    energy_smooth: float = 0.0
    onset: float = 0.0
    centroid: float = 0.0
    low: float = 0.0
    mid: float = 0.0
    high: float = 0.0
    beat_phase: float = 0.0
    history: deque[AudioFeatureFrame] = field(default_factory=lambda: deque(maxlen=128))

    def __post_init__(self) -> None:
        self.smoothing_alpha = clamp01(self.smoothing_alpha)
        self.history = deque(self.history, maxlen=self.history_size)

    def update(self, features: AudioFeatureFrame | Mapping[str, object]) -> "FeatureState":
        frame = features if isinstance(features, AudioFeatureFrame) else AudioFeatureFrame.from_mapping(features)
        self.energy = clamp01(frame.energy)
        self.energy_smooth = round(self.energy_smooth + self.smoothing_alpha * (self.energy - self.energy_smooth), 6)
        self.onset = clamp01(frame.onset)
        self.centroid = max(0.0, float(frame.centroid))
        self.low, self.mid, self.high = tuple(clamp01(value) for value in frame.bands)
        self.beat_phase = clamp01(frame.beat_phase)
        self.history.append(frame)
        return self

    @property
    def band_balance(self) -> tuple[float, float, float]:
        total = max(1e-9, self.low + self.mid + self.high)
        return (round(self.low / total, 6), round(self.mid / total, 6), round(self.high / total, 6))
