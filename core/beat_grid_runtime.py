from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.beat_grid import BeatGrid


@dataclass(frozen=True)
class BeatGridRuntimeOptions:
    beat_grid: BeatGrid | None = None
    snap_timing: bool = True
    cleaned_args: tuple[str, ...] = ()


def parse_beat_grid_runtime_args(engine_args: Iterable[str]) -> BeatGridRuntimeOptions:
    """Extract BeatGrid CLI flags from engine args without failing old callers.

    Supported flags:
    - --snap-grid <subdivision>
    - --snap-bpm <bpm>
    - --snap-offset-ms <ms>
    - --snap-mode strict|musical|humanized
    - --snap-max-shift-ms <ms>
    - --no-snap
    """

    args = list(engine_args or [])
    cleaned: list[str] = []
    snap_timing = True
    subdivision: int | None = None
    bpm: float | None = None
    offset_ms = 0
    mode = "musical"
    max_shift_ms = 40

    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "--no-snap":
            snap_timing = False
            idx += 1
            continue
        if arg == "--snap-grid" and idx + 1 < len(args):
            try:
                subdivision = int(args[idx + 1])
            except ValueError:
                subdivision = None
            idx += 2
            continue
        if arg == "--snap-bpm" and idx + 1 < len(args):
            try:
                bpm = float(args[idx + 1])
            except ValueError:
                bpm = None
            idx += 2
            continue
        if arg == "--snap-offset-ms" and idx + 1 < len(args):
            try:
                offset_ms = int(round(float(args[idx + 1])))
            except ValueError:
                offset_ms = 0
            idx += 2
            continue
        if arg == "--snap-mode" and idx + 1 < len(args):
            candidate = str(args[idx + 1]).strip().lower()
            if candidate in {"strict", "musical", "humanized"}:
                mode = candidate
            idx += 2
            continue
        if arg == "--snap-max-shift-ms" and idx + 1 < len(args):
            try:
                max_shift_ms = max(0, int(round(float(args[idx + 1]))))
            except ValueError:
                max_shift_ms = 40
            idx += 2
            continue
        cleaned.append(arg)
        idx += 1

    beat_grid = None
    if snap_timing and subdivision:
        beat_grid = BeatGrid(
            bpm=bpm or 120.0,
            subdivision=subdivision,
            offset_ms=offset_ms,
            mode=mode,  # type: ignore[arg-type]
            max_shift_ms=max_shift_ms,
        )
    return BeatGridRuntimeOptions(beat_grid=beat_grid, snap_timing=snap_timing, cleaned_args=tuple(cleaned))


def beat_grid_args_from_options(options: BeatGridRuntimeOptions) -> list[str]:
    if not options.snap_timing:
        return ["--no-snap"]
    grid = options.beat_grid
    if grid is None:
        return []
    args = ["--snap-grid", str(grid.subdivision), "--snap-bpm", str(grid.bpm or 120.0)]
    if grid.offset_ms:
        args.extend(["--snap-offset-ms", str(grid.offset_ms)])
    if grid.mode != "musical":
        args.extend(["--snap-mode", grid.mode])
    if grid.max_shift_ms != 40:
        args.extend(["--snap-max-shift-ms", str(grid.max_shift_ms)])
    return args
