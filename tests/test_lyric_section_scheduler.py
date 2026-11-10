from __future__ import annotations

from core.lyric_section_scheduler import schedule_lyric_section


def test_even_line_distribution() -> None:
    timings = schedule_lyric_section(
        performer="singer",
        lines=["a", "a"],
        section_start=0.0,
        section_duration=4.0,
    )

    # Two lines, each gets 2 seconds
    # Each line has 1 phoneme
    assert len(timings) == 2
    assert timings[0].start == 0.0
    assert timings[1].start == 2.0
    assert timings[0].duration == 2.0
    assert timings[1].duration == 2.0


def test_section_is_deterministic() -> None:
    args = dict(
        performer="singer",
        lines=["Hello", "World"],
        section_start=1.0,
        section_duration=6.0,
    )

    first = schedule_lyric_section(**args)
    second = schedule_lyric_section(**args)

    assert first == second


def test_negative_duration_raises() -> None:
    try:
        schedule_lyric_section(
            performer="singer",
            lines=["a"],
            section_start=0.0,
            section_duration=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for non-positive section_duration")
