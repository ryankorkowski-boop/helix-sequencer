from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class VisualIntent:
    id: str
    start_time: float
    end_time: float
    intent_type: str
    musical_trigger: str
    spatial_behavior: str
    target_roles: list[str]
    density_level: str
    emotional_role: str
    color_strategy: str
    brightness_strategy: str
    curve_strategy: str
    render_style_hint: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PropEffectIntent:
    visual_intent_id: str
    target_prop: str
    target_role: str
    effect_family: str
    render_style: str
    curve_type: str
    brightness_cap: float
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderStylePlan:
    visual_intent_id: str
    render_style: str
    readability_score: float
    direction_preservation_score: float
    density_match_score: float
    render_cost_score: float
    layout_fit_score: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
