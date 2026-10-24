"""Conservative per-source presence screening; singer identity remains unverified."""
import numpy as np


def screen_clock(clock, probabilities, *, probability_hop=.032, clock_hop=.01,
                 threshold=.15, context_frames=2, minimum_frames=5):
    probabilities = np.asarray(probabilities)
    if (probabilities.ndim != 1 or not len(probabilities)
            or not np.isfinite(probabilities).all()
            or np.any(probabilities < 0) or np.any(probabilities > 1)):
        raise ValueError('Finite per-source probabilities in 0..1 required')
    energy = np.asarray(clock['energy'])
    if abs(len(energy)*clock_hop-len(probabilities)*probability_hop) > probability_hop+.01:
        raise ValueError('Presence evidence and source clock have different durations')
    # Small context covers detector windows across consonants. No song-specific
    # timestamp, ending mask, copied singer lane or added release tail exists.
    padded = np.pad(probabilities, (context_frames, context_frames))
    nearby = np.lib.stride_tricks.sliding_window_view(padded, 2*context_frames+1).max(axis=1)
    indices = np.floor(np.arange(len(energy))*clock_hop/probability_hop).astype(int)
    scores = nearby[np.minimum(indices, len(nearby)-1)]
    active = (energy > 0) & (scores >= threshold)
    edges = np.flatnonzero(np.diff(np.r_[False, active, False]))
    for start, end in zip(edges[::2], edges[1::2]):
        if end-start < minimum_frames:
            active[start:end] = False
    result = {key: np.asarray(value).copy() for key, value in clock.items()}
    result['energy'] = np.where(active, energy, 0).astype('f4')
    result['shapes'] = np.where(active, clock['shapes'], 0).astype('i1')
    result['presence_probability'] = scores.astype('f4')
    return result
