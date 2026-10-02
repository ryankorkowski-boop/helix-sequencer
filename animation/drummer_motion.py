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


def build_drummer_motion(events: Iterable[DrumEvent], config: DrummerMotionConfig = DrummerMotionConfig()) -> list[dict[str, object]]:
    """Create visual hit timing without inventing hand/stick sequencing channels.

    A motion event targets one canonical physical hit component. Contacting stick
    geometry is rendered by that component. Kick has no stick target; toms are
    explicitly High/Mid/Floor.
    """
    rng = random.Random(config.seed)
    motions: list[dict[str, object]] = []
    tom_index = 0
    cymbal_index = 0
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
        sign = -1 if rng.random() < 0.5 else 1
        humanize = sign * rng.randint(config.humanize_min_ms, config.humanize_max_ms)
        strike = max(0, event.timestamp_ms + humanize)
        start = max(0, strike - config.anticipation_ms)
        end = strike + config.strike_ms + config.rebound_ms
        motions.append({
            "drum_type": event.drum_type,
            "component": component,
            "tom_class": tom_class,
            "start_ms": start,
            "anticipation_ms": strike - config.anticipation_ms,
            "strike_ms": strike,
            "rebound_end_ms": end,
            "velocity": round(max(0.0, min(1.0, event.velocity * (0.92 + rng.random() * 0.16))), 3),
            "submodels": [component],
            "humanized_offset_ms": humanize,
        })
    return motions
