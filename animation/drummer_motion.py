from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import drummer_component_for_event, tom_class_for_event


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
    """Readable limb assignment for a single strike.

    This is performance metadata only. Physical illumination still routes
    through the canonical drummer components, never independent stick channels.
    """
    if event.drum_type == "kick":
        return "foot"
    if event.drum_type == "snare":
        return "left"
    if event.drum_type in {"hihat", "ride"}:
        return "left" if previous_hand == "right" else "right"
    if event.drum_type == "cymbal":
        return "right"
    return "both"


def build_drummer_motion(events: Iterable[DrumEvent], config: DrummerMotionConfig = DrummerMotionConfig()) -> list[dict[str, object]]:
    """Create visual hit timing and deterministic hand assignment.

    Preserve physical routing. Alternate snare hands on every strike and
    align crash hands with the actual alternating physical crash target.
    No independent stick channels are created.
    """
    rng = random.Random(config.seed)
    motions: list[dict[str, object]] = []
    tom_index = 0
    cymbal_index = 0
    snare_index = 0
    previous_limb: str | None = None
    for event in sorted(events, key=lambda item: item.timestamp_ms):
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

        hand: str | None = None
        if event.drum_type == "snare":
            hand = "L" if snare_index % 2 == 0 else "R"
            snare_index += 1
        elif event.drum_type == "cymbal":
            hand = "L" if component.endswith("_LEFT") else "R"
        # ``limb`` is the readable contract shared with assign_hand: alternating
        # stick hits report the hand actually used, the kick reports the foot,
        # and every other strike keeps the historical assignment.
        if hand is not None:
            limb = "left" if hand == "L" else "right"
        else:
            limb = assign_hand(event, previous_limb)
        previous_limb = limb

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
            "limb": limb,
            "start_ms": start,
            "anticipation_ms": strike - config.anticipation_ms,
            "strike_ms": strike,
            "rebound_end_ms": end,
            "velocity": round(max(0.0, min(1.0, event.velocity * (0.92 + rng.random() * 0.16))), 3),
            "submodels": [component],
            "humanized_offset_ms": humanize,
        })
    return motions
