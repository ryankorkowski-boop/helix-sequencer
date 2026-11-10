from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from core.beat_grid import BeatGrid
from core.beat_grid_bpm import resolve_bpm, bpm_from_recent_reports
from core.beat_grid_runtime import BeatGridRuntimeOptions, parse_beat_grid_runtime_args


PRIME_DEFAULT_SUBDIVISION = 16
PRIME_DEFAULT_MODE = "musical"
PRIME_DEFAULT_MAX_SHIFT_MS = 40
PRIME_DEFAULT_OFFSET_MS = 0


@dataclass(frozen=True)
class PrimeBeatGridDecision:
    enabled: bool
    beat_grid: BeatGrid | None
    source: str
    snap_timing: bool = True

    def as_dict(self) -> dict[str, Any]:
        grid = self.beat_grid
        return {
            "enabled": self.enabled,
            "source": self.source,
            "snap_timing": self.snap_timing,
            "bpm": grid.bpm if grid else None,
            "subdivision": grid.subdivision if grid else None,
            "offset_ms": grid.offset_ms if grid else None,
            "mode": grid.mode if grid else None,
            "max_shift_ms": grid.max_shift_ms if grid else None,
        }


def is_prime_profile(profile_id_or_version: str | None) -> bool:
    text = (profile_id_or_version or "").strip().lower()
    return text in {"", "master", "prime", "v27.3"} or "prime" in text


def decide_prime_beat_grid(
    *,
    profile_id_or_version: str | None,
    engine_args: Iterable[str] | None = None,
    analysis_payloads: Iterable[dict[str, Any]] = (),
    output_root: Path | None = None,
    since: float | None = None,
    default_enabled: bool = True,
) -> PrimeBeatGridDecision:
    """Resolve the BeatGrid Prime should use for normal generation.

    Explicit runtime flags win. Without explicit flags, Prime profiles default to
    sixteenth-note musical snapping and use detected BPM from payloads/reports
    when available. Non-Prime profiles remain unchanged unless the user passes
    explicit BeatGrid flags.
    """

    parsed = parse_beat_grid_runtime_args(engine_args or [])
    if not parsed.snap_timing:
        return PrimeBeatGridDecision(False, None, "explicit_no_snap", snap_timing=False)
    if parsed.beat_grid is not None:
        return PrimeBeatGridDecision(True, parsed.beat_grid, "explicit_runtime_flags", snap_timing=True)
    if not default_enabled or not is_prime_profile(profile_id_or_version):
        return PrimeBeatGridDecision(False, None, "not_prime_or_disabled", snap_timing=True)

    detected_bpm = None
    if output_root is not None:
        detected_bpm = bpm_from_recent_reports(output_root, since=since)
    bpm = resolve_bpm(detected_bpm, analysis_payloads, fallback_bpm=120.0)
    grid = BeatGrid(
        bpm=bpm,
        subdivision=PRIME_DEFAULT_SUBDIVISION,
        offset_ms=PRIME_DEFAULT_OFFSET_MS,
        mode=PRIME_DEFAULT_MODE,  # type: ignore[arg-type]
        max_shift_ms=PRIME_DEFAULT_MAX_SHIFT_MS,
    )
    source = "prime_default_detected_bpm" if detected_bpm is not None else "prime_default_fallback_bpm"
    return PrimeBeatGridDecision(True, grid, source, snap_timing=True)


def prime_beat_grid_args(
    *,
    profile_id_or_version: str | None,
    engine_args: Iterable[str] | None = None,
    output_root: Path | None = None,
    since: float | None = None,
) -> list[str]:
    """Return canonical args to prepend for Prime default BeatGrid activation."""

    decision = decide_prime_beat_grid(
        profile_id_or_version=profile_id_or_version,
        engine_args=engine_args,
        output_root=output_root,
        since=since,
    )
    if not decision.enabled or decision.beat_grid is None:
        return [] if decision.snap_timing else ["--no-snap"]
    grid = decision.beat_grid
    args = ["--snap-grid", str(grid.subdivision), "--snap-bpm", str(grid.bpm or 120.0)]
    if grid.offset_ms:
        args.extend(["--snap-offset-ms", str(grid.offset_ms)])
    if grid.mode != "musical":
        args.extend(["--snap-mode", grid.mode])
    if grid.max_shift_ms != 40:
        args.extend(["--snap-max-shift-ms", str(grid.max_shift_ms)])
    return args
