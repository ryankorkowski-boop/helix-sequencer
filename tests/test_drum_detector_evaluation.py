from __future__ import annotations

from tools.evaluate_drum_detector_oracle import _match_times


def test_match_times_uses_nearest_unused_detection() -> None:
    matches, missed, false_positive = _match_times(
        [100, 200, 300],
        [95, 205, 260, 305],
        tolerance_ms=20,
    )

    assert matches == [(100, 95), (200, 205), (300, 305)]
    assert missed == []
    assert false_positive == [260]


def test_match_times_reports_misses_and_false_positives() -> None:
    matches, missed, false_positive = _match_times(
        [100, 300],
        [105, 500],
        tolerance_ms=20,
    )

    assert matches == [(100, 105)]
    assert missed == [300]
    assert false_positive == [500]
