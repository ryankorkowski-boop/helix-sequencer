"""Translate Wadena landmark events into explicit AC channel cues.

The adapter requires a caller-supplied landmark-to-channel map.  This is an
intentional safety boundary: geometry or visual evidence must never silently
invent electrical channel assignments.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.wadena_temporal_renderer import ACSafeLandmarkEvent


@dataclass(frozen=True)
class WadenaACChannelEvent:
    """One AC-safe event bound to a known channel name."""

    channel_name: str
    start_ms: int
    end_ms: int
    value: float
    effect: str
    landmark: str
    order: int

    def to_cue(self) -> dict[str, object]:
        return {
            "channel_name": self.channel_name,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "value": self.value,
            "effect": self.effect,
            "landmark": self.landmark,
            "order": self.order,
            "kind": "wadena_spatial_propagation",
        }


def compile_wadena_ac_events(
    events: tuple[ACSafeLandmarkEvent, ...],
    landmark_channels: Mapping[str, str],
) -> tuple[WadenaACChannelEvent, ...]:
    """Bind only explicitly known landmarks to electrical channel names.

    Unknown landmarks are dropped rather than guessed.  Empty/blank channel
    names are also dropped.  The output remains limited to the effect already
    validated by ``ACSafeLandmarkEvent``.
    """
    compiled: list[WadenaACChannelEvent] = []
    for event in events:
        channel_name = str(landmark_channels.get(event.landmark, "") or "").strip()
        if not channel_name:
            continue
        compiled.append(
            WadenaACChannelEvent(
                channel_name=channel_name,
                start_ms=max(0, round(event.start_s * 1000)),
                end_ms=max(1, round(event.end_s * 1000)),
                value=max(0.0, min(1.0, float(event.intensity))),
                effect=event.effect,
                landmark=event.landmark,
                order=event.order,
            )
        )
    return tuple(sorted(compiled, key=lambda item: (item.start_ms, item.order, item.channel_name)))


def compile_wadena_ac_cues(
    events: tuple[ACSafeLandmarkEvent, ...],
    landmark_channels: Mapping[str, str],
) -> tuple[dict[str, object], ...]:
    """Return stable cue dictionaries suitable for an existing event compiler."""
    return tuple(event.to_cue() for event in compile_wadena_ac_events(events, landmark_channels))
