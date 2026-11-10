from __future__ import annotations

from typing import List

from core.lyric_phoneme_mapper import map_lyric_to_phonemes
from core.band_vocal_face_export import VocalPhonemeTiming


def allocate_lyric_timings(
    *,
    performer: str,
    lyric: str,
    start: float,
    duration: float,
    intensity: float = 1.0,
) -> List[VocalPhonemeTiming]:
    """
    Deterministically allocate phoneme timings across a lyric duration.

    Strategy (v1):
    - Map graphemes → approved phonemes
    - Evenly divide total duration across resulting phoneme list
    - Preserve order
    - Clamp intensity to [0, 1]
    """

    phonemes = map_lyric_to_phonemes(lyric)

    if duration <= 0:
        raise ValueError("duration must be positive")

    slice_duration = duration / len(phonemes)
    clamped_intensity = max(0.0, min(1.0, intensity))

    timings: List[VocalPhonemeTiming] = []

    for idx, phoneme in enumerate(phonemes):
        phoneme_start = start + idx * slice_duration
        timings.append(
            VocalPhonemeTiming(
                performer=performer,
                phoneme=phoneme,
                start=round(phoneme_start, 6),
                duration=round(slice_duration, 6),
                intensity=round(clamped_intensity, 4),
            )
        )

    return timings
