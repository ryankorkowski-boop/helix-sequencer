from __future__ import annotations

from core.lyric_timing_allocator import allocate_lyric_timings


def test_allocate_even_distribution() -> None:
    timings = allocate_lyric_timings(
        performer="singer",
        lyric="aa",
        start=0.0,
        duration=2.0,
    )

    assert len(timings) == 2
    assert timings[0].start == 0.0
    assert timings[1].start == 1.0
    assert timings[0].duration == 1.0
    assert timings[1].duration == 1.0


def test_allocate_is_deterministic() -> None:
    args = dict(
        performer="singer",
        lyric="Hello",
        start=1.0,
        duration=5.0,
    )

    first = allocate_lyric_timings(**args)
    second = allocate_lyric_timings(**args)

    assert first == second


def test_intensity_is_clamped() -> None:
    timings = allocate_lyric_timings(
        performer="singer",
        lyric="a",
        start=0.0,
        duration=1.0,
        intensity=5.0,
    )

    assert timings[0].intensity == 1.0


def test_duration_must_be_positive() -> None:
    try:
        allocate_lyric_timings(
            performer="singer",
            lyric="a",
            start=0.0,
            duration=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for non-positive duration")
