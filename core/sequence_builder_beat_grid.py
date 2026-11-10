from __future__ import annotations

import argparse
from typing import Iterable

from core.beat_grid import BeatGrid
from core.beat_grid_runtime import BeatGridRuntimeOptions, beat_grid_args_from_options
from core import sequence_builder


def _beat_grid_options_from_args(args: argparse.Namespace) -> BeatGridRuntimeOptions:
    if bool(getattr(args, "no_snap", False)):
        return BeatGridRuntimeOptions(beat_grid=None, snap_timing=False, cleaned_args=())
    subdivision = getattr(args, "snap_grid", None)
    if subdivision is None:
        return BeatGridRuntimeOptions(beat_grid=None, snap_timing=True, cleaned_args=())
    grid = BeatGrid(
        bpm=float(getattr(args, "snap_bpm", None) or 120.0),
        subdivision=int(subdivision),
        offset_ms=int(getattr(args, "snap_offset_ms", 0) or 0),
        mode=str(getattr(args, "snap_mode", "musical") or "musical"),  # type: ignore[arg-type]
        max_shift_ms=int(getattr(args, "snap_max_shift_ms", 40) or 40),
    )
    return BeatGridRuntimeOptions(beat_grid=grid, snap_timing=True, cleaned_args=())


def append_beat_grid_args(engine_args: Iterable[str], options: BeatGridRuntimeOptions) -> list[str]:
    """Prepend canonical BeatGrid flags to existing effect-engine args."""

    return beat_grid_args_from_options(options) + list(engine_args or [])


def build_parser() -> argparse.ArgumentParser:
    parser = sequence_builder.build_parser()
    parser.add_argument(
        "--snap-grid",
        type=int,
        choices=(4, 8, 16, 24, 32),
        help="Snap generated timing to a musical grid subdivision, e.g. 16 for sixteenth notes.",
    )
    parser.add_argument(
        "--snap-bpm",
        type=float,
        default=120.0,
        help="BPM used with --snap-grid when no detected beat track is available. Defaults to 120.",
    )
    parser.add_argument(
        "--snap-offset-ms",
        type=int,
        default=0,
        help="Global timing offset in milliseconds for the beat grid.",
    )
    parser.add_argument(
        "--snap-mode",
        choices=("strict", "musical", "humanized"),
        default="musical",
        help="Beat-grid snapping behavior. Defaults to musical.",
    )
    parser.add_argument(
        "--snap-max-shift-ms",
        type=int,
        default=40,
        help="Maximum timing movement in musical/humanized snapping modes. Defaults to 40 ms.",
    )
    parser.add_argument(
        "--no-snap",
        action="store_true",
        help="Disable beat-grid timing snapping.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_profiles or args.list_versions:
        return sequence_builder.main(["--list-profiles"])
    profiles = args.profiles or [sequence_builder.engine_profiles.ACTIVE_PROFILE_ID]
    engine_args = list(args.engine_args)
    if engine_args[:1] == ["--"]:
        engine_args = engine_args[1:]
    engine_args = append_beat_grid_args(engine_args, _beat_grid_options_from_args(args))
    sequence_builder.build_sequence_set(profiles, engine_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
