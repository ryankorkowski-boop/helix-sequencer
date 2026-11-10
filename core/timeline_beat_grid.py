from __future__ import annotations

from typing import Any, Iterable

from core.beat_grid import BeatGrid, generate_beat_grid, snap_timing_events


def _start_ms(obj: Any) -> int:
    if hasattr(obj, "start_ms"):
        return int(getattr(obj, "start_ms") or 0)
    return int(round(float(getattr(obj, "start_time", getattr(obj, "timestamp", 0.0))) * 1000.0))


def _end_ms(obj: Any, fallback_ms: int) -> int:
    if hasattr(obj, "end_ms"):
        return int(getattr(obj, "end_ms") or (_start_ms(obj) + fallback_ms))
    return int(round(float(getattr(obj, "end_time", 0.0)) * 1000.0)) or (_start_ms(obj) + fallback_ms)


def _apply_start(obj: Any, raw_ms: int, snapped_ms: int) -> None:
    setattr(obj, "raw_start_ms", int(raw_ms))
    setattr(obj, "snapped_start_ms", int(snapped_ms))
    if hasattr(obj, "timestamp") and not hasattr(obj, "start_time"):
        setattr(obj, "timestamp", round(snapped_ms / 1000.0, 3))
    elif hasattr(obj, "start_time"):
        setattr(obj, "start_time", round(snapped_ms / 1000.0, 3))


def _apply_end(obj: Any, raw_ms: int, snapped_ms: int) -> None:
    setattr(obj, "raw_end_ms", int(raw_ms))
    setattr(obj, "snapped_end_ms", int(snapped_ms))
    if hasattr(obj, "end_time"):
        setattr(obj, "end_time", round(snapped_ms / 1000.0, 3))


def snap_timeline_items(items: list[Any], beat_grid: BeatGrid, *, duration_ms: int, fallback_duration_ms: int = 40) -> list[Any]:
    """Snap objects with start/end timing fields and preserve raw timing metadata."""

    grid_points = generate_beat_grid(beat_grid, duration_ms)
    raw_starts = [_start_ms(item) for item in items]
    snapped_starts = snap_timing_events(
        raw_starts,
        grid_points,
        max_shift_ms=beat_grid.max_shift_ms,
        mode=beat_grid.mode,
    )
    for item, raw_start, snapped_start in zip(items, raw_starts, snapped_starts):
        delta = snapped_start - raw_start
        raw_end = _end_ms(item, fallback_duration_ms)
        snapped_end = max(snapped_start + 1, raw_end + delta)
        _apply_start(item, raw_start, snapped_start)
        _apply_end(item, raw_end, snapped_end)
    return items


def snap_lyric_timeline_to_grid(timeline: Any, beat_grid: BeatGrid, *, duration_ms: int | None = None) -> Any:
    """Snap lyric lines, words, and phoneme events to a BeatGrid.

    Existing downstream emitters keep using start_time/end_time, which are moved
    to snapped values. Raw timing remains available through raw_start_ms and
    raw_end_ms for scoring, debugging, and future ML features.
    """

    if duration_ms is None:
        duration_ms = 1
        for item in list(getattr(timeline, "words", []) or []) + list(getattr(timeline, "phoneme_events", []) or []):
            duration_ms = max(duration_ms, _end_ms(item, 40))
        for line in getattr(timeline, "lines", []) or []:
            duration_ms = max(duration_ms, _end_ms(line, 180))
        duration_ms += 1000

    snap_timeline_items(list(getattr(timeline, "lines", []) or []), beat_grid, duration_ms=duration_ms, fallback_duration_ms=180)
    snap_timeline_items(list(getattr(timeline, "words", []) or []), beat_grid, duration_ms=duration_ms, fallback_duration_ms=40)
    snap_timeline_items(list(getattr(timeline, "phoneme_events", []) or []), beat_grid, duration_ms=duration_ms, fallback_duration_ms=35)

    summary = getattr(timeline, "confidence_summary", None)
    if isinstance(summary, dict):
        summary["beat_grid_snapped"] = True
        summary["beat_grid_subdivision"] = beat_grid.subdivision
        summary["beat_grid_mode"] = beat_grid.mode

    return timeline


def snap_song_parts_to_grid(song_parts: Iterable[Any], beat_grid: BeatGrid, *, duration_ms: int) -> list[Any]:
    """Snap section boundaries such as verse, chorus, drop, bridge, and outro."""

    return snap_timeline_items(list(song_parts or []), beat_grid, duration_ms=duration_ms, fallback_duration_ms=1)


def snap_part_hits_to_grid(part_hits: Iterable[Any], beat_grid: BeatGrid, *, duration_ms: int) -> list[Any]:
    """Snap one-shot events such as phrase hits, fills, releases, and crashes."""

    hits = list(part_hits or [])
    grid_points = generate_beat_grid(beat_grid, duration_ms)
    raw_starts = [_start_ms(hit) for hit in hits]
    snapped_starts = snap_timing_events(
        raw_starts,
        grid_points,
        max_shift_ms=beat_grid.max_shift_ms,
        mode=beat_grid.mode,
    )
    for hit, raw_start, snapped_start in zip(hits, raw_starts, snapped_starts):
        _apply_start(hit, raw_start, snapped_start)
    return hits


def build_lyric_timeline_with_grid(
    lyric_events: Iterable[Any],
    vocal_peaks_ms: Iterable[int] | None = None,
    *,
    beat_grid: BeatGrid | None = None,
    snap_timing: bool = True,
    duration_ms: int | None = None,
) -> Any:
    """Build a lyric timeline and optionally return it beat-grid aligned.

    This is the opt-in activation path for Issue #41. The existing
    ``core.vocal_timeline.build_lyric_timeline`` function remains unchanged for
    legacy callers, while engine/CLI paths can switch to this wrapper to get
    deterministic raw + snapped timing metadata.
    """

    from core.vocal_timeline import build_lyric_timeline

    timeline = build_lyric_timeline(lyric_events, vocal_peaks_ms=vocal_peaks_ms)
    if snap_timing and beat_grid is not None:
        return snap_lyric_timeline_to_grid(timeline, beat_grid, duration_ms=duration_ms)
    return timeline
