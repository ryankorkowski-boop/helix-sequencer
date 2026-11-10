from __future__ import annotations

from dataclasses import dataclass

from core.birdsong_feature_state import FeatureState, clamp01
from core.birdsong_phrase_engine import Phrase


Point3 = tuple[float, float, float]


@dataclass(frozen=True)
class MotionPulse:
    position: Point3
    step: Point3
    strength: float
    decay: float = 0.92

    def advance(self, seconds: float) -> "MotionPulse":
        if seconds < 0:
            raise ValueError("seconds must be >= 0")
        px, py, pz = self.position
        sx, sy, sz = self.step
        return MotionPulse(
            position=(round(px + sx * seconds, 6), round(py + sy * seconds, 6), round(pz + sz * seconds, 6)),
            step=self.step,
            strength=round(clamp01(self.strength * self.decay), 6),
            decay=self.decay,
        )

    @property
    def active(self) -> bool:
        return self.strength > 0.01


def direction_motion(direction: str) -> tuple[Point3, Point3]:
    if direction == "right_to_left":
        return (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)
    if direction == "center_out":
        return (0.0, 0.0, 0.0), (1.0, 0.2, 0.0)
    if direction == "bottom_up":
        return (0.0, -1.0, 0.0), (0.0, 1.0, 0.0)
    if direction == "top_down":
        return (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)
    return (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0)


def create_motion_pulse(state: FeatureState, phrase: Phrase) -> MotionPulse | None:
    strength = max(state.onset, state.energy_smooth)
    if state.onset < 0.5 and state.energy_smooth < 0.35:
        return None
    position, step = direction_motion(phrase.direction)
    return MotionPulse(position=position, step=step, strength=round(clamp01(strength), 6))


def advance_motion_pulses(pulses: tuple[MotionPulse, ...], seconds: float) -> tuple[MotionPulse, ...]:
    advanced = tuple(pulse.advance(seconds) for pulse in pulses)
    return tuple(pulse for pulse in advanced if pulse.active)
