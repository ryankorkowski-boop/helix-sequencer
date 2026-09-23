from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DrumEvent


@dataclass(frozen=True)
class PerformanceHit:
    time_ms: int
    end_ms: int
    drum_type: str
    velocity: float
    hand: str | None
    target: str
    accent: bool


@dataclass(frozen=True)
class StickPose:
    x: float
    y: float
    angle: float


TARGETS = {
    "snare": (0.43, 0.58),
    "hihat": (0.21, 0.46),
    "tom_left": (0.38, 0.51),
    "tom_right": (0.61, 0.51),
    "crash_left": (0.20, 0.30),
    "crash_right": (0.80, 0.30),
}

IDLE_LEFT = (0.27, 0.50)
IDLE_RIGHT = (0.73, 0.50)


def build_performance(events: Iterable[DrumEvent]) -> list[PerformanceHit]:
    ordered = sorted(events, key=lambda e: (e.timestamp_ms, e.drum_type))
    left_next = True
    out: list[PerformanceHit] = []
    tom_next_left = True
    for event in ordered:
        t = event.timestamp_ms
        v = max(0.08, min(1.0, float(event.velocity)))
        if event.drum_type == "kick":
            target, hand = "kick", None
            duration = 150
        elif event.drum_type == "snare":
            target, hand = "snare", "L" if left_next else "R"
            left_next = not left_next
            duration = 130
        elif event.drum_type == "hihat":
            target, hand = "hihat", "L"
            duration = 85
        elif event.drum_type == "tom":
            target = "tom_left" if tom_next_left else "tom_right"
            hand = "L" if tom_next_left else "R"
            tom_next_left = not tom_next_left
            duration = 160
        elif event.drum_type == "cymbal":
            hand = "L" if left_next else "R"
            target = "crash_left" if hand == "L" else "crash_right"
            left_next = not left_next
            duration = 300
        else:
            target, hand, duration = "snare", "R", 120
        out.append(PerformanceHit(t, t + duration, event.drum_type, v, hand, target, v >= 0.88))
    return out


def _ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def stick_pose(hit: PerformanceHit, now_ms: int, side: str) -> StickPose:
    idle = IDLE_LEFT if side == "L" else IDLE_RIGHT
    if hit.hand != side or now_ms < hit.time_ms - 70 or now_ms >= hit.end_ms:
        return StickPose(*idle, 0.0 if side == "L" else 180.0)
    target = TARGETS.get(hit.target)
    if target is None:
        return StickPose(*idle, 0.0 if side == "L" else 180.0)
    attack = max(1, hit.time_ms - (hit.time_ms - 65))
    release = max(1, hit.end_ms - hit.time_ms)
    if now_ms < hit.time_ms:
        p = _ease((now_ms - (hit.time_ms - 65)) / attack)
        p *= 0.88 + 0.12 * hit.velocity
    else:
        p = 1.0 - _ease((now_ms - hit.time_ms) / release)
    x = idle[0] + (target[0] - idle[0]) * p
    y = idle[1] + (target[1] - idle[1]) * p
    dx = target[0] - idle[0]
    dy = target[1] - idle[1]
    angle = __import__("math").degrees(__import__("math").atan2(dy, dx))
    return StickPose(x, y, angle)


def active_hits(performance: Iterable[PerformanceHit], now_ms: int) -> list[PerformanceHit]:
    return [hit for hit in performance if hit.time_ms - 70 <= now_ms < hit.end_ms]


__all__ = ["PerformanceHit", "StickPose", "build_performance", "stick_pose", "active_hits"]
