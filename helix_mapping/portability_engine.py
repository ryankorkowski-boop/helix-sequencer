from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LayoutMappingPlan:
    song_analysis: dict[str, Any]
    visual_intents: list[dict[str, Any]]
    layout_mapping: dict[str, Any]
    render_style_plan: list[dict[str, Any]]
    effect_export_plan: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
