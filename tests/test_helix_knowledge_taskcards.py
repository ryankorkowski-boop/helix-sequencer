from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from helix_knowledge.parsing.instruction_extractor import extract_task_drafts
from helix_knowledge.storage.models import KnowledgeChunk, KnowledgeSource, TaskCard
from helix_knowledge.storage.sqlite_store import SQLiteKnowledgeStore


class TaskCardGenerationTests(unittest.TestCase):
    def test_generates_task_card_from_chunk_text(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = SQLiteKnowledgeStore(Path(temp_dir) / "knowledge.db")
            source = KnowledgeSource(source_type="xlights_manual", title="Timing", url="https://manual.xlights.org/xlights/")
            store.upsert_source(source)
            chunk = KnowledgeChunk(source_id=source.id, cleaned_text="Select the timing track. Drag the effect. Common mistake: forgetting snap mode.")
            store.add_chunk(chunk)

            drafts = extract_task_drafts(chunk.cleaned_text)
            self.assertTrue(drafts)
            draft = drafts[0]
            classification = draft.classification
            self.assertIsNotNone(classification)

            task = TaskCard(
                task_name=draft.task_name,
                task_category=classification.task_category if classification else "best_practices",
                problem_statement=draft.problem_statement,
                step_by_step_solution=draft.step_by_step_solution,
                xlights_area=classification.xlights_area if classification else "general",
                applicable_models=classification.applicable_models if classification else [],
                applicable_effects=classification.applicable_effects if classification else [],
                prerequisites=[],
                common_mistakes=draft.common_mistakes,
                troubleshooting_notes=draft.troubleshooting_notes,
                helix_relevance=classification.helix_relevance if classification else "",
                source_ids=[source.id],
                confidence_score=draft.confidence,
                needs_human_review=bool(classification.needs_human_review) if classification else True,
            )
            store.add_task_card(task)

            cards = store.fetch_task_cards()
        self.assertEqual(len(cards), 1)
        self.assertIn("timing", cards[0].problem_statement.lower())


if __name__ == "__main__":
    unittest.main()
