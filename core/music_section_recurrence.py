"""Diagnostic-only recurrence evidence for candidate song sections.

A repeated chroma texture is evidence of similarity, not proof of a chorus.
No output from this module is eligible for automatic template promotion.
"""
from __future__ import annotations

import math
from typing import Sequence


def find_recurrent_regions(
    times_s: Sequence[float],
    chroma_vectors: Sequence[Sequence[float]],
    *,
    duration_s: float,
    region_s: float = 8.0,
    minimum_separation_s: float = 12.0,
    similarity_threshold: float = 0.86,
    max_pairs: int = 20,
) -> list[dict[str, float | str]]:
    """Compare nonoverlapping time windows using normalized chroma averages.

    The output is bounded, deterministic, and sorted by earlier time. Input
    should be downsampled to roughly one feature frame per second.
    """
    if not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("duration must be positive and finite")
    if not math.isfinite(region_s) or region_s <= 0 or not math.isfinite(minimum_separation_s) or minimum_separation_s < region_s:
        raise ValueError("invalid region and separation")
    if not math.isfinite(similarity_threshold) or not 0 <= similarity_threshold <= 1 or max_pairs < 0:
        raise ValueError("invalid similarity threshold or pair limit")
    if len(times_s) != len(chroma_vectors):
        raise ValueError("time and chroma frame counts differ")
    if not times_s or max_pairs == 0:
        return []
    width = len(chroma_vectors[0])
    if width == 0:
        return []
    previous = -1.0
    for t, vector in zip(times_s, chroma_vectors):
        if not math.isfinite(t) or t <= previous or t < 0 or t > duration_s:
            raise ValueError("times must be finite, increasing and within audio")
        if len(vector) != width or any(not math.isfinite(v) or v < 0 for v in vector):
            raise ValueError("chroma must be finite nonnegative fixed-width vectors")
        previous = t
    # Nonoverlapping windows keep work bounded and prevent overlapping frames
    # from producing misleadingly perfect self-similarity.
    windows: list[tuple[float, list[float]]] = []
    start = 0.0
    while start + region_s <= duration_s + 1e-9:
        indices = [i for i, t in enumerate(times_s) if start <= t < start + region_s]
        if len(indices) >= 3:
            vector = [sum(chroma_vectors[i][k] for i in indices) / len(indices) for k in range(width)]
            variation = sum(
                sum((chroma_vectors[i][k] - vector[k]) ** 2 for k in range(width))
                for i in indices
            ) / (len(indices) * width)
            # A stationary tone has high cosine similarity everywhere, but
            # carries no evidence of a repeated musical phrase.
            norm = math.sqrt(sum(x * x for x in vector))
            if norm > 1e-8 and variation >= 0.0025:
                windows.append((start, [x / norm for x in vector]))
        start += region_s
    matches: list[tuple[float, float, float]] = []
    for i, (start_a, vec_a) in enumerate(windows):
        for start_b, vec_b in windows[i + 1:]:
            if start_b - start_a < minimum_separation_s:
                continue
            score = max(0.0, min(1.0, sum(x * y for x, y in zip(vec_a, vec_b))))
            if score >= similarity_threshold:
                matches.append((score, start_a, start_b))
    matches.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [
        {"first_start_seconds": round(a, 3), "repeat_start_seconds": round(b, 3),
         "window_seconds": region_s, "similarity": round(score, 4),
         "confidence": round(min(0.65, score * 0.65), 4),
         "reason": "chroma_recurrence_candidate"}
        for score, a, b in matches[:max_pairs]
    ]
