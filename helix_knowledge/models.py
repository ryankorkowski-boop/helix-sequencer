from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TechniqueCard:
    id: str
    title: str
    category: str
    xlights_area: str
    problem: str
    strategy: str
    step_by_step: list[str]
    applicable_prop_types: list[str]
    musical_use_case: str
    layout_requirements: list[str]
    render_style_notes: str
    common_mistakes: list[str]
    helix_automation_idea: str
    risk_warning: str
    confidence: float
    source_type: str
    provenance_note: str
    permission_status: str
    human_review_status: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
