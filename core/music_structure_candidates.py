"""Conservative, label-neutral musical change-point candidates.

Produces *diagnostic* boundaries, not verified verse/chorus labels. The
candidate confidence is deliberately below the automatic promotion gate.
"""
from __future__ import annotations

import math
from typing import Sequence


def detect_structure_candidates(
    times_s: Sequence[float],
    energies: Sequence[float],
    chroma_vectors: Sequence[Sequence[float]],
    *,
    duration_s: float,
    min_segment_s: float = 8.0,
    context_s: float = 4.0,
    max_boundaries: int = 24,
) -> list[dict[str, float | str]]:
    """Return sorted change points from independent energy and chroma changes.

    Vectors are per-frame (not 12-by-frame). This routine is O(N*K) for
    context windows and should be fed downsampled (about 1 Hz) features.
    """
    n = len(times_s)
    if n != len(energies) or n != len(chroma_vectors):
        raise ValueError("times, energies and chroma vectors must have equal lengths")
    if not math.isfinite(duration_s) or duration_s <= 0 or min_segment_s <= 0 or context_s <= 0 or max_boundaries < 0:
        raise ValueError("invalid detection parameters")
    if n < 4 or max_boundaries == 0:
        return []
    width = len(chroma_vectors[0])
    if width == 0:
        return []
    previous = -1.0
    for t, e, vector in zip(times_s, energies, chroma_vectors):
        if not math.isfinite(t) or t <= previous or t < 0 or t > duration_s:
            raise ValueError("timestamps must be finite and strictly increasing")
        if not math.isfinite(e) or e < 0:
            raise ValueError("energies must be finite and nonnegative")
        if len(vector) != width or any(not math.isfinite(v) for v in vector):
            raise ValueError("chroma vectors must be finite and fixed width")
        previous = t
    def mean_vector(indices: list[int]) -> list[float]:
        return [sum(chroma_vectors[j][k] for j in indices) / len(indices) for k in range(width)]
    scores: list[tuple[float, float]] = []
    for i in range(1, n - 1):
        t = times_s[i]
        if t < min_segment_s or duration_s - t < min_segment_s:
            continue
        left = [j for j in range(i) if t - context_s <= times_s[j] < t]
        right = [j for j in range(i, n) if t <= times_s[j] < t + context_s]
        if len(left) < 2 or len(right) < 2:
            continue
        a, b = mean_vector(left), mean_vector(right)
        chroma_distance = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / width)
        energy_distance = abs(sum(energies[j] for j in left) / len(left) - sum(energies[j] for j in right) / len(right))
        # Energy and chroma both matter; no assumption that novelty equals chorus.
        score = 0.65 * min(1.0, chroma_distance) + 0.35 * min(1.0, energy_distance)
        scores.append((score, t))
    if not scores:
        return []
    # Require a clear departure from baseline rather than always splitting.
    sorted_scores = sorted(score for score, _ in scores)
    median = sorted_scores[len(sorted_scores) // 2]
    threshold = max(0.20, median * 1.8)
    selected: list[tuple[float, float]] = []
    for score, t in sorted(scores, key=lambda pair: (-pair[0], pair[1])):
        if score < threshold or any(abs(t - chosen_t) < min_segment_s for _, chosen_t in selected):
            continue
        selected.append((score, t))
        if len(selected) >= max_boundaries:
            break
    return [
        {"time_seconds": round(t, 3), "novelty": round(score, 4),
         "confidence": round(min(0.65, score * 0.65), 4),
         "reason": "energy_chroma_novelty_candidate"}
        for score, t in sorted(selected, key=lambda pair: pair[1])
    ]
