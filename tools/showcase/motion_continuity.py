from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

DIRECTION_ORDER = {"none": 0, "center": 0, "left_to_right": 1, "right_to_left": -1, "bottom_to_top": 2, "top_to_bottom": -2, "inside_out": 3, "outside_in": -3, "radial": 3, "random": 99}
COMPATIBLE_MOTION_FAMILIES = {("sweep", "chase"), ("chase", "sweep"), ("chase", "spiral"), ("spiral", "chase"), ("pulse", "burst"), ("burst", "pulse"), ("wash", "shimmer"), ("shimmer", "wash"), ("spiral", "sweep"), ("sweep", "spiral")}


@dataclass(frozen=True)
class MotionTrace:
    name: str
    section: str = ""
    section_kind: str = "unknown"
    start: float = 0.0
    end: float = 0.0
    motion_family: str = "unknown"
    direction: str = "none"
    intensity: float = 0.5
    speed: float = 0.5
    breadth: float = 0.5
    transition: str = "cut"

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "section": self.section, "section_kind": self.section_kind, "start": self.start, "end": self.end, "motion_family": self.motion_family, "direction": self.direction, "intensity": self.intensity, "speed": self.speed, "breadth": self.breadth, "transition": self.transition}


@dataclass(frozen=True)
class MotionContinuityFinding:
    code: str
    severity: str
    message: str
    motion: str | None = None
    penalty: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "severity": self.severity, "message": self.message, "motion": self.motion, "penalty": self.penalty}


@dataclass(frozen=True)
class MotionContinuityReport:
    motion_count: int
    direction_coherence_score: float
    family_continuity_score: float
    transition_smoothness_score: float
    hard_cut_penalty: float
    showcase_motion_score: float
    raw_metrics: dict[str, float] = field(default_factory=dict)
    findings: tuple[MotionContinuityFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {"motion_count": self.motion_count, "direction_coherence_score": self.direction_coherence_score, "family_continuity_score": self.family_continuity_score, "transition_smoothness_score": self.transition_smoothness_score, "hard_cut_penalty": self.hard_cut_penalty, "showcase_motion_score": self.showcase_motion_score, "raw_metrics": self.raw_metrics, "findings": [finding.as_dict() for finding in self.findings]}


def score_motion_continuity(raw_motions: Iterable[Mapping[str, object] | MotionTrace]) -> MotionContinuityReport:
    motions = normalize_motion_traces(raw_motions)
    findings: list[MotionContinuityFinding] = []
    if not motions:
        finding = MotionContinuityFinding("no_motion_traces", "warning", "No motion traces were provided, so motion continuity cannot be measured.", penalty=1.0)
        return MotionContinuityReport(0, 0.0, 0.0, 0.0, 1.0, 0.0, findings=(finding,))
    direction_coherence_score = _score_direction_coherence(motions, findings)
    family_continuity_score = _score_family_continuity(motions, findings)
    transition_smoothness_score = _score_transition_smoothness(motions, findings)
    hard_cut_penalty = _score_hard_cut_penalty(motions, findings)
    showcase_motion_score = round(max(0.0, (0.3 * direction_coherence_score) + (0.25 * family_continuity_score) + (0.25 * transition_smoothness_score) + (0.2 * (1.0 - hard_cut_penalty))), 4)
    return MotionContinuityReport(len(motions), direction_coherence_score, family_continuity_score, transition_smoothness_score, hard_cut_penalty, showcase_motion_score, {"mean_intensity": round(_mean(motion.intensity for motion in motions), 4), "mean_speed": round(_mean(motion.speed for motion in motions), 4), "mean_breadth": round(_mean(motion.breadth for motion in motions), 4), "unique_motion_families": float(len({motion.motion_family for motion in motions})), "unique_directions": float(len({motion.direction for motion in motions}))}, tuple(findings))


def normalize_motion_trace(raw: Mapping[str, object] | MotionTrace) -> MotionTrace:
    if isinstance(raw, MotionTrace):
        return raw
    return MotionTrace(name=str(raw.get("name", raw.get("motion_id", "unnamed_motion"))), section=str(raw.get("section", "")), section_kind=_normalize_token(str(raw.get("section_kind", raw.get("kind", "unknown")))), start=float(raw.get("start", raw.get("time", 0.0))), end=float(raw.get("end", raw.get("time", 0.0))), motion_family=_normalize_token(str(raw.get("motion_family", raw.get("family", raw.get("effect_family", "unknown"))))), direction=_normalize_direction(str(raw.get("direction", "none"))), intensity=_clamp01(float(raw.get("intensity", 0.5))), speed=_clamp01(float(raw.get("speed", raw.get("motion_speed", 0.5)))), breadth=_clamp01(float(raw.get("breadth", raw.get("prop_breadth", 0.5)))), transition=_normalize_token(str(raw.get("transition", raw.get("transition_type", "cut")))))


def normalize_motion_traces(raw_motions: Iterable[Mapping[str, object] | MotionTrace]) -> list[MotionTrace]:
    return sorted((normalize_motion_trace(motion) for motion in raw_motions), key=lambda motion: motion.start)


def _score_direction_coherence(motions: list[MotionTrace], findings: list[MotionContinuityFinding]) -> float:
    if len(motions) < 2:
        return 0.8
    compatible = 0
    total = 0
    abrupt_flips = 0
    for left, right in zip(motions, motions[1:]):
        total += 1
        left_value = DIRECTION_ORDER.get(left.direction, 99)
        right_value = DIRECTION_ORDER.get(right.direction, 99)
        if left.direction == right.direction:
            compatible += 1
        elif "random" in {left.direction, right.direction}:
            pass
        elif left_value == -right_value and left_value != 0:
            abrupt_flips += 1
            findings.append(MotionContinuityFinding("abrupt_direction_flip", "warning", f"Motion '{right.name}' reverses direction sharply from the previous motion.", right.name, 0.08))
        elif abs(left_value - right_value) <= 2:
            compatible += 1
    score = compatible / total if total else 1.0
    return round(max(0.0, score - (0.08 * abrupt_flips)), 4)


def _score_family_continuity(motions: list[MotionTrace], findings: list[MotionContinuityFinding]) -> float:
    if len(motions) < 2:
        return 0.8
    compatible = 0
    total = 0
    unrelated_jumps = 0
    for left, right in zip(motions, motions[1:]):
        total += 1
        if left.motion_family == right.motion_family or (left.motion_family, right.motion_family) in COMPATIBLE_MOTION_FAMILIES:
            compatible += 1
        else:
            unrelated_jumps += 1
            if left.intensity >= 0.65 and right.intensity >= 0.65:
                findings.append(MotionContinuityFinding("unrelated_high_energy_motion_jump", "info", f"High-energy motion '{right.name}' changes to an unrelated motion family.", right.name, 0.05))
    score = compatible / total if total else 1.0
    return round(max(0.0, score - (0.04 * unrelated_jumps)), 4)


def _score_transition_smoothness(motions: list[MotionTrace], findings: list[MotionContinuityFinding]) -> float:
    weights = {"blend": 1.0, "crossfade": 1.0, "wipe": 0.85, "morph": 1.0, "echo": 0.75, "cut": 0.45, "hard_cut": 0.2, "blackout_cut": 0.65}
    scores = []
    for motion in motions:
        scores.append(weights.get(motion.transition, 0.55))
        if motion.transition in {"hard_cut", "cut"} and motion.intensity >= 0.75:
            findings.append(MotionContinuityFinding("high_energy_hard_transition", "info", f"High-energy motion '{motion.name}' uses a hard transition.", motion.name, 0.05))
    return round(_mean(scores), 4)


def _score_hard_cut_penalty(motions: list[MotionTrace], findings: list[MotionContinuityFinding]) -> float:
    risky = []
    for left, right in zip(motions, motions[1:]):
        gap = right.start - left.end
        if right.transition in {"cut", "hard_cut"} and gap <= 0.1 and abs(right.intensity - left.intensity) >= 0.35 and abs(right.speed - left.speed) >= 0.25:
            risky.append(right)
            findings.append(MotionContinuityFinding("hard_cut_risk", "warning", f"Motion '{right.name}' hard-cuts after a large intensity/speed change.", right.name, 0.1))
    return round(min(1.0, len(risky) / max(1, len(motions) - 1)), 4)


def _normalize_token(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())


def _normalize_direction(value: str) -> str:
    aliases = {"ltr": "left_to_right", "left_right": "left_to_right", "rtl": "right_to_left", "right_left": "right_to_left", "up": "bottom_to_top", "down": "top_to_bottom", "in_out": "inside_out", "out_in": "outside_in"}
    token = _normalize_token(value)
    return aliases.get(token, token or "none")


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
