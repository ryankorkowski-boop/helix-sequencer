"""Deterministic whole-layout flash restraint, independent of generation/DSP."""
from collections.abc import Sequence
import math


def allows_global_flash(
    time_ms: float,
    flash_guard: float,
    max_flashes_per_sec: float = 2.0,
    accepted_times_ms: Sequence[float] = (),
) -> bool:
    """Use one minimum spacing for all colors, including out-of-order requests.

    Guard 1 disables flashes; lower guards retain the caller's musical/probability
    gates. Nonpositive caps disable flashes. This function never mutates history;
    callers record only successful placements at their final (snapped) start time.
    """
    if not all(math.isfinite(value) for value in (time_ms, flash_guard, max_flashes_per_sec)):
        return False
    if flash_guard >= 1.0 or max_flashes_per_sec <= 0.0:
        return False
    cooldown_ms = 1000.0 / max_flashes_per_sec
    return all(abs(time_ms - previous) >= cooldown_ms for previous in accepted_times_ms)
