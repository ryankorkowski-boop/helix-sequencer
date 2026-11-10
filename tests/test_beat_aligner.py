from __future__ import annotations

from core.beat_aligner import align_to_beat_grid
from core.band_vocal_face_export import VocalPhonemeTiming


def _make_timing(start: float) -> VocalPhonemeTiming:
    return VocalPhonemeTiming(
        performer="singer",
        phoneme="AH",
        start=start,
        duration=0.5,
        intensity=1.0,
    )


def test_snaps_to_nearest_beat():
    timings = [_make_timing(0.26)]
    aligned = align_to_beat_grid(timings, beat_interval=0.5)
    assert aligned[0].start == 0.5


def test_subdivision_support():
    timings = [_make_timing(0.26)]
    aligned = align_to_beat_grid(timings, beat_interval=1.0, grid_division=4)
    # grid_size = 0.25 → nearest to 0.26 is 0.25
    assert aligned[0].start == 0.25


def test_preserves_duration_and_phoneme():
    timings = [_make_timing(0.3)]
    aligned = align_to_beat_grid(timings, beat_interval=1.0)
    assert aligned[0].duration == 0.5
    assert aligned[0].phoneme == "AH"


def test_invalid_inputs_raise():
    timings = [_make_timing(0.3)]

    try:
        align_to_beat_grid(timings, beat_interval=0.0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid beat_interval")

    try:
        align_to_beat_grid(timings, beat_interval=1.0, grid_division=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid grid_division")


def test_deterministic_output():
    timings = [_make_timing(0.37)]
    first = align_to_beat_grid(timings, 0.5)
    second = align_to_beat_grid(timings, 0.5)
    assert first == second
