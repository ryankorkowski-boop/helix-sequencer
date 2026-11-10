"""Renderer bridge for Wadena temporal spatial intent.

Turns renderer-independent propagation samples into frame-level landmark
intensities and simple AC-safe effect events.  This module deliberately keeps
physical channel addressing out of the propagation layer: downstream adapters
can map landmark names to the existing LOR/xLights model/channel definitions.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.wadena_spatial_intent import SpatialGesture, compile_temporal_gesture
from core.wadena_spatial_propagation import (
    PropagationProfile,
    PropagationSample,
    sample_weight_at,
)


@dataclass(frozen=True)
class LandmarkFrame:
    """Intensity of one named landmark at a renderer time."""

    landmark: str
    time_s: float
    intensity: float
    order: int


@dataclass(frozen=True)
class ACSafeLandmarkEvent:
    """A channel-independent event restricted to AC-safe semantics."""

    landmark: str
    start_s: float
    end_s: float
    intensity: float
    effect: str = "Level"
    order: int = 0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def render_samples_at(
    samples: tuple[PropagationSample, ...],
    time_s: float,
    profile: PropagationProfile | None = None,
    *,
    threshold: float = 0.001,
) -> tuple[LandmarkFrame, ...]:
    """Sample a travelling gesture into one deterministic preview frame."""
    t = max(0.0, float(time_s))
    floor = max(0.0, float(threshold))
    rendered: list[LandmarkFrame] = []
    for sample in samples:
        intensity = _clamp(sample_weight_at(sample, t, profile))
        if intensity < floor:
            continue
        rendered.append(
            LandmarkFrame(
                landmark=sample.landmark,
                time_s=round(t, 6),
                intensity=round(intensity, 6),
                order=sample.order,
            )
        )
    return tuple(rendered)


def render_gesture_at(
    gesture: SpatialGesture,
    time_s: float,
    profile: PropagationProfile | None = None,
    *,
    threshold: float = 0.001,
) -> tuple[LandmarkFrame, ...]:
    """Compile and sample a spatial gesture in one call for preview use."""
    samples = compile_temporal_gesture(gesture, profile=profile)
    return render_samples_at(samples, time_s, profile, threshold=threshold)


def compile_ac_safe_events(
    samples: tuple[PropagationSample, ...],
    *,
    effect: str = "Level",
) -> tuple[ACSafeLandmarkEvent, ...]:
    """Translate propagation samples into channel-independent AC-safe events.

    Only the conservative effects already used by Helix's dumb-light path are
    accepted here.  Unsupported effect names fail safe to ``Level`` rather
    than introducing pixel-only semantics.
    """
    allowed = {"On", "Level", "Ramp", "Shimmer"}
    safe_effect = effect if effect in allowed else "Level"
    return tuple(
        ACSafeLandmarkEvent(
            landmark=sample.landmark,
            start_s=max(0.0, sample.arrival_s),
            end_s=max(sample.arrival_s, sample.release_s),
            intensity=round(_clamp(sample.weight), 6),
            effect=safe_effect,
            order=sample.order,
        )
        for sample in samples
        if sample.weight > 0.0
    )


def render_timeline(
    gesture: SpatialGesture,
    duration_s: float,
    *,
    fps: float = 20.0,
    profile: PropagationProfile | None = None,
    threshold: float = 0.001,
) -> tuple[tuple[LandmarkFrame, ...], ...]:
    """Render a complete deterministic frame timeline for preview/export."""
    duration = max(0.0, float(duration_s))
    rate = max(1.0, float(fps))
    samples = compile_temporal_gesture(gesture, profile=profile)
    frame_count = int(duration * rate) + 1
    return tuple(
        render_samples_at(
            samples,
            min(duration, index / rate),
            profile,
            threshold=threshold,
        )
        for index in range(frame_count)
    )
