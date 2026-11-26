"""Streaming RGB frame quality checks for native-preview acceptance.

Consumes decoded RGB frames; does not assume synthetic XSQ effects imply pixels.
Thresholds are conservative defaults and must be calibrated to real layouts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class FrameQualityThresholds:
    max_white_fraction: float = 0.80
    max_blank_frame_fraction: float = 0.65
    max_frozen_transition_fraction: float = 0.85
    min_mean_saturation: float = 0.08


def evaluate_rgb_frames(
    frames: Iterable[np.ndarray],
    thresholds: FrameQualityThresholds = FrameQualityThresholds(),
) -> dict:
    """Score sampled HxWx3 uint8 RGB frames with bounded streaming memory.

    Excludes near-black pixels from saturation denominator so intentional
    musical rests are not penalized as desaturated color. Requires at least
    two frames for a motion verdict. Sampling cadence is caller-controlled.
    """
    count = blank = white = frozen = 0
    saturation_sum = 0.0
    previous = None
    for frame in frames:
        rgb = np.asarray(frame)
        if rgb.ndim != 3 or rgb.shape[-1] != 3 or rgb.size == 0:
            raise ValueError("Expected nonempty HxWx3 RGB frame")
        if rgb.dtype != np.uint8:
            raise ValueError("Expected uint8 RGB values")
        # Compare at fixed coarse resolution for stable memory/cost.
        sy = max(1, rgb.shape[0] // 96)
        sx = max(1, rgb.shape[1] // 160)
        sample = rgb[::sy, ::sx, :].astype(np.int16)
        hi = sample.max(axis=2)
        lo = sample.min(axis=2)
        lit = hi > 28
        blank += int(np.mean(lit) < 0.005)
        white_mask = lit & (lo > 180) & ((hi - lo) < 24)
        # The dark yard must not dilute white dominance among illuminated pixels.
        # Ignore blank frames; this is an RGB diagnostic, not an AC color gate.
        white_fraction = float(np.count_nonzero(white_mask) / max(1, np.count_nonzero(lit)))
        white += int(np.mean(lit) >= 0.005 and white_fraction > thresholds.max_white_fraction)
        if np.any(lit):
            saturation_sum += float(np.mean((hi[lit] - lo[lit]) / np.maximum(hi[lit], 1)))
        if previous is not None:
            frozen += int(previous.shape == sample.shape and
                          np.mean(np.abs(sample - previous)) < 1.0)
        previous = sample
        count += 1
    if count == 0:
        raise ValueError("No decoded RGB frames supplied")
    blank_fraction = blank / count
    white_fraction = white / count
    frozen_fraction = frozen / max(1, count - 1)
    mean_saturation = saturation_sum / count
    failures = []
    if blank_fraction > thresholds.max_blank_frame_fraction:
        failures.append("excess_blank_frames")
    if white_fraction > 0:
        failures.append("white_dominant_frames")
    if count > 1 and frozen_fraction > thresholds.max_frozen_transition_fraction:
        failures.append("frozen_or_repeated_frames")
    if mean_saturation < thresholds.min_mean_saturation and blank_fraction < 0.95:
        failures.append("insufficient_color_saturation")
    return {
        "schema": "helix.native_rgb_quality.v1",
        "sampled_frames": count,
        "blank_frame_fraction": round(blank_fraction, 5),
        "white_dominant_frame_fraction": round(white_fraction, 5),
        "frozen_transition_fraction": round(frozen_fraction, 5),
        "mean_lit_saturation": round(mean_saturation, 5),
        "thresholds": asdict(thresholds),
        "failures": failures,
        "passed": not failures,
        "scope": "sampled decoded RGB only; not native xLights proof or owner approval",
    }
