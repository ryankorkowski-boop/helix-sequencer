from core.beat_grid import BeatGrid
from core.timeline_beat_grid import snap_lyric_timeline_to_grid, snap_timeline_items
from core.vocal_timeline import LyricLine, LyricTimeline, LyricWord, PhonemeEvent


def test_snap_timeline_items_preserves_raw_and_moves_public_times():
    word = LyricWord("hello", 0.126, 0.400, 0.8)
    grid = BeatGrid(bpm=120, subdivision=16, max_shift_ms=40)

    snap_timeline_items([word], grid, duration_ms=1000)

    assert word.raw_start_ms == 126
    assert word.snapped_start_ms == 125
    assert word.start_ms == 125
    assert word.raw_end_ms == 400
    assert word.snapped_end_ms == 399


def test_snap_lyric_timeline_to_grid_snaps_words_lines_and_phonemes():
    phoneme = PhonemeEvent("AH", "mouth_A", "mouth_A", 0.126, 0.220, 0.9, "ah")
    word = LyricWord("ah", 0.126, 0.400, 0.9, [phoneme])
    line = LyricLine([word], 0.126, 0.400, 0.9)
    timeline = LyricTimeline([line], [word], [phoneme], {"source": "test"})
    grid = BeatGrid(bpm=120, subdivision=16, max_shift_ms=40)

    out = snap_lyric_timeline_to_grid(timeline, grid, duration_ms=1000)

    assert out is timeline
    assert line.raw_start_ms == 126
    assert line.snapped_start_ms == 125
    assert word.raw_start_ms == 126
    assert word.snapped_start_ms == 125
    assert phoneme.raw_start_ms == 126
    assert phoneme.snapped_start_ms == 125
    assert timeline.confidence_summary["beat_grid_snapped"] is True
    assert timeline.confidence_summary["beat_grid_subdivision"] == 16


def test_snap_lyric_timeline_respects_threshold_for_vocal_feel():
    phoneme = PhonemeEvent("AH", "mouth_A", "mouth_A", 0.180, 0.260, 0.9, "ah")
    word = LyricWord("ah", 0.180, 0.420, 0.9, [phoneme])
    line = LyricLine([word], 0.180, 0.420, 0.9)
    timeline = LyricTimeline([line], [word], [phoneme], {})
    grid = BeatGrid(bpm=120, subdivision=16, max_shift_ms=40)

    snap_lyric_timeline_to_grid(timeline, grid, duration_ms=1000)

    assert phoneme.raw_start_ms == 180
    assert phoneme.snapped_start_ms == 180
    assert phoneme.start_ms == 180
