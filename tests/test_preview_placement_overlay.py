from __future__ import annotations

import unittest

from helix_preview.preview_generator import generate_preview_data
from helix_preview.preview_grader import grade_preview


class PreviewPlacementOverlayTests(unittest.TestCase):
    def test_generate_preview_data_includes_placement_overlay(self) -> None:
        intents = [
            {"id": "intent_001", "start_time": 0.0, "end_time": 4.0, "intent_type": "bloom"},
            {"id": "intent_002", "start_time": 4.0, "end_time": 8.0, "intent_type": "trail"},
        ]
        placement_plan = {
            "visual_intents": intents,
            "planner_report": {
                "placement_count": 2,
                "rejected_intents": [],
                "capped_density_intents": ["intent_002"],
            },
            "prop_effect_intents": [
                {
                    "visual_intent_id": "intent_001",
                    "target_prop": "Mega Tree",
                    "target_role": "hero",
                    "effect_family": "energy_wave",
                    "render_style": "per_preview",
                    "brightness_cap": 0.82,
                },
                {
                    "visual_intent_id": "intent_002",
                    "target_prop": "Front Roof",
                    "target_role": "structure",
                    "effect_family": "outline_pulse",
                    "render_style": "per_model",
                    "brightness_cap": 0.62,
                },
            ],
            "warnings": ["Density-capped intents: intent_002"],
        }

        preview = generate_preview_data(
            layout_name="fixture_layout",
            intents=intents,
            seconds=30,
            placement_plan=placement_plan,
        )

        self.assertTrue(preview["placement_overlay"])
        self.assertEqual(preview["placement_count"], 2)
        self.assertEqual(preview["placement_capped_intent_count"], 1)
        self.assertEqual(preview["placement_unique_target_count"], 2)
        self.assertEqual(preview["placement_effect_family_count"], 2)
        self.assertEqual(preview["placement_clips"][0]["target_prop"], "Mega Tree")
        self.assertEqual(preview["placement_clips"][0]["start_time"], 0.0)

    def test_grade_preview_uses_placement_overlay_metrics(self) -> None:
        baseline = generate_preview_data(
            layout_name="fixture_layout",
            intents=[{"id": "intent_001"}],
            seconds=30,
        )
        placed = generate_preview_data(
            layout_name="fixture_layout",
            intents=[{"id": "intent_001", "start_time": 0.0, "end_time": 4.0, "intent_type": "bloom"}],
            seconds=30,
            placement_plan={
                "visual_intents": [{"id": "intent_001", "start_time": 0.0, "end_time": 4.0, "intent_type": "bloom"}],
                "planner_report": {"placement_count": 3, "rejected_intents": [], "capped_density_intents": []},
                "prop_effect_intents": [
                    {"visual_intent_id": "intent_001", "target_prop": "Mega Tree", "effect_family": "energy_wave"},
                    {"visual_intent_id": "intent_001", "target_prop": "Front Roof", "effect_family": "outline_pulse"},
                    {"visual_intent_id": "intent_001", "target_prop": "Matrix", "effect_family": "matrix_pulse"},
                ],
            },
        )

        baseline_grade = grade_preview(baseline)
        placed_grade = grade_preview(placed)

        self.assertFalse(baseline_grade["placement_overlay"])
        self.assertTrue(placed_grade["placement_overlay"])
        self.assertEqual(placed_grade["placement_count"], 3)
        self.assertGreaterEqual(placed_grade["preview_grade"], baseline_grade["preview_grade"])

    def test_grade_preview_penalizes_rejected_placement_intents(self) -> None:
        preview = generate_preview_data(
            layout_name="fixture_layout",
            intents=[{"id": "intent_001"}],
            placement_plan={
                "visual_intents": [{"id": "intent_001"}],
                "planner_report": {"placement_count": 0, "rejected_intents": ["intent_001"], "capped_density_intents": []},
                "prop_effect_intents": [],
            },
        )

        grade = grade_preview(preview)

        self.assertTrue(grade["placement_overlay"])
        self.assertEqual(grade["placement_rejected_intent_count"], 1)
        self.assertLess(grade["Readability"], 0.82)


if __name__ == "__main__":
    unittest.main()
