from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


@dataclass(frozen=True)
class DirectorState:
    intensity: float
    section: str


class ShowDirector:
    def __init__(self, song_length_s: float | None = None) -> None:
        try:
            length = float(song_length_s) if song_length_s is not None else 0.0
        except Exception:
            length = 0.0
        self.song_length_s = length if isfinite(length) and length > 0.0 else None
        self._previous_energy = 0.0

    def update(self, time_s: float, energy: float) -> DirectorState:
        try:
            t = max(0.0, float(time_s))
        except Exception:
            t = 0.0
        e = _clamp(energy)
        trend = e - self._previous_energy
        self._previous_energy = e

        progress = (t / self.song_length_s) if self.song_length_s else None
        if progress is not None and progress >= 0.86:
            return DirectorState(intensity=_clamp(0.20 + (e * 0.45)), section="outro")

        intro_window_s = 6.0
        if self.song_length_s is not None:
            intro_window_s = max(4.0, min(10.0, self.song_length_s * 0.12))
        if t <= intro_window_s and e < 0.72:
            return DirectorState(intensity=_clamp(0.18 + (e * 0.45)), section="intro")

        if e >= 0.72:
            return DirectorState(intensity=_clamp(0.80 + (e * 0.20)), section="drop")

        if trend >= 0.08 or e >= 0.42:
            return DirectorState(intensity=_clamp(0.38 + (e * 0.50) + (max(0.0, trend) * 0.45)), section="build")

        return DirectorState(intensity=_clamp(0.28 + (e * 0.35)), section="build")
