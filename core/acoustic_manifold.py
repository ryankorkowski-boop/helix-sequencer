"""Music-first acoustic manifold primitives for Helix.

"Birdsong" is a metaphor here: these features describe ordinary music as a
moving multidimensional organism. No bird detection or species classification
is performed by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class AcousticState:
    time_ms: int
    energy: float
    onset: float
    pitch: float
    pitch_confidence: float
    centroid: float
    bandwidth: float
    flux: float
    low_energy: float
    mid_energy: float
    high_energy: float
    pressure: float
    tension: float


def _norm(value: float, lo: float, hi: float) -> float:
    if not isfinite(value) or hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def build_state(
    *,
    time_ms: int,
    energy: float,
    onset: float = 0.0,
    pitch_hz: float = 0.0,
    pitch_confidence: float = 0.0,
    centroid_hz: float = 0.0,
    bandwidth_hz: float = 0.0,
    flux: float = 0.0,
    low_energy: float = 0.0,
    mid_energy: float = 0.0,
    high_energy: float = 0.0,
) -> AcousticState:
    e = max(0.0, float(energy)) if isfinite(float(energy)) else 0.0
    o = _norm(float(onset), 0.0, 1.0)
    pitch = _norm(float(pitch_hz), 40.0, 4000.0)
    centroid = _norm(float(centroid_hz), 80.0, 10000.0)
    bandwidth = _norm(float(bandwidth_hz), 50.0, 8000.0)
    flux_n = _norm(float(flux), 0.0, 1.0)
    low = max(0.0, float(low_energy)) if isfinite(float(low_energy)) else 0.0
    mid = max(0.0, float(mid_energy)) if isfinite(float(mid_energy)) else 0.0
    high = max(0.0, float(high_energy)) if isfinite(float(high_energy)) else 0.0
    band_total = low + mid + high
    if band_total > 0:
        low, mid, high = low / band_total, mid / band_total, high / band_total

    # Musical abstractions inspired by the idea of motor trajectories:
    # pressure tracks dynamic force; tension tracks spectral/pitch complexity.
    pressure = max(0.0, min(1.0, 0.68 * min(1.0, e) + 0.32 * o))
    tension = max(
        0.0,
        min(1.0, 0.42 * centroid + 0.28 * bandwidth + 0.20 * flux_n + 0.10 * (1.0 - min(1.0, float(pitch_confidence)))),
    )

    return AcousticState(
        time_ms=max(0, int(time_ms)),
        energy=min(1.0, e),
        onset=o,
        pitch=pitch,
        pitch_confidence=max(0.0, min(1.0, float(pitch_confidence))),
        centroid=centroid,
        bandwidth=bandwidth,
        flux=flux_n,
        low_energy=low,
        mid_energy=mid,
        high_energy=high,
        pressure=pressure,
        tension=tension,
    )


def spatial_intent(state: AcousticState) -> dict[str, float]:
    """Map acoustic state into renderer-independent normalized spatial intent."""
    # Pitch drives vertical placement; energy drives visual force.  The renderer
    # decides which real physical models intersect the intended trajectory.
    return {
        "x": 0.5 + (state.tension - 0.5) * 0.8,
        "y": state.pitch,
        "z": 0.5 + (state.pressure - 0.5) * 0.8,
        "brightness": max(state.energy, state.onset * 0.85),
        "hue": state.centroid,
        "width": 0.15 + 0.65 * state.bandwidth,
        "velocity": 0.15 + 0.85 * max(state.flux, state.onset),
    }
