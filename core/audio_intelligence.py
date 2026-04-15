from __future__ import annotations
from bisect import bisect_left
import json
import numpy as np

# Existing code...


def _compress_ms():
    # Existing implementation
    pass


def nearest_mark_distance_ms(target_ms: int, marks: list[int]) -> int | None:
    if not marks:
        return None
    idx = bisect_left(marks, int(target_ms))
    best: int | None = None
    for probe in (idx - 1, idx):
        if 0 <= probe < len(marks):
            dist = abs(int(marks[probe]) - int(target_ms))
            if best is None or dist < best:
                best = dist
    return best


def proximity_confidence(target_ms: int, marks: list[int], window_ms: int, floor: float = 0.0) -> float:
    distance = nearest_mark_distance_ms(target_ms, marks)
    if distance is None:
        return float(np.clip(floor, 0.0, 1.0))
    if window_ms <= 0:
        return 1.0 if distance == 0 else float(np.clip(floor, 0.0, 1.0))
    score = 1.0 - min(1.0, float(distance) / float(window_ms))
    return float(np.clip(max(floor, score), 0.0, 1.0))

# Rest of the file...