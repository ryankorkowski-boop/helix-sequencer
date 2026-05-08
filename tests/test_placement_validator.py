from __future__ import annotations

import unittest

from helix_intent.placement_validator import validate_placement_plan


def _valid_plan() -> dict[str, object]:
    return {
        "visual_intents": [
            {"id": "intent_001"},
            {"id": "intent_002"},
        ],
        "candidates": [
            {"prop_name": "Mega Tree", "role": "hero"},
            {"prop_name": "Front Roof", "role": "structure"},
        ],
        "prop_effect_intents": [
            {
                "visual_intent_id": "intent_001",
                "target_prop": "Mega Tree",
                "effect_family": "energy_wave",
                "brightness_cap": 0.82,
            },
            {
                "visual_intent_id": "intent_002",
                "target_prop": "Front Roof",
                "effect_family": "outline_pulse",
                "brightness_cap": 0.62,
            },
        ],
        "planner_report": {
            "intent_count": 2,
            "placement_count": 2,
            "rejected_intents": [],
            "capped_density_intents": [],
        },
    }


class PlacementValidatorTests(unittest.TestCase):
    def test_valid_plan_passes(self) -> None:
        report = validate_placement_plan(_valid_plan())

        self.assertTrue(report.passed)
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.metrics["placement_count"], 2)
        self.assertEqual(report.metrics["effect_family_count"], 2)

    def test_rejects_plan_with_intents_but_no_placements(self) -> None:
        plan = _valid_plan()
        plan["prop_effect_intents"] = []
        plan["planner_report"] = {
            "intent_count": 2,
            "placement_count": 0,
            "rejected_intents": ["intent_001", "intent_002"],
            "capped_density_intents": [],
        }

        report = validate_placement_plan(plan)

        self.assertFalse(report.passed)
        self.assertTrue(any("no prop-effect intents" in error for error in report.errors))
        self.assertTrue(any("Rejected intent share too high" in error for error in report.errors))

    def test_rejects_unsupported_effect_and_bad_brightness(self) -> None:
        plan = _valid_plan()
        plan["prop_effect_intents"] = [
            {
                "visual_intent_id": "intent_001",
                "target_prop": "Mega Tree",
                "effect_family": "unsupported_flash_blast",
                "brightness_cap": 1.25,
            }
        ]
        plan["planner_report"] = {"intent_count": 1, "placement_count": 1, "rejected_intents": [], "capped_density_intents": []}

        report = validate_placement_plan(plan)

        self.assertFalse(report.passed)
        self.assertTrue(any("unsupported effect_family" in error for error in report.errors))
        self.assertTrue(any("brightness_cap outside" in error for error in report.errors))

    def test_warns_for_unknown_candidate_and_target_overuse(self) -> None:
        plan = _valid_plan()
        plan["prop_effect_intents"] = [
            {"visual_intent_id": "intent_001", "target_prop": "Unknown Target", "effect_family": "energy_wave", "brightness_cap": 0.7},
            {"visual_intent_id": "intent_002", "target_prop": "Mega Tree", "effect_family": "energy_wave", "brightness_cap": 0.7},
            {"visual_intent_id": "intent_002", "target_prop": "Mega Tree", "effect_family": "energy_wave", "brightness_cap": 0.7},
        ]
        plan["planner_report"] = {"intent_count": 2, "placement_count": 3, "rejected_intents": [], "capped_density_intents": []}

        report = validate_placement_plan(plan)

        self.assertTrue(report.passed)
        self.assertGreater(report.warning_count, 0)
        self.assertTrue(any("not present in candidate inventory" in warning for warning in report.warnings))
        self.assertTrue(any("too much of the plan" in warning for warning in report.warnings))

    def test_warns_for_high_brightness_without_failing(self) -> None:
        plan = _valid_plan()
        plan["prop_effect_intents"][0]["brightness_cap"] = 0.9  # type: ignore[index]

        report = validate_placement_plan(plan)

        self.assertTrue(report.passed)
        self.assertTrue(any("high brightness_cap" in warning for warning in report.warnings))


if __name__ == "__main__":
    unittest.main()
