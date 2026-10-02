from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DrumEvent


@dataclass(frozen=True)
class DrummerMotionConfig:
    anticipation_ms: int = 70
    strike_ms: int = 36
    rebound_ms: int = 130
    humanize_min_ms: int = 10
    humanize_max_ms: int = 30
    seed: int = 414
    velocity_jitter: float = 0.08


def assign_hand(event: DrumEvent, previous_hand: str | None = None) -> str:
    if event.drum_type == "kick":
        return "foot"
    if event.drum_type == "snare":
        return "left"
    if event.drum_type in {"hihat", "cymbal"}:
        return "left" if previous_hand == "right" and event.drum_type == "hihat" else "right"
    if event.drum_type == "tom":
        return "both"
    return "both"


def _visual_offset(rng: random.Random, event: DrumEvent, config: DrummerMotionConfig) -> int:
    if event.drum_type == "kick":
        return 0
    magnitude = rng.randint(config.humanize_min_ms, config.humanize_max_ms)
    if event.drum_type in {"tom", "cymbal"}:
        magnitude = int(round(magnitude * 0.6))
    return (-1 if rng.random() < 0.5 else 1) * magnitude


def build_drummer_motion(events: Iterable[DrumEvent], config: DrummerMotionConfig = DrummerMotionConfig()) -> list[dict[str, object]]:
    rng = random.Random(config.seed)
    motions: list[dict[str, object]] = []
    previous_hand: str | None = None
    for event in sorted(events, key=lambda item: item.timestamp_ms):
        hand = assign_hand(event, previous_hand)
        if hand in {"left", "right"}:
            previous_hand = hand

        visual_offset = _visual_offset(rng, event, config)
        musical_strike = max(0, event.timestamp_ms)
        anticipation = max(0, min(musical_strike, musical_strike - config.anticipation_ms + visual_offset))
        end = musical_strike + config.strike_ms + config.rebound_ms
        visual_velocity = max(0.0, min(1.0, event.velocity * (1.0 + rng.uniform(-config.velocity_jitter, config.velocity_jitter))))
        motions.append(
            {
                "drum_type": event.drum_type,
                "hand": hand,
                "start_ms": anticipation,
                "anticipation_ms": anticipation,
                "musical_strike_ms": musical_strike,
                "strike_ms": musical_strike,
                "rebound_end_ms": end,
                "velocity": round(visual_velocity, 3),
                "submodels": (["left_stick", "right_stick"] if hand == "both" else [] if hand == "foot" else [f"{hand}_stick"]),
                "visual_humanized_offset_ms": visual_offset,
                "musical_event_locked": True,
            }
        )
    return motions
