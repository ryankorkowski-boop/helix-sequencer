from __future__ import annotations

import pytest

from core.beat_grid import BeatGrid


def test_beat_grid_nearest_beat() -> None:
    grid = BeatGrid(120.0)

    assert grid.nearest_beat(0.26) == 0.5


def test_beat_grid_next_beat() -> None:
    grid = BeatGrid(120.0)

    assert grid.next_beat(0.51) == 1.0


def test_beat_grid_subdivision() -> None:
    grid = BeatGrid(120.0)

    assert grid.subdivision(1.12, division=4) == 1.125


def test_beat_grid_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        BeatGrid(0.0)

    with pytest.raises(ValueError):
        BeatGrid(120.0).subdivision(1.0, division=0)
