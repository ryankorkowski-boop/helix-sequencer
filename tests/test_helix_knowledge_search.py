from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from helix_knowledge.storage.models import TaskCard
from helix_knowledge.storage.sqlite_store import SQLiteKnowledgeStore


class SearchTests(unittest.TestCase):
    def test_search_returns_relevant_task_card(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = SQLiteKnowledgeStore(Path(temp_dir) / "knowledge.db")
            store.add_task_card(
                TaskCard(
                    task_name="Arch Direction Alternation",
                    task_category="effects_usage",
                    problem_statement="Make arches run both directions.",
                    step_by_step_solution=["Create two effect layers", "Reverse the second layer direction"],
                    xlights_area="effects",
                    applicable_models=["pixel_arch"],
                    applicable_effects=["chase", "wave"],
                    prerequisites=["Arch models configured"],
                    common_mistakes=["Applying same direction twice"],
                    troubleshooting_notes=["Check model orientation"],
                    helix_relevance="Helix should support reverse-direction arch sweeps.",
                    source_ids=["src_arch"],
                    confidence_score=0.88,
                    needs_human_review=False,
                )
            )
            store.add_task_card(
                TaskCard(
                    task_name="Controller Universe Setup",
                    task_category="controllers",
                    problem_statement="Assign universes to controllers.",
                    step_by_step_solution=["Open controller tab", "Set start channel"],
                    xlights_area="controllers",
                    applicable_models=[],
                    applicable_effects=[],
                    prerequisites=[],
                    common_mistakes=[],
                    troubleshooting_notes=[],
                    helix_relevance="Helix should validate protocol assumptions.",
                    source_ids=["src_ctrl"],
                    confidence_score=0.70,
                    needs_human_review=False,
                )
            )

            results = store.search_task_cards("arches both directions", limit=5)

        self.assertTrue(results)
        self.assertEqual(results[0].task_name, "Arch Direction Alternation")


if __name__ == "__main__":
    unittest.main()
