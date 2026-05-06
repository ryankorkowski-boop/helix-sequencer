from __future__ import annotations

import unittest

from tools.build_helpers.variant_lanes import (
    AUXILIARY_LANE,
    CINEMATIC_LANE,
    HOOK_LANE,
    SIGNATURE_LANE,
    SPATIAL_LANE,
    STEM_LANE,
    build_variant_lane_plan,
    lane_for_variant,
    normalize_variant_label,
)


class VariantLaneTests(unittest.TestCase):
    def test_normalize_variant_label_is_deterministic(self) -> None:
        self.assertEqual(normalize_variant_label("Hook Focus"), "hook_focus")
        self.assertEqual(normalize_variant_label("wide-stage"), "wide_stage")
        self.assertEqual(normalize_variant_label("  Stem_Story  "), "stem_story")
        self.assertEqual(normalize_variant_label(None), "")

    def test_known_variants_map_to_named_lanes(self) -> None:
        self.assertEqual(lane_for_variant("signature"), SIGNATURE_LANE)
        self.assertEqual(lane_for_variant("hook_focus"), HOOK_LANE)
        self.assertEqual(lane_for_variant("wide_stage"), SPATIAL_LANE)
        self.assertEqual(lane_for_variant("stem_story"), STEM_LANE)
        self.assertEqual(lane_for_variant("cinematic_arc"), CINEMATIC_LANE)

    def test_unknown_variants_fall_back_to_auxiliary_lane(self) -> None:
        self.assertEqual(lane_for_variant("experimental_glitter_burst"), AUXILIARY_LANE)
        self.assertEqual(lane_for_variant(None), AUXILIARY_LANE)

    def test_build_variant_lane_plan_is_report_only_and_deterministic(self) -> None:
        entries = [
            {
                "label": "signature",
                "description": "Base backbone.",
                "quality_gate_passed": True,
                "shortlist_score": 94.25,
            },
            {
                "label": "hook-focus",
                "description": "Hooks and accents.",
                "quality_gate_passed": False,
                "shortlist_score": 83.5,
            },
            {
                "label": "unknown lane",
                "description": "Future experiment.",
            },
        ]

        plan = build_variant_lane_plan(entries)

        self.assertEqual(plan["version"], 1)
        self.assertEqual(plan["mode"], "variant_lanes_plan")
        self.assertFalse(plan["composite_enabled"])
        self.assertEqual(plan["assignment_count"], 3)
        self.assertEqual(plan["lane_count"], 3)
        self.assertEqual(plan["assignments"][0]["lane"], SIGNATURE_LANE)
        self.assertEqual(plan["assignments"][1]["label"], "hook_focus")
        self.assertEqual(plan["assignments"][1]["lane"], HOOK_LANE)
        self.assertEqual(plan["assignments"][1]["quality_gate_passed"], False)
        self.assertEqual(plan["assignments"][2]["lane"], AUXILIARY_LANE)
        self.assertIn(SIGNATURE_LANE, plan["lanes"])
        self.assertIn(HOOK_LANE, plan["lanes"])
        self.assertIn(AUXILIARY_LANE, plan["lanes"])

    def test_missing_labels_are_still_planned(self) -> None:
        plan = build_variant_lane_plan([{}])

        self.assertEqual(plan["assignment_count"], 1)
        self.assertEqual(plan["assignments"][0]["label"], "variant_1")
        self.assertEqual(plan["assignments"][0]["lane"], AUXILIARY_LANE)


if __name__ == "__main__":
    unittest.main()
