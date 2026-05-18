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
    seed: int = 414


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


def build_drummer_motion(events: Iterable[DrumEvent], config: DrummerMotionConfig = DrummerMotionConfig()) -> list[dict[str, object]]:
    rng = random.Random(config.seed)
    motions: list[dict[str, object]] = []
    previous_hand: str | None = None
    for event in sorted(events, key=lambda item: item.timestamp_ms):
        hand = assign_hand(event, previous_hand)
        if hand in {"left", "right"}:
            previous_hand = hand
        strike = max(0, event.timestamp_ms)
        start = max(0, strike - config.anticipation_ms)
        end = strike + config.strike_ms + config.rebound_ms
        motions.append(
            {
                "drum_type": event.drum_type,
                "hand": hand,
                "start_ms": start,
                "anticipation_ms": strike - config.anticipation_ms,
                "strike_ms": strike,
                "rebound_end_ms": end,
                "velocity": round(max(0.0, min(1.0, event.velocity * (0.92 + rng.random() * 0.16))), 3),
                "submodels": ["left_stick" if hand == "left" else "right_stick" if hand == "right" else "left_stick", "right_stick"] if hand == "both" else ([] if hand == "foot" else [f"{hand}_stick"]),
            }
        )
    return motions
