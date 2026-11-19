"""Drum-stem ride and floor-tom recovery stays off the full mix."""
from __future__ import annotations

import numpy as np

from audio.drum_stem_cohits import detect_stem_cohits
from mapping.drum_mapper import drummer_component_for_event


def _burst(sr, center_s, freq, ms=80, harmonics=()):
    n = int(sr * ms / 1000)
    t = np.arange(n) / sr
    env = np.linspace(0.0, 1.0, max(1, n // 8))
    env = np.concatenate([env, np.ones(n - env.size)])
    wave = np.sin(2 * np.pi * freq * t)
    for harmonic, gain in harmonics:
        wave += gain * np.sin(2 * np.pi * harmonic * t)
    start = int(center_s * sr)
    y = np.zeros(sr, dtype=np.float32)
    y[start:start + n] += (0.8 * wave * env).astype(np.float32)
    return y


def test_stem_separates_floor_tom_and_ride_from_kick():
    sr = 44100
    y = _burst(sr, 0.20, 55.0)
    y += _burst(sr, 0.50, 160.0, harmonics=((320.0, 0.3),))
    y += _burst(sr, 0.80, 4200.0, ms=50)
    added, report = detect_stem_cohits(y, sr)
    kinds = [event.drum_type for event in added]
    assert "tom" in kinds
    assert "ride" in kinds
    floors = [event for event in added if event.drum_type == "tom"]
    rides = [event for event in added if event.drum_type == "ride"]
    assert floors[0].frequency_band_info["tom_class"] == 3.0
    assert drummer_component_for_event(floors[0]) == "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR"
    assert drummer_component_for_event(rides[0]) == "HX_SNOWMAN_DRUMMER_V3_RIDE"
    assert report["measured"]["floor"] >= 1
    assert report["measured"]["ride"] >= 1
    # The 55 Hz burst is a kick body, not a floor tom.
    assert all(event.timestamp < 0.35 or event.timestamp > 0.4 for event in floors)
