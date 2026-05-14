from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class ContrastDecision:
    start_ms: int
    end_ms: int
    section_label: str
    density: str
    brightness: str
    motion: str
    temperature: str
    contrast_score: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ContrastPlan:
    decisions: tuple[ContrastDecision, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "helix.contrast_engine.v1",
            "decision_count": len(self.decisions),
            "decisions": [decision.to_dict() for decision in self.decisions],
        }


def _label(section: Any) -> str:
    return str(getattr(section, "label", "") or "").lower()


def _energy(section: Any, energy_curve: Any | None = None) -> float:
    if energy_curve is not None:
        try:
            return _clamp01(float(energy_curve.energy_between(int(getattr(section, "start_ms", 0)), int(getattr(section, "end_ms", 0)))))
        except Exception:
            pass
    try:
        return _clamp01(float(getattr(section, "energy", 0.5)))
    except Exception:
        return 0.5


def _density_for(label: str, energy: float, previous_density: str) -> str:
    if label in {"breakdown", "intro", "outro"} or energy < 0.34:
        return "sparse"
    if label in {"drop", "chorus"} and energy >= 0.62:
        return "dense" if previous_density != "dense" else "medium"
    if label in {"buildup", "pre-chorus"}:
        return "medium"
    return "medium" if previous_density == "sparse" else "sparse"


def _brightness_for(label: str, energy: float, density: str) -> str:
    if label == "breakdown":
        return "dark"
    if label in {"drop", "chorus"} and energy >= 0.66:
        return "bright"
    if density == "dense" and energy < 0.72:
        return "balanced"
    return "dark" if energy < 0.42 else "balanced"


def _motion_for(label: str, energy: float, density: str) -> str:
    if label in {"buildup", "drop"}:
        return "active"
    if density == "dense" and energy >= 0.72:
        return "active"
    if density == "sparse":
        return "still"
    return "gentle"


def _temperature_for(index: int, label: str, previous: str) -> str:
    if label in {"drop", "chorus"}:
        return "warm" if previous != "warm" else "cool"
    if label in {"breakdown", "bridge"}:
        return "cool"
    return "warm" if index % 2 == 0 else "cool"


def build_contrast_plan(sections: Sequence[Any], energy_curve: Any | None = None) -> ContrastPlan:
    decisions: list[ContrastDecision] = []
    previous_density = "medium"
    previous_temperature = "cool"
    for idx, section in enumerate(sections):
        label = _label(section)
        energy = _energy(section, energy_curve)
        density = _density_for(label, energy, previous_density)
        brightness = _brightness_for(label, energy, density)
        motion = _motion_for(label, energy, density)
        temperature = _temperature_for(idx, label, previous_temperature)
        contrast_terms = [
            density != previous_density,
            temperature != previous_temperature,
            (brightness == "bright") != (previous_density == "dense"),
            motion in {"still", "active"},
        ]
        score = 0.35 + (0.13 * sum(1 for item in contrast_terms if item))
        decisions.append(
            ContrastDecision(
                start_ms=int(getattr(section, "start_ms", 0) or 0),
                end_ms=max(int(getattr(section, "start_ms", 0) or 0) + 1, int(getattr(section, "end_ms", 1) or 1)),
                section_label=label or "section",
                density=density,
                brightness=brightness,
                motion=motion,
                temperature=temperature,
                contrast_score=round(_clamp01(score), 4),
            )
        )
        previous_density = density
        previous_temperature = temperature
    return ContrastPlan(decisions=tuple(decisions))
