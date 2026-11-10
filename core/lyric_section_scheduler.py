from __future__ import annotations

from typing import List

from core.lyric_timing_allocator import allocate_lyric_timings
from core.band_vocal_face_export import VocalPhonemeTiming


def schedule_lyric_section(
    *,
    performer: str,
    lines: List[str],
    section_start: float,
    section_duration: float,
    intensity: float = 1.0,
) -> List[VocalPhonemeTiming]:
    """
    Deterministically schedule multiple lyric lines inside a section.

    Strategy (v1):
    - Evenly divide section_duration across lines
    - For each line:
        - Call allocate_lyric_timings
    - Preserve ordering
    - Ensure full section coverage (within float rounding)
    """

    if section_duration <= 0:
        raise ValueError("section_duration must be positive")

    if not lines:
        return []

    line_count = len(lines)
    line_duration = section_duration / line_count

    all_timings: List[VocalPhonemeTiming] = []

    for idx, line in enumerate(lines):
        line_start = section_start + idx * line_duration

        timings = allocate_lyric_timings(
            performer=performer,
            lyric=line,
            start=round(line_start, 6),
            duration=round(line_duration, 6),
            intensity=intensity,
        )

        all_timings.extend(timings)

    return all_timings
