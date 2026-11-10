"""Temporal propagation for Wadena landmark choreography.

The spatial graph answers *where* a gesture travels.  This module answers
*when* each landmark receives it.  It deliberately remains renderer- and
channel-independent so the effect compiler can later translate the samples
into AC-safe R/G/W output.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp

from core.wadena_spatial_graph import WadenaSpatialGraph, wadena_spatial_graph


@dataclass(frozen=True)
class PropagationProfile:
    """Timing shape of a travelling impulse or phrase."""

    launch_s: float = 0.0
    travel_s: float = 0.18
    attack_s: float = 0.05
    decay_s: float = 0.35
    hop_decay: float = 1.0


@dataclass(frozen=True)
class PropagationSample:
    """One landmark's renderer-independent temporal event."""

    landmark: str
    arrival_s: float
    release_s: float
    weight: float
    order: int


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _profile(profile: PropagationProfile) -> PropagationProfile:
    """Normalize malformed timing values without creating negative time."""
    return PropagationProfile(
        launch_s=max(0.0, float(profile.launch_s)),
        travel_s=max(0.0, float(profile.travel_s)),
        attack_s=max(0.0, float(profile.attack_s)),
        decay_s=max(0.0, float(profile.decay_s)),
        hop_decay=_clamp(float(profile.hop_decay), 0.0, 1.0),
    )


def compile_propagation(
    start: str,
    end: str,
    strength: float = 1.0,
    profile: PropagationProfile | None = None,
    graph: WadenaSpatialGraph | None = None,
) -> tuple[PropagationSample, ...]:
    """Compile a named route into deterministic temporal propagation samples.

    ``travel_s`` is the time between landmark arrivals.  ``attack_s`` and
    ``decay_s`` describe the event lifetime after arrival.  ``hop_decay``
    optionally attenuates later landmarks, allowing a wave to lose pressure
    as it crosses the display.

    Invalid landmarks/routes fail safe to an empty tuple.  No physical channel
    is selected here and no RGB interpretation is introduced.
    """
    graph = graph or wadena_spatial_graph()
    route = graph.route(start, end)
    if not route:
        return ()

    strength = _clamp(float(strength), 0.0, 1.0)
    if strength <= 0.0:
        return ()

    timing = _profile(profile or PropagationProfile())
    lifetime = timing.attack_s + timing.decay_s
    return tuple(
        PropagationSample(
            landmark=name,
            arrival_s=round(timing.launch_s + (index * timing.travel_s), 6),
            release_s=round(
                timing.launch_s + (index * timing.travel_s) + lifetime, 6
            ),
            weight=round(strength * (timing.hop_decay**index), 6),
            order=index,
        )
        for index, name in enumerate(route)
    )


def compile_direction_propagation(
    direction: str,
    strength: float = 1.0,
    profile: PropagationProfile | None = None,
    graph: WadenaSpatialGraph | None = None,
) -> tuple[PropagationSample, ...]:
    """Compile a directional wave using the graph's stable landmark order."""
    graph = graph or wadena_spatial_graph()
    names = graph.order(direction)
    if not names:
        return ()

    strength = _clamp(float(strength), 0.0, 1.0)
    if strength <= 0.0:
        return ()

    timing = _profile(profile or PropagationProfile())
    lifetime = timing.attack_s + timing.decay_s
    return tuple(
        PropagationSample(
            landmark=name,
            arrival_s=round(timing.launch_s + (index * timing.travel_s), 6),
            release_s=round(
                timing.launch_s + (index * timing.travel_s) + lifetime, 6
            ),
            weight=round(strength * (timing.hop_decay**index), 6),
            order=index,
        )
        for index, name in enumerate(names)
    )


def sample_weight_at(
    sample: PropagationSample,
    time_s: float,
    profile: PropagationProfile | None = None,
) -> float:
    """Evaluate a sample's attack/decay envelope at one time point.

    The envelope is zero before arrival, rises linearly through attack, then
    decays exponentially over ``decay_s``.  A zero-duration attack/decay is
    handled deterministically and never produces NaN or division by zero.
    """
    timing = _profile(profile or PropagationProfile())
    t = float(time_s)
    if t < sample.arrival_s:
        return 0.0

    elapsed = t - sample.arrival_s
    if timing.attack_s > 0.0 and elapsed < timing.attack_s:
        return round(sample.weight * (elapsed / timing.attack_s), 6)

    if timing.decay_s <= 0.0:
        return round(sample.weight, 6) if elapsed <= timing.attack_s else 0.0

    decay_elapsed = max(0.0, elapsed - timing.attack_s)
    return round(sample.weight * exp(-decay_elapsed / timing.decay_s), 6)
