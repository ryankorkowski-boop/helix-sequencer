from __future__ import annotations

from typing import List

from core.band_vocal_face_export import VocalPhonemeTiming


def align_to_beat_grid(
    timings: List[VocalPhonemeTiming],
    beat_interval: float,
    grid_division: int = 1,
) -> List[VocalPhonemeTiming]:
    """
    Deterministically snap phoneme start times to nearest beat grid subdivision.

    Rules:
    - beat_interval must be > 0
    - grid_division must be >= 1
    - grid_size = beat_interval / grid_division
    - new_start = round(start / grid_size) * grid_size
    - Output start rounded to 6 decimal places
    - Duration unchanged (v1)
    - Ordering preserved
    - No randomness
    """

    if beat_interval <= 0:
        raise ValueError("beat_interval must be > 0")

    if grid_division < 1:
        raise ValueError("grid_division must be >= 1")

    grid_size = beat_interval / grid_division

    aligned: List[VocalPhonemeTiming] = []

    for t in timings:
        snapped = round(t.start / grid_size) * grid_size

        aligned.append(
            VocalPhonemeTiming(
                performer=t.performer,
                phoneme=t.phoneme,
                start=round(snapped, 6),
                duration=t.duration,
                intensity=t.intensity,
            )
        )

    return aligned
