"""Cymbal surface response shared by the preview and stock xLights On effects."""
from __future__ import annotations

import math
from collections.abc import Iterable

DECAY_MS = 1800
SHIMMER_SOFT_GAIN = 0.85
DEFAULT_FRAME_MS = 50


def is_cymbal(target: str) -> bool:
    return target.endswith(("_CYMBAL_LEFT", "_CYMBAL_RIGHT"))


def peak_level(velocity: float) -> float:
    # Keep the existing native velocity/brightness relationship.
    return round(68 + 32 * math.sqrt(max(0.0, min(1.0, velocity)))) / 100.0


def fade_level(age_ms: float) -> float:
    if age_ms < 0 or age_ms >= DECAY_MS:
        return 0.0
    return 1.0 - age_ms / DECAY_MS


def cymbal_level(
    hits: Iterable[tuple[int, float]],
    time_ms: float,
    *,
    frame_ms: int = DEFAULT_FRAME_MS,
    nearest_ms: float = 0,
) -> float:
    """Latest attack restarts the fade; alternate two lit gold intensities.

    xLights On shimmer alternates palette entries each sequence frame. The
    second entry is a softer gold, never black. No extra hits are generated.
    """
    if frame_ms <= 0:
        raise ValueError("Sequence frame duration must be positive")
    eligible = [(start, velocity) for start, velocity in hits
                if start <= time_ms + nearest_ms]
    if not eligible:
        return 0.0
    start, velocity = max(eligible)
    age = max(0.0, time_ms - start)
    phase = max(0, math.floor(time_ms / frame_ms) - math.floor(start / frame_ms))
    shimmer = SHIMMER_SOFT_GAIN if phase % 2 else 1.0
    return peak_level(velocity) * fade_level(age) * shimmer


def decay_intervals(hits: Iterable[tuple[int, float]]) -> list[tuple[int, int, float, float]]:
    """Nonoverlapping native fades, clipped at a retrigger without speeding up."""
    ordered = sorted(hits)
    result = []
    for i, (start, velocity) in enumerate(ordered):
        end = min(start + DECAY_MS, ordered[i + 1][0]) if i + 1 < len(ordered) else start + DECAY_MS
        if end <= start:
            continue
        peak = peak_level(velocity)
        result.append((start, end, peak, peak * fade_level(end - start)))
    return result
