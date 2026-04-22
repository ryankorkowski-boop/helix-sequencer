from __future__ import annotations

import unittest

from helix_knowledge.parsing.instruction_extractor import extract_task_drafts
from helix_knowledge.parsing.task_classifier import classify_task_text
from helix_knowledge.storage.models import TaskCard


class ExtractionTests(unittest.TestCase):
    def test_instruction_extractor_builds_task_draft(self) -> None:
        text = (
            "To do model groups cleanly, click Model Groups and create one for arches. "
            "Then drag the effect onto the model group. "
            "Common mistake: forgetting to include all arch props."
        )
        drafts = extract_task_drafts(text)
        self.assertTrue(drafts)
        draft = drafts[0]
        self.assertGreaterEqual(len(draft.step_by_step_solution), 2)
        self.assertTrue(draft.common_mistakes)

    def test_task_classifier_assigns_group_relevance(self) -> None:
        classification = classify_task_text("Use model groups when applying effects to arches")
        self.assertEqual(classification.task_category, "model_groups")
        self.assertIn("group-level", classification.helix_relevance)

    def test_task_card_generation_fields(self) -> None:
        classification = classify_task_text("Beat marks should be slightly before the audible beat")
        card = TaskCard(
            task_name="Beat lead compensation",
            task_category=classification.task_category,
            problem_statement="Beat alignment drifts behind visual output.",
            step_by_step_solution=["Open timing track", "Shift marks slightly earlier"],
            xlights_area=classification.xlights_area,
            applicable_models=classification.applicable_models,
            applicable_effects=classification.applicable_effects,
            prerequisites=["Timing track exists"],
            common_mistakes=["Shifting too far"],
            troubleshooting_notes=["Check render latency"],
            helix_relevance=classification.helix_relevance,
            source_ids=["src_123"],
            confidence_score=0.9,
            needs_human_review=False,
        )
        self.assertEqual(card.task_category, "beat_sync")
        self.assertIn("lead/lag compensation", card.helix_relevance)


if __name__ == "__main__":
    unittest.main()
