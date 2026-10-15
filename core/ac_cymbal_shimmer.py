"""Audio-tail-following cymbal shimmer envelopes for dimmable AC outputs.

Input is a measured cymbal-tail amplitude series, not a guessed fixed decay.
Values are 0..100 percent brightness for export by a separate LOR adapter.
"""
from __future__ import annotations

import math


def cymbal_shimmer(
    tail_amplitudes: list[float] | tuple[float, ...],
    *,
    fps: float = 40.0,
    shimmer_hz: float = 8.0,
    shimmer_depth: float = 0.18,
    noise_floor: float = 0.025,
) -> tuple[int, ...]:
    """Spike at impact, then shimmer and fade while measured sound remains.

    tail_amplitudes[0] is the attack. Subsequent values should be measured
    cymbal-specific energy (e.g. isolated cymbal stem or accepted decay band).
    Do not feed broadband song loudness: it would hold the cymbal on for vocals.
    """
    if fps <= 0 or not math.isfinite(fps):
        raise ValueError("fps must be finite and positive")
    if not 0 <= shimmer_depth <= 1 or not 0 <= noise_floor < 1:
        raise ValueError("invalid shimmer parameters")
    if not tail_amplitudes:
        return ()
    if any(not math.isfinite(float(x)) or float(x) < 0 for x in tail_amplitudes):
        raise ValueError("amplitudes must be finite and nonnegative")
    peak = max(float(x) for x in tail_amplitudes)
    if peak <= 0:
        return (0,) * len(tail_amplitudes)
    result = [100]
    for i, amplitude in enumerate(tail_amplitudes[1:], start=1):
        normalized = min(1.0, float(amplitude) / peak)
        if normalized <= noise_floor:
            result.append(0)
            continue
        # Modulate only a shrinking envelope, so shimmer cannot outlive sound.
        pulse = 1 - shimmer_depth * (0.5 + 0.5 * math.sin(2 * math.pi * shimmer_hz * i / fps))
        brightness = 100 * normalized ** 0.65 * pulse
        result.append(max(0, min(100, round(brightness))))
    return tuple(result)


def cymbal_circuits() -> dict[str, int]:
    """Physical CTB16PC outputs; independent left and right cymbals."""
    return {"left": 2, "right": 10}
