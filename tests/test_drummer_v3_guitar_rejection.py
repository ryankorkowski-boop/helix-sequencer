from __future__ import annotations

import numpy as np

from core.drummer_v3_analysis import analyze_drummer_features


def _spike(length: int = 400, positions=(100, 200, 300), amplitude: float = 1.0) -> np.ndarray:
    x = np.zeros(length, dtype=float)
    for p in positions:
        x[p] = amplitude
        if p + 1 < length:
            x[p + 1] = amplitude * 0.15
    return x


def test_tonal_guitar_transients_do_not_become_drum_events() -> None:
    # Simulate a guitar-heavy mix: the full mix has sharp attacks and HPSS leaks
    # some of those attacks into the percussive bands, but the percussive/harmonic
    # energy ratio remains low. The detector must refuse to promote them to drums.
    n = 400
    low = _spike(n, amplitude=0.9)
    mid = _spike(n, amplitude=0.8)
    high = _spike(n, amplitude=0.5)
    drum_low = _spike(n, amplitude=0.45)
    drum_mid = _spike(n, amplitude=0.40)
    drum_high = _spike(n, amplitude=0.20)
    quality = np.full(n, 0.12, dtype=float)
    rms = np.maximum(low + mid + high, 0.001)
    times = np.arange(n, dtype=float) / 100.0

    events = analyze_drummer_features(
        low=low,
        mid=mid,
        high=high,
        rms=rms,
        times=times,
        drum_low=drum_low,
        drum_mid=drum_mid,
        drum_high=drum_high,
        frame_rate=100.0,
        drum_percussive_ratio=quality,
        min_percussive_ratio=0.30,
    )

    assert events == []


def test_real_percussive_quality_can_still_produce_typed_events() -> None:
    n = 400
    low = _spike(n, amplitude=1.0)
    mid = _spike(n, amplitude=0.6)
    high = _spike(n, amplitude=0.35)
    drum_low = _spike(n, amplitude=1.0)
    drum_mid = _spike(n, amplitude=0.65)
    drum_high = _spike(n, amplitude=0.35)
    quality = np.full(n, 0.82, dtype=float)
    rms = np.maximum(low + mid + high, 0.001)
    times = np.arange(n, dtype=float) / 100.0

    events = analyze_drummer_features(
        low=low,
        mid=mid,
        high=high,
        rms=rms,
        times=times,
        drum_low=drum_low,
        drum_mid=drum_mid,
        drum_high=drum_high,
        frame_rate=100.0,
        drum_percussive_ratio=quality,
        min_percussive_ratio=0.30,
    )

    assert events
