from __future__ import annotations

import math


class BeatGrid:
    def __init__(self, bpm: float) -> None:
        try:
            value = float(bpm)
        except Exception as exc:
            raise ValueError("bpm must be > 0") from exc
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError("bpm must be > 0")
        self.bpm = value
        self.beat_s = 60.0 / value

    def nearest_beat(self, time_s: float) -> float:
        return self._snap(time_s, self.beat_s)

    def next_beat(self, time_s: float) -> float:
        t = max(0.0, float(time_s))
        return math.ceil((t + 1e-9) / self.beat_s) * self.beat_s

    def subdivision(self, time_s: float, division: int = 2) -> float:
        if division < 1:
            raise ValueError("division must be >= 1")
        return self._snap(time_s, self.beat_s / float(division))

    def next_subdivision(self, time_s: float, division: int = 2) -> float:
        if division < 1:
            raise ValueError("division must be >= 1")
        t = max(0.0, float(time_s))
        step = self.beat_s / float(division)
        return math.ceil((t + 1e-9) / step) * step

    @staticmethod
    def _snap(time_s: float, step_s: float) -> float:
        t = max(0.0, float(time_s))
        return round(t / step_s) * step_s
