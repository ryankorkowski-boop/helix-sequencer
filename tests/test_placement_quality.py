from __future__ import annotations

import unittest

from helix_intent.placement_quality import score_placement_plan


def _plan() -> dict[str, object]:
    return {
        "visual_intents": [{"id": f"intent_{idx:03d}"} for idx in range(1, 4)],
        "candidates": [
            {"prop_name": "Mega Tree", "role": "hero"},
            {"prop_name": "Front Roof", "role": "structure"},
            {"prop_name": "Matrix", "role": "detail_surface"},
            {"prop_name": "Singer", "role": "vocals"},
        ],
        "prop_effect_intents": [
            {"visual_intent_id": "intent_001", "target_prop": "Mega Tree", "target_role": "hero", "effect_family": "energy_wave", "brightness_cap": 0.82},
            {"visual_intent_id": "intent_001", "target_prop": "Front Roof", "target_role": "structure", "effect_family": "outline_pulse", "brightness_cap": 0.62},
            {"visual_intent_id": "intent_002", "target_prop": "Matrix", "target_role": "detail_surface", "effect_family": "matrix_pulse", "brightness_cap": 0.7},
            {"visual_intent_id": "intent_003", "target_prop": "Singer", "target_role": "vocals", "effect_family": "lyric_pulse", "brightness_cap": 0.55},
        ],
        "planner_report": {"intent_count": 3, "placement_count": 4, "rejected_intents": [], "capped_density_intents": []},
        "validation_report": {"passed": True, "warning_count": 0, "error_count": 0},
    }


class PlacementQualityTests(unittest.TestCase):
    def test_scores_good_plan(self) -> None:
        report = score_placement_plan(_plan())

        self.assertGreaterEqual(report.overall_placement_score, 0.7)
        self.assertIn(report.grade, {"good", "showcase_ready", "excellent"})
        self.assertEqual(report.metrics["unique_target_count"], 4)
        self.assertEqual(report.metrics["unique_effect_family_count"], 4)

    def test_penalizes_rejected_and_empty_plan(self) -> None:
        plan = _plan()
        plan["prop_effect_intents"] = []
        plan["planner_report"] = {"intent_count": 3, "placement_count": 0, "rejected_intents": ["intent_001", "intent_002"], "capped_density_intents": []}
        plan["validation_report"] = {"passed": False, "warning_count": 0, "error_count": 2}

        report = score_placement_plan(plan)

        self.assertEqual(report.grade, "blocked")
        self.assertLess(report.coverage_score, 0.4)
        self.assertEqual(report.validation_score, 0.0)
        self.assertTrue(report.recommendations)

    def test_penalizes_missing_candidate_target_and_high_brightness(self) -> None:
        plan = _plan()
        plan["prop_effect_intents"] = [
            {"visual_intent_id": "intent_001", "target_prop": "Unknown", "target_role": "hero", "effect_family": "energy_wave", "brightness_cap": 0.95},
        ]
        plan["planner_report"] = {"intent_count": 1, "placement_count": 1, "rejected_intents": [], "capped_density_intents": []}
        plan["validation_report"] = {"passed": True, "warning_count": 2, "error_count": 0}

        report = score_placement_plan(plan)

        self.assertLess(report.role_match_score, 1.0)
        self.assertLess(report.brightness_safety_score, 1.0)
        self.assertEqual(report.metrics["missing_candidate_target_count"], 1)


if __name__ == "__main__":
    unittest.main()
