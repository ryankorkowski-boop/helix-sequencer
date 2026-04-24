from __future__ import annotations

from pathlib import Path

from helix_knowledge.models import TechniqueCard
from helix_knowledge.source_policy import evaluate_source_policy


def import_user_notes(path: Path, *, confirmed_by_user: bool = True) -> list[TechniqueCard]:
    text = path.read_text(encoding="utf-8")
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    cards: list[TechniqueCard] = []
    source_type = "USER_AUTHORED_NOTES" if confirmed_by_user else "USER_SUPPLIED_FILES_WITH_CONFIRMATION"
    decision = evaluate_source_policy(source_type, provenance_note=f"Imported from {path.name}")
    if not decision.allowed:
        raise ValueError(decision.reason)
    for idx, paragraph in enumerate(paragraphs, start=1):
        lines = [line.strip("- ").strip() for line in paragraph.splitlines() if line.strip()]
        title = lines[0][:72] if lines else f"User Note {idx}"
        cards.append(
            TechniqueCard(
                id=f"user_note_{idx:03d}",
                title=title,
                category="user_note",
                xlights_area="general",
                problem=paragraph[:160],
                strategy=paragraph[:240],
                step_by_step=lines[:6],
                applicable_prop_types=[],
                musical_use_case="user supplied",
                layout_requirements=[],
                render_style_notes="Imported from user-authored note block.",
                common_mistakes=[],
                helix_automation_idea="Convert user-authored heuristics into inspectable technique cards.",
                risk_warning="Requires human review before large-scale reuse.",
                confidence=0.66,
                source_type=source_type,
                provenance_note=f"Imported from {path}",
                permission_status="confirmed_by_user" if confirmed_by_user else "pending_confirmation",
                human_review_status="pending",
                tags=["user_notes"],
            )
        )
    return cards
