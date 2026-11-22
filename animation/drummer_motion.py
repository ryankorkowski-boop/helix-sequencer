from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import drummer_component_for_event, tom_class_for_event, _explicit_tom_class


@dataclass(frozen=True)
class DrummerMotionConfig:
    anticipation_ms: int = 70
    strike_ms: int = 36
    rebound_ms: int = 130
    humanize_min_ms: int = 10
    humanize_max_ms: int = 30
    seed: int = 414
    rapid_alternation_threshold_ms: int = 180


def assign_hand(event: DrumEvent, previous_hand: str | None = None) -> str:
    """Preserve the historical drummer-motion hand contract.

    This is performance metadata only; physical illumination still routes through
    the canonical eight integrated components, never independent stick channels.
    """
    if event.drum_type == "kick":
        return "foot"
    if event.drum_type == "snare":
        return "left"
    if event.drum_type in {"hihat", "ride"}:
        return "left" if previous_hand == "right" else "right"
    if event.drum_type == "cymbal":
        return "right"
    if event.drum_type == "tom":
        return "both"
    return "both"


def build_drummer_motion(events: Iterable[DrumEvent], config: DrummerMotionConfig = DrummerMotionConfig()) -> list[dict[str, object]]:
    """Create visual hit timing and deterministic hand assignment.

    Physical routing remains the canonical nine-component drummer. Hand is a
    performance attribute used by contacting-stick composites: snare strikes
    alternate left/right hands and crashes alternate the left/right physical
    cymbals on every strike. No independent stick channels are created.
    """
    rng = random.Random(config.seed)
    motions: list[dict[str, object]] = []
    tom_index = 0
    cymbal_index = 0
    snare_index = 0
    previous_hand: str | None = None
    for event in sorted(events, key=lambda item: item.timestamp_ms):
        if event.drum_type == "drum_bus" or (event.drum_type == "tom" and _explicit_tom_class(event)[0] is None):
            continue
        if event.drum_type == "tom":
            component = drummer_component_for_event(event, event_index=tom_index)
            tom_class = tom_class_for_event(event, tom_index)
            tom_index += 1
        elif event.drum_type == "cymbal":
            component = drummer_component_for_event(event, event_index=cymbal_index)
            tom_class = None
            cymbal_index += 1
        else:
            component = drummer_component_for_event(event)
            tom_class = None

        # Staging contract: the snare alternates hands on every strike, slow or
        # fast, and each crash is struck by the hand on its own physical side.
        if event.drum_type == "snare":
            hand = "left" if snare_index % 2 == 0 else "right"
            snare_index += 1
        elif event.drum_type == "cymbal":
            hand = "left" if component.endswith("_LEFT") else "right"
        else:
            hand = assign_hand(event, previous_hand)
        previous_hand = hand

        sign = -1 if rng.random() < 0.5 else 1
        humanize = sign * rng.randint(config.humanize_min_ms, config.humanize_max_ms)
        strike = max(0, event.timestamp_ms + humanize)
        start = max(0, strike - config.anticipation_ms)
        end = strike + config.strike_ms + config.rebound_ms
        motions.append({
            "drum_type": event.drum_type,
            "component": component,
            "tom_class": tom_class,
            "hand": hand,
            "start_ms": start,
            "anticipation_ms": strike - config.anticipation_ms,
            "strike_ms": strike,
            "rebound_end_ms": end,
            "velocity": round(max(0.0, min(1.0, event.velocity * (0.92 + rng.random() * 0.16))), 3),
            "submodels": [component],
            "humanized_offset_ms": humanize,
        })
    return motions
