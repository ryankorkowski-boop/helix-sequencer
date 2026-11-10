from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from typing import Iterable, Literal, Sequence

GridMode = Literal["strict", "musical", "humanized"]


@dataclass(frozen=True)
class BeatGrid:
    """Deterministic musical timing grid used to align analysis events.

    A grid can be generated from a fixed BPM or from an explicit beat track.
    The explicit beat track path keeps Helix ready for detected tempo maps and
    live recordings where a single global BPM is not accurate enough.
    """

    bpm: float | None = None
    time_signature: tuple[int, int] = (4, 4)
    subdivision: int = 16
    offset_ms: int = 0
    beat_track_ms: tuple[int, ...] | None = None
    mode: GridMode = "musical"
    max_shift_ms: int = 40


def _validate_grid(grid: BeatGrid) -> None:
    if grid.subdivision <= 0:
        raise ValueError("BeatGrid.subdivision must be positive")
    if len(grid.time_signature) != 2 or grid.time_signature[0] <= 0 or grid.time_signature[1] <= 0:
        raise ValueError("BeatGrid.time_signature must be a positive numerator/denominator pair")
    if grid.beat_track_ms:
        return
    if grid.bpm is None or grid.bpm <= 0:
        raise ValueError("BeatGrid requires a positive bpm or a non-empty beat_track_ms")


def generate_beat_grid(grid: BeatGrid, duration_ms: int) -> list[int]:
    """Generate sorted grid points in milliseconds.

    ``subdivision`` follows the xLights-friendly convention where 4 means
    quarter notes, 8 means eighth notes, 16 means sixteenth notes, and 24 means
    triplet eighths. Ties and rounding are deterministic.
    """

    _validate_grid(grid)
    if duration_ms <= 0:
        return []

    if grid.beat_track_ms:
        beats = sorted({int(round(ms)) for ms in grid.beat_track_ms if int(round(ms)) <= duration_ms})
        if len(beats) < 2:
            return beats
        points: set[int] = set()
        steps_per_beat = max(1, int(round(grid.subdivision / 4)))
        for left, right in zip(beats, beats[1:]):
            span = max(1, right - left)
            for step in range(steps_per_beat):
                points.add(int(round(left + (span * step / steps_per_beat))))
        points.add(beats[-1])
        return sorted(p for p in points if 0 <= p <= duration_ms)

    assert grid.bpm is not None
    beat_ms = 60000.0 / grid.bpm
    step_ms = beat_ms / (grid.subdivision / 4.0)
    points: list[int] = []
    idx = 0
    while True:
        point = int(round(grid.offset_ms + idx * step_ms))
        if point > duration_ms:
            break
        if point >= 0 and (not points or points[-1] != point):
            points.append(point)
        idx += 1
    return points


def snap_to_grid(value_ms: int | float, grid_points: Sequence[int]) -> int:
    """Snap to the nearest grid point using deterministic earlier-point ties."""

    if not grid_points:
        return int(round(value_ms))
    value = float(value_ms)
    idx = bisect_left(grid_points, value)
    if idx <= 0:
        return int(grid_points[0])
    if idx >= len(grid_points):
        return int(grid_points[-1])
    before = int(grid_points[idx - 1])
    after = int(grid_points[idx])
    if abs(value - before) <= abs(after - value):
        return before
    return after


def snap_ms_to_grid(value_ms: int | float, grid_points: Sequence[int], *, max_shift_ms: int | None = 40, mode: GridMode = "musical") -> int:
    """Snap one timestamp while respecting shift limits for musical modes."""

    raw = int(round(value_ms))
    if mode == "humanized":
        max_shift_ms = 25 if max_shift_ms is None else min(max_shift_ms, 25)
    snapped = snap_to_grid(raw, grid_points)
    if mode != "strict" and max_shift_ms is not None and abs(snapped - raw) > max_shift_ms:
        return raw
    return snapped


def preserve_order(snapped_values: Iterable[int], grid_points: Sequence[int], *, min_gap_ms: int = 1) -> list[int]:
    """Make snapped events monotonic without introducing randomness.

    If two events land on the same grid point or reverse order, the later event
    advances to the next available grid point when possible. If the grid is
    exhausted, it advances by ``min_gap_ms`` so ordering is still preserved.
    """

    ordered: list[int] = []
    grid = list(grid_points)
    for value in snapped_values:
        candidate = int(value)
        if ordered and candidate <= ordered[-1]:
            idx = bisect_left(grid, ordered[-1] + min_gap_ms)
            candidate = int(grid[idx]) if idx < len(grid) else ordered[-1] + min_gap_ms
        ordered.append(candidate)
    return ordered


def snap_timing_events(raw_values_ms: Iterable[int | float], grid_points: Sequence[int], *, max_shift_ms: int | None = 40, mode: GridMode = "musical", preserve_event_order: bool = True) -> list[int]:
    snapped = [snap_ms_to_grid(value, grid_points, max_shift_ms=max_shift_ms, mode=mode) for value in raw_values_ms]
    if preserve_event_order:
        return preserve_order(snapped, grid_points)
    return snapped
