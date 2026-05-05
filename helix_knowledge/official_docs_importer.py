from __future__ import annotations

from pathlib import Path

from helix_knowledge.models import TechniqueCard
from helix_knowledge.source_policy import evaluate_source_policy


def import_official_docs(path: Path) -> list[TechniqueCard]:
    decision = evaluate_source_policy("OFFICIAL_XLIGHTS_DOCS", provenance_note=f"Official doc import from {path}")
    if not decision.allowed:
        raise ValueError(decision.reason)
    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    return [
        TechniqueCard(
            id=f"official_{path.stem}",
            title=lines[0][:72],
            category="official_docs",
            xlights_area="documentation",
            problem=text[:160],
            strategy=text[:240],
            step_by_step=lines[:6],
            applicable_prop_types=[],
            musical_use_case="documentation reference",
            layout_requirements=[],
            render_style_notes="Summarized from official xLights documentation.",
            common_mistakes=[],
            helix_automation_idea="Use official guidance as generalized technique cards, not copied placements.",
            risk_warning="Summaries should stay high level and provenance-tagged.",
            confidence=0.72,
            source_type="OFFICIAL_XLIGHTS_DOCS",
            provenance_note=f"Summarized from {path}",
            permission_status="official_docs",
            human_review_status="pending",
            tags=["official_docs"],
        )
    ]
