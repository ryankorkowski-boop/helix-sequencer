"""Shared vocal-clock checks; detector scores never certify singer identity."""
from __future__ import annotations

import numpy as np
from models.band_sampler_logic import SHAPE_NAMES


def validate_lanes(energy, shapes):
    energy, shapes = np.asarray(energy), np.asarray(shapes)
    if (energy.ndim != 2 or energy.shape[1] != 2 or not len(energy)
            or shapes.shape != energy.shape or not np.isfinite(energy).all()
            or np.any((energy < 0) | (energy > 1))
            or not np.isfinite(shapes).all() or np.any(shapes != np.floor(shapes))
            or np.any((shapes < 0) | (shapes >= len(SHAPE_NAMES)))):
        raise ValueError('Invalid source-bound vocal frame arrays')
    return energy, shapes


def independence_metrics(energy, shapes):
    """Measure clocks, including gain copies that have different file hashes.

    Similar activity alone is not a rejection: real harmony can sing in unison.
    Exact shape/activity duplication AND proportional envelopes are rejected.
    """
    energy, shapes = validate_lanes(energy, shapes)
    active = (energy > 0) & (shapes != SHAPE_NAMES.index('REST'))
    x, y = energy.astype('float64').T
    denominator = float(x @ x)
    gain = float(x @ y) / denominator if denominator > 0 else 0.0
    residual = float(np.linalg.norm(y-gain*x) / max(np.linalg.norm(y), 1e-12))
    shared = active.all(axis=1)
    union = active.any(axis=1)
    correlation = None
    if shared.sum() >= 2 and np.std(x[shared]) > 0 and np.std(y[shared]) > 0:
        correlation = float(np.corrcoef(x[shared], y[shared])[0, 1])
    same_activity = bool(np.array_equal(active[:, 0], active[:, 1]))
    same_shapes = bool(np.array_equal(shapes[:, 0], shapes[:, 1]))
    return dict(non_rest_frames=active.sum(axis=0).astype(int).tolist(),
                unique_active_frames=[int(np.sum(active[:, i] & ~active[:, 1-i])) for i in (0, 1)],
                activity_jaccard=float(shared.sum()/max(1, union.sum())),
                shared_active_envelope_correlation=correlation,
                gain_normalized_residual=residual,
                duplicate_clock=bool(union.any() and same_activity and same_shapes and residual < 1e-4))


def screen_candidate_lanes(energy, shapes, probabilities, *, fps=100,
                           onset=.65, offset=.35, minimum_seconds=.15):
    """Suppress uncertain source events independently, without copying phones.

    Hysteresis retains an existing event in the uncertain band only after a
    confident onset. An acoustic REST resets the detector immediately. Short
    runs are removed, never extended. Defaults are conservative engineering
    settings, not calibrated singing probabilities or lexical confidence.
    """
    energy, shapes = validate_lanes(energy, shapes)
    probabilities = np.asarray(probabilities)
    if (probabilities.shape != energy.shape or not np.isfinite(probabilities).all()
            or np.any((probabilities < 0) | (probabilities > 1))):
        raise ValueError('Finite independent per-frame presence probabilities required')
    if not np.isfinite(fps) or fps <= 0 or not 0 <= offset < onset <= 1 or minimum_seconds <= 0:
        raise ValueError('Invalid vocal confidence policy')
    active = np.zeros(energy.shape, dtype=bool)
    minimum = max(1, int(np.ceil(minimum_seconds*fps)))
    for lane in (0, 1):
        sounding = False
        for frame in range(len(energy)):
            acoustic = energy[frame, lane] > 0 and shapes[frame, lane] != 0
            score = probabilities[frame, lane]
            sounding = bool(acoustic and (score >= onset or (sounding and score > offset)))
            active[frame, lane] = sounding
        edges = np.flatnonzero(np.diff(np.r_[False, active[:, lane], False]))
        for start, end in zip(edges[::2], edges[1::2]):
            if end-start < minimum:
                active[start:end, lane] = False
    screened_energy = np.where(active, energy, 0).astype('f4')
    screened_shapes = np.where(active, shapes, 0).astype('i1')
    metrics = independence_metrics(screened_energy, screened_shapes)
    duplicate = metrics['duplicate_clock']
    if duplicate:
        # Abstain from a second singer rather than display a duplicate mouth.
        screened_energy[:, 1] = 0
        screened_shapes[:, 1] = 0
    return screened_energy, screened_shapes, dict(
        state='REJECTED' if duplicate else 'ESTIMATED',
        independent_backing_verified=False, identity_confidence=None,
        policy=dict(onset=onset, offset=offset, minimum_seconds=minimum_seconds, fps=fps),
        metrics_before_duplicate_suppression=metrics,
        removed_non_rest_frames=(np.sum((energy > 0) & (shapes != 0), axis=0)
                                 - np.sum(screened_energy > 0, axis=0)).astype(int).tolist(),
        limitation='Presence scores reject uncertain activity; singer identity and lexical phonemes remain unverified.')
