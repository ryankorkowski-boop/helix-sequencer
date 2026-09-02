"""Emit renderer-independent Wadena AC propagation cues as deterministic XSQ XML.

This module is deliberately narrow: electrical channel names must already have
been supplied by the caller. It never infers channels from geometry or labels.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence
from xml.etree.ElementTree import Element, SubElement, tostring

from core.wadena_ac_adapter import WadenaACChannelEvent, compile_wadena_ac_events
from core.wadena_temporal_renderer import ACSafeLandmarkEvent


@dataclass(frozen=True)
class WadenaXSQSequence:
    sequence_name: str
    xml_text: str


def _grid_ms(value: int, grid_ms: int) -> int:
    return max(0, round(value / grid_ms) * grid_ms)


def emit_wadena_xsq_sequence(
    *,
    events: Sequence[ACSafeLandmarkEvent],
    landmark_channels: Mapping[str, str],
    sequence_name: str = "WadenaPropagationProof",
    model_name: str = "WADENA_AC",
    grid_ms: int = 50,
) -> WadenaXSQSequence:
    """Emit explicit AC cues on the repository's validator-compatible skeleton.

    ``grid_ms`` defaults to the 50 ms LOR/xLights timing grid used by the
    professional reference. Values are rounded deterministically to that grid.
    No RGB/pixel representation is introduced.
    """
    if grid_ms <= 0:
        raise ValueError("grid_ms must be positive")

    channel_events = compile_wadena_ac_events(tuple(events), landmark_channels)
    root = Element("xsequence", {"name": sequence_name, "model": model_name})
    timing_track = SubElement(root, "timingtrack", {"name": "WadenaPropagation"})
    effects = SubElement(root, "effects")
    element_effects = SubElement(root, "ElementEffects")

    for idx, event in enumerate(channel_events):
        start_ms = _grid_ms(event.start_ms, grid_ms)
        end_ms = max(start_ms + grid_ms, _grid_ms(event.end_ms, grid_ms))
        start = f"{start_ms / 1000.0:.6f}"
        duration = f"{(end_ms - start_ms) / 1000.0:.6f}"
        value = f"{event.value:.4f}"

        SubElement(timing_track, "cue", {
            "index": str(idx),
            "channel": event.channel_name,
            "start": start,
            "duration": duration,
            "landmark": event.landmark,
            "effect": event.effect,
        })
        SubElement(effects, "effect", {
            "index": str(idx),
            "type": event.effect,
            "channel": event.channel_name,
            "start": start,
            "duration": duration,
            "value": value,
        })
        SubElement(element_effects, "Element", {
            "name": event.channel_name,
            "effectIndex": str(idx),
            "type": event.effect,
            "start": start,
            "duration": duration,
            "intensity": value,
        })

    return WadenaXSQSequence(
        sequence_name=sequence_name,
        xml_text=tostring(root, encoding="utf-8").decode("utf-8"),
    )
