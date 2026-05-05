from __future__ import annotations

from helix_knowledge.models import TechniqueCard


def default_technique_cards() -> list[TechniqueCard]:
    return [
        TechniqueCard(
            id="tc_center_out_chorus",
            title="Center-Out Chorus Bloom",
            category="coverage",
            xlights_area="groups",
            problem="Chorus sections need readable expansion without chaotic full-house clutter.",
            strategy="Use center anchors and outward ordering so coverage widens on the musical lift.",
            step_by_step=[
                "Classify center-capable props and hero surfaces.",
                "Choose a center or visual-center anchor.",
                "Apply a bloom or pulse field with outward propagation.",
                "Reserve full white for short accents only.",
            ],
            applicable_prop_types=["matrix", "mega_tree", "arch", "roofline", "whole_house_group"],
            musical_use_case="chorus lift, final chorus, triumphant release",
            layout_requirements=["center anchor", "ordered groups"],
            render_style_notes="Prefer per-preview or center-aware group order when motion direction matters.",
            common_mistakes=["lighting every prop equally", "using dense sparkle everywhere", "skipping cooldown after impact"],
            helix_automation_idea="Generate a center-out ordering and brightness budget from section energy.",
            risk_warning="Can become amateur-looking if used repeatedly without contrast.",
            confidence=0.84,
            source_type="HELIX_GENERATED_EXPERIMENTS",
            provenance_note="Generalized from Helix internal preview experiments.",
            permission_status="internal",
            human_review_status="approved",
            tags=["chorus", "center_out", "coverage"],
        )
    ]
