"""Evidence-first audio/video synchronization helpers for Wadena calibration.

This module deliberately avoids global duration warping. It compares independent
transition/energy envelopes and returns candidate local anchors with uncertainty.
It does not decide that two recordings are the same performance; that remains an
explicit evidence-gate decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence


@dataclass(frozen=True)
class EnvelopePoint:
    time: float
    value: float


@dataclass(frozen=True)
class AnchorMatch:
    video_time: float
    audio_time: float
    offset: float
    score: float
    uncertainty: float


@dataclass(frozen=True)
class SyncAssessment:
    anchors: tuple[AnchorMatch, ...]
    offsets: tuple[float, ...]
    stable: bool
    same_performance_supported: bool
    reason: str


def _validate(points: Iterable[EnvelopePoint]) -> tuple[EnvelopePoint, ...]:
    result = tuple(points)
    if any(not isfinite(p.time) or not isfinite(p.value) for p in result):
        raise ValueError("envelope points must be finite")
    if any(b.time <= a.time for a, b in zip(result, result[1:])):
        raise ValueError("envelope times must be strictly increasing")
    return result


def match_transition_anchors(
    video: Sequence[EnvelopePoint],
    audio: Sequence[EnvelopePoint],
    *,
    tolerance: float = 1.5,
    min_score: float = 0.25,
) -> tuple[AnchorMatch, ...]:
    """Match each video transition to the strongest nearby audio transition.

    `value` is an already-normalized transition/energy strength. This function
    never stretches either timeline and never assumes a single global offset.
    """
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    v = _validate(video)
    a = _validate(audio)
    matches: list[AnchorMatch] = []
    for vp in v:
        nearby = [ap for ap in a if abs(ap.time - vp.time) <= tolerance]
        if not nearby:
            continue
        ranked = sorted(
            nearby,
            key=lambda ap: (abs(ap.time - vp.time), -ap.value),
        )
        ap = ranked[0]
        distance_score = max(0.0, 1.0 - abs(ap.time - vp.time) / tolerance)
        score = max(0.0, min(1.0, distance_score * max(0.0, min(1.0, ap.value))))
        if score < min_score:
            continue
        uncertainty = max(0.05, min(tolerance, abs(ap.time - vp.time) + 0.05))
        matches.append(
            AnchorMatch(
                video_time=vp.time,
                audio_time=ap.time,
                offset=ap.time - vp.time,
                score=score,
                uncertainty=uncertainty,
            )
        )
    return tuple(matches)


def assess_piecewise_alignment(
    anchors: Sequence[AnchorMatch],
    *,
    max_offset_spread: float = 0.75,
    min_independent_anchors: int = 3,
) -> SyncAssessment:
    """Assess whether matched anchors support a stable alignment hypothesis.

    A stable offset is evidence for alignment, not proof that the video and LMS
    are the same performance. That stronger claim requires edit/performance
    evidence outside this numeric helper.
    """
    if max_offset_spread < 0:
        raise ValueError("max_offset_spread must be non-negative")
    ordered = tuple(sorted(anchors, key=lambda x: x.video_time))
    offsets = tuple(a.offset for a in ordered)
    if len(ordered) < min_independent_anchors:
        return SyncAssessment(
            anchors=ordered,
            offsets=offsets,
            stable=False,
            same_performance_supported=False,
            reason="insufficient independent anchors",
        )
    spread = max(offsets) - min(offsets)
    stable = spread <= max_offset_spread
    return SyncAssessment(
        anchors=ordered,
        offsets=offsets,
        stable=stable,
        same_performance_supported=False,
        reason=(
            "multiple anchors support a stable local offset; performance identity remains unproven"
            if stable
            else "anchor offsets disagree beyond the configured uncertainty bound"
        ),
    )


def piecewise_offset_intervals(
    anchors: Sequence[AnchorMatch],
) -> tuple[tuple[float, float, float, float], ...]:
    """Return `(video_start, video_end, offset, uncertainty)` intervals.

    Intervals are midpoint-partitioned between adjacent anchors; this is a
    diagnostic representation only and does not modify the underlying media.
    """
    ordered = tuple(sorted(anchors, key=lambda x: x.video_time))
    if not ordered:
        return ()
    bounds: list[tuple[float, float, float, float]] = []
    for i, anchor in enumerate(ordered):
        left = anchor.video_time if i == 0 else (ordered[i - 1].video_time + anchor.video_time) / 2
        right = anchor.video_time if i == len(ordered) - 1 else (anchor.video_time + ordered[i + 1].video_time) / 2
        bounds.append((left, right, anchor.offset, anchor.uncertainty))
    return tuple(bounds)
