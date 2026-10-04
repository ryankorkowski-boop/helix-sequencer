"""Multi-detector Drummer V3 analysis inspired by xLights AutoSequencer architecture.

This module is intentionally dependency-light. It accepts precomputed audio features so
Helix can use a Demucs drum stem when available without making stem separation mandatory.
It does not create visual channels; it emits typed musical candidates for the V3 performer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Sequence

import numpy as np


class DrumType(str, Enum):
    KICK = "kick"
    SNARE = "snare"
    HI_HAT = "hi_hat"
    CYMBAL = "cymbal"
    TOM_HIGH = "tom_high"
    TOM_MID = "tom_mid"
    TOM_FLOOR = "tom_floor"


@dataclass(frozen=True)
class Candidate:
    time: float
    kind: DrumType
    strength: float
    source: str


@dataclass(frozen=True)
class DrumEvent:
    time: float
    kind: DrumType
    confidence: float
    votes: tuple[str, ...] = field(default_factory=tuple)


def _adaptive_floor(x: np.ndarray, window: int = 101) -> np.ndarray:
    """Centered rolling median floor, robust to section-level loudness changes."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return x.copy()
    window = max(3, int(window) | 1)
    pad = window // 2
    xp = np.pad(x, (pad, pad), mode="edge")
    out = np.empty_like(x)
    for i in range(x.size):
        out[i] = np.median(xp[i:i + window])
    return out


def _positive_flux(band_energy: np.ndarray) -> np.ndarray:
    e = np.maximum(np.asarray(band_energy, dtype=float), 0.0)
    if e.size == 0:
        return e.copy()
    d = np.diff(np.log1p(e), prepend=np.log1p(e[0]))
    return np.maximum(d, 0.0)


def _peaks(x: np.ndarray, threshold: np.ndarray, min_gap: int = 2) -> np.ndarray:
    """Simple deterministic local maxima with adaptive threshold and re-arm gap."""
    x = np.asarray(x, dtype=float)
    threshold = np.asarray(threshold, dtype=float)
    if x.size < 3:
        return np.empty(0, dtype=int)
    hits: list[int] = []
    last = -10**9
    for i in range(1, x.size - 1):
        if i - last < min_gap:
            continue
        if x[i] >= threshold[i] and x[i] >= x[i - 1] and x[i] > x[i + 1]:
            hits.append(i)
            last = i
    return np.asarray(hits, dtype=int)


def _emit_family(signal: np.ndarray, family: DrumType, source: str, strength_floor: float,
                 min_gap: int) -> list[Candidate]:
    flux = _positive_flux(signal)
    floor = _adaptive_floor(flux)
    threshold = floor + strength_floor
    peaks = _peaks(flux, threshold, min_gap=min_gap)
    return [Candidate(float(i), family, float(flux[i]), source) for i in peaks]


def analyze_drummer_features(
    *,
    low: Sequence[float],
    mid: Sequence[float],
    high: Sequence[float],
    times: Sequence[float] | None = None,
    drum_low: Sequence[float] | None = None,
    drum_mid: Sequence[float] | None = None,
    drum_high: Sequence[float] | None = None,
    beat_indices: Iterable[int] = (),
    frame_rate: float = 100.0,
) -> list[DrumEvent]:
    """Produce conservative typed drummer events from independent detector families.

    `low/mid/high` are full-mix band-energy tracks. `drum_*` are optional isolated-drum
    tracks. The latter receive additional vote weight. Beat positions are contextual only.
    """
    low = np.asarray(low, dtype=float)
    mid = np.asarray(mid, dtype=float)
    high = np.asarray(high, dtype=float)
    n = min(len(low), len(mid), len(high))
    low, mid, high = low[:n], mid[:n], high[:n]
    if times is None:
        times_arr = np.arange(n, dtype=float) / frame_rate
    else:
        times_arr = np.asarray(times, dtype=float)[:n]

    candidates: list[Candidate] = []
    # Independent full-mix detector families.
    candidates += _emit_family(low, DrumType.KICK, "mix.low_flux", 0.06, 5)
    candidates += _emit_family(mid, DrumType.SNARE, "mix.mid_flux", 0.05, 4)
    candidates += _emit_family(high, DrumType.HI_HAT, "mix.high_flux", 0.035, 2)
    candidates += _emit_family(high, DrumType.CYMBAL, "mix.high_flux_long", 0.08, 8)

    # Optional isolated drum stem: stronger evidence and tom analysis.
    if drum_low is not None and drum_mid is not None and drum_high is not None:
        dl = np.asarray(drum_low, dtype=float)[:n]
        dm = np.asarray(drum_mid, dtype=float)[:n]
        dh = np.asarray(drum_high, dtype=float)[:n]
        candidates += _emit_family(dl, DrumType.KICK, "drum.low_flux", 0.035, 5)
        candidates += _emit_family(dm, DrumType.SNARE, "drum.mid_flux", 0.03, 4)
        candidates += _emit_family(dh, DrumType.HI_HAT, "drum.high_flux", 0.02, 2)
        candidates += _emit_family(dh, DrumType.CYMBAL, "drum.high_flux_long", 0.045, 8)

        # Toms: detect mid-band transients, then classify by local spectral centroid proxy.
        tm = _positive_flux(dm)
        floor = _adaptive_floor(tm)
        for i in _peaks(tm, floor + 0.025, min_gap=6):
            # Without a full STFT centroid, use low/mid energy ratio as a stable proxy.
            ratio = float(dl[i] / (dm[i] + 1e-9))
            kind = DrumType.TOM_HIGH if ratio > 0.80 else DrumType.TOM_MID if ratio > 0.35 else DrumType.TOM_FLOOR
            candidates.append(Candidate(float(times_arr[i]), kind, float(tm[i]), "drum.tom_band"))

    # Convert frame indices from the simple full-mix detector to seconds.
    normalized: list[Candidate] = []
    for c in candidates:
        if c.source.startswith("mix.") or c.source.startswith("drum."):
            # _emit_family emitted a frame index for mix; tom already used seconds.
            if c.time >= 0 and c.time < n:
                normalized.append(Candidate(float(times_arr[int(c.time)]), c.kind, c.strength, c.source))
            else:
                normalized.append(c)
    candidates = normalized

    # Consensus clustering: nearby independent detectors vote on one event.
    clusters: list[list[Candidate]] = []
    for c in sorted(candidates, key=lambda z: z.time):
        if clusters and c.kind == clusters[-1][0].kind and abs(c.time - clusters[-1][-1].time) <= 0.045:
            clusters[-1].append(c)
        else:
            clusters.append([c])

    beat_set = np.asarray(list(beat_indices), dtype=int)
    events: list[DrumEvent] = []
    for cluster in clusters:
        kinds = {c.kind for c in cluster}
        if len(kinds) != 1:
            continue
        kind = cluster[0].kind
        sources = tuple(dict.fromkeys(c.source for c in cluster))
        weighted = sum((2.0 if c.source.startswith("drum.") else 1.0) for c in cluster)
        confidence = min(1.0, 0.18 + 0.18 * weighted)
        # Context boosts confidence only; it never creates an event.
        if beat_set.size:
            tframe = int(round(cluster[0].time * frame_rate))
            if np.min(np.abs(beat_set - tframe)) <= 2:
                confidence = min(1.0, confidence + 0.08)
        if confidence >= 0.45:
            events.append(DrumEvent(cluster[0].time, kind, confidence, sources))

    return events
