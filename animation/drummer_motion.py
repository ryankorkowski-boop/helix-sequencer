from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DrumEvent


DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_V3_STICK_SUBMODELS = {
    "left": "HX_SNOWMAN_DRUMMER_V3_LEFT_STICK_SNARE",
    "right": "HX_SNOWMAN_DRUMMER_V3_RIGHT_STICK_SNARE",
    "hihat": "HX_SNOWMAN_DRUMMER_V3_LEFT_STICK_HIHAT",
    "left_tom": "HX_SNOWMAN_DRUMMER_V3_LEFT_STICK_TOM",
    "right_tom": "HX_SNOWMAN_DRUMMER_V3_RIGHT_STICK_TOM",
    "left_crash": "HX_SNOWMAN_DRUMMER_V3_LEFT_STICK_CRASH",
    "right_crash": "HX_SNOWMAN_DRUMMER_V3_RIGHT_STICK_CRASH",
    "idle_left": "HX_SNOWMAN_DRUMMER_V3_LEFT_STICK_IDLE",
    "idle_right": "HX_SNOWMAN_DRUMMER_V3_RIGHT_STICK_IDLE",
}


@dataclass(frozen=True)
class DrummerMotionConfig:
    anticipation_ms: int = 70
    strike_ms: int = 36
    rebound_ms: int = 130
    humanize_min_ms: int = 10
    humanize_max_ms: int = 30
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


def _v3_stick_targets(event: DrumEvent, hand: str, event_index: int) -> list[str]:
    if event.drum_type == "kick":
        return []
    if event.drum_type == "snare":
        return [DRUMMER_V3_STICK_SUBMODELS["left"]]
    if event.drum_type == "hihat":
        return [DRUMMER_V3_STICK_SUBMODELS["hihat"]]
    if event.drum_type == "tom":
        return [DRUMMER_V3_STICK_SUBMODELS["left_tom" if event_index % 2 == 0 else "right_tom"]]
    if event.drum_type == "cymbal":
        return [DRUMMER_V3_STICK_SUBMODELS["left_crash" if event_index % 2 else "right_crash"]]
    if hand == "left":
        return [DRUMMER_V3_STICK_SUBMODELS["left"]]
    if hand == "right":
        return [DRUMMER_V3_STICK_SUBMODELS["right"]]
    return [DRUMMER_V3_STICK_SUBMODELS["left"], DRUMMER_V3_STICK_SUBMODELS["right"]]


def build_drummer_motion(events: Iterable[DrumEvent], config: DrummerMotionConfig = DrummerMotionConfig()) -> list[dict[str, object]]:
    rng = random.Random(config.seed)
    motions: list[dict[str, object]] = []
    previous_hand: str | None = None
    for event_index, event in enumerate(sorted(events, key=lambda item: item.timestamp_ms)):
        hand = assign_hand(event, previous_hand)
        if hand in {"left", "right"}:
            previous_hand = hand
        sign = -1 if rng.random() < 0.5 else 1
        humanize = sign * rng.randint(config.humanize_min_ms, config.humanize_max_ms)
        strike = max(0, event.timestamp_ms + humanize)
        start = max(0, strike - config.anticipation_ms)
        end = strike + config.strike_ms + config.rebound_ms
        legacy_submodels = (
            ["left_stick" if hand == "left" else "right_stick" if hand == "right" else "left_stick", "right_stick"]
            if hand == "both"
            else ([] if hand == "foot" else [f"{hand}_stick"])
        )
        motions.append(
            {
                "drum_type": event.drum_type,
                "hand": hand,
                "start_ms": start,
                "anticipation_ms": strike - config.anticipation_ms,
                "strike_ms": strike,
                "rebound_end_ms": end,
                "velocity": round(max(0.0, min(1.0, event.velocity * (0.92 + rng.random() * 0.16))), 3),
                # Keep legacy names for existing consumers.
                "submodels": legacy_submodels,
                # V3 is the canonical rendered motion target.
                "model": DRUMMER_V3_MODEL,
                "v3_submodels": _v3_stick_targets(event, hand, event_index),
                "humanized_offset_ms": humanize,
            }
        )
    return motions
