from core.beat_grid import BeatGrid, generate_beat_grid, preserve_order, snap_ms_to_grid, snap_to_grid, snap_timing_events


def test_generate_sixteenth_grid_from_bpm():
    grid = BeatGrid(bpm=120, subdivision=16, offset_ms=0)
    assert generate_beat_grid(grid, 1000) == [0, 125, 250, 375, 500, 625, 750, 875, 1000]


def test_generate_grid_respects_offset():
    grid = BeatGrid(bpm=60, subdivision=4, offset_ms=100)
    assert generate_beat_grid(grid, 2300) == [100, 1100, 2100]


def test_generate_grid_from_beat_track():
    grid = BeatGrid(subdivision=8, beat_track_ms=(0, 500, 1000))
    assert generate_beat_grid(grid, 1000) == [0, 250, 500, 750, 1000]


def test_snap_to_grid_chooses_nearest():
    assert snap_to_grid(138, [0, 125, 250]) == 125
    assert snap_to_grid(190, [0, 125, 250]) == 250


def test_snap_to_grid_breaks_ties_earlier():
    assert snap_to_grid(187.5, [125, 250]) == 125


def test_snap_threshold_keeps_raw_when_too_far():
    assert snap_ms_to_grid(180, [0, 125, 250], max_shift_ms=40) == 180


def test_strict_mode_ignores_threshold():
    assert snap_ms_to_grid(180, [0, 125, 250], max_shift_ms=40, mode="strict") == 125


def test_preserve_order_advances_overlaps():
    assert preserve_order([125, 125, 250], [0, 125, 250, 375]) == [125, 250, 375]


def test_batch_snap_preserves_order():
    assert snap_timing_events([126, 127, 250], [0, 125, 250, 375]) == [125, 250, 375]


def test_invalid_grid_requires_bpm_or_beat_track():
    try:
        generate_beat_grid(BeatGrid(subdivision=16), 1000)
    except ValueError as exc:
        assert "positive bpm" in str(exc)
    else:
        raise AssertionError("expected ValueError")
