from __future__ import annotations

from typing import List

from core.band_vocal_face_export import VocalPhonemeTiming


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def scale_section_intensity(
    timings: List[VocalPhonemeTiming],
    section_energy: float,
) -> List[VocalPhonemeTiming]:
    """
    Deterministically scale intensity of a section.

    Rules:
    - section_energy <= 0 → intensity becomes 0
    - section_energy >= 1 → unchanged
    - otherwise → intensity *= section_energy
    - Output clamped to [0.0, 1.0]
    - Timing + phoneme preserved
    - No randomness
    """

    # Normalize energy bounds deterministically
    if section_energy <= 0.0:
        factor = 0.0
    elif section_energy >= 1.0:
        factor = 1.0
    else:
        factor = section_energy

    scaled: List[VocalPhonemeTiming] = []

    for t in timings:
        if factor == 1.0:
            new_intensity = t.intensity
        else:
            new_intensity = t.intensity * factor

        scaled.append(
            VocalPhonemeTiming(
                performer=t.performer,
                phoneme=t.phoneme,
                start=t.start,
                duration=t.duration,
                intensity=round(_clamp(new_intensity), 4),
            )
        )

    return scaled
