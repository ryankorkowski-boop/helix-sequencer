"""Compile acoustic gestures into deterministic Wadena landmark propagation.

This module is an intent layer only. It does not know LOR channels, RGB values,
or electrical output. Acoustic analysis can describe *what* should move; this
compiler decides *where* that motion travels through the named Wadena topology.
The renderer/effect compiler remains responsible for turning the resulting
landmark weights into AC-safe effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp

from core.wadena_spatial_graph import WadenaSpatialGraph, wadena_spatial_graph
from core.wadena_spatial_propagation import (
    PropagationProfile,
    PropagationSample,
    compile_direction_propagation,
    compile_propagation,
)


@dataclass(frozen=True)
class SpatialGesture:
    """A musical gesture expressed without electrical semantics."""

    direction: str = "left_to_right"
    start: str | None = None
    end: str | None = None
    strength: float = 1.0
    spread: float = 1.0


@dataclass(frozen=True)
class LandmarkIntent:
    """One physical landmark's contribution to a gesture."""

    landmark: str
    weight: float
    order: int


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _ordered_falloff(count: int, spread: float) -> tuple[float, ...]:
    """Return a smooth deterministic center-weighted falloff."""
    if count <= 0:
        return ()
    sigma = max(0.25, float(spread))
    center = (count - 1) / 2.0
    return tuple(exp(-((index - center) ** 2) / (2.0 * sigma * sigma)) for index in range(count))


def compile_gesture(
    gesture: SpatialGesture,
    graph: WadenaSpatialGraph | None = None,
) -> tuple[LandmarkIntent, ...]:
    """Compile a gesture into stable landmark weights.

    Explicit start/end points use the named graph route. Otherwise a spatial
    direction uses the graph's deterministic landmark ordering. Invalid names
    fail safe to an empty intent rather than inventing a physical target.
    """
    graph = graph or wadena_spatial_graph()
    strength = _clamp(float(gesture.strength), 0.0, 1.0)

    if gesture.start is not None or gesture.end is not None:
        if gesture.start is None or gesture.end is None:
            return ()
        names = graph.route(gesture.start, gesture.end)
        if not names:
            return ()
    else:
        names = graph.order(gesture.direction)

    falloff = _ordered_falloff(len(names), gesture.spread)
    peak = max(falloff) if falloff else 1.0
    return tuple(
        LandmarkIntent(
            landmark=name,
            weight=round(strength * (value / peak), 6),
            order=index,
        )
        for index, (name, value) in enumerate(zip(names, falloff))
        if strength > 0.0
    )


def propagate_route(
    start: str,
    end: str,
    strength: float = 1.0,
    graph: WadenaSpatialGraph | None = None,
) -> tuple[LandmarkIntent, ...]:
    """Convenience API for impulse/phrase propagation between landmarks."""
    return compile_gesture(
        SpatialGesture(start=start, end=end, strength=strength),
        graph=graph,
    )


def compile_temporal_gesture(
    gesture: SpatialGesture,
    profile: PropagationProfile | None = None,
    graph: WadenaSpatialGraph | None = None,
) -> tuple[PropagationSample, ...]:
    """Compile a spatial gesture into a travelling temporal wave.

    This is the bridge between the existing spatial intent API and the new
    temporal propagation primitive.  Spatial ordering remains deterministic;
    arrival/release timing is handled separately by ``PropagationProfile``.
    """
    graph = graph or wadena_spatial_graph()
    if gesture.start is not None or gesture.end is not None:
        if gesture.start is None or gesture.end is None:
            return ()
        return compile_propagation(
            gesture.start,
            gesture.end,
            strength=gesture.strength,
            profile=profile,
            graph=graph,
        )
    return compile_direction_propagation(
        gesture.direction,
        strength=gesture.strength,
        profile=profile,
        graph=graph,
    )
