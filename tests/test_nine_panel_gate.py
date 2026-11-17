"""Nine-panel approval gate regressions: never render placeholders as owner-ready."""
import copy
import json
import unittest
from pathlib import Path

from tools.layout_bench.validate_nine_panel import LOCK, MANIFEST, validate


class NinePanelGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = json.loads(Path(LOCK).read_text(encoding="utf-8"))
        cls.fixtures = json.loads(Path(MANIFEST).read_text(encoding="utf-8"))

    def test_native_model_zoo_generator_has_broad_families_and_groups(self):
        from tools.layout_bench.generate_layouts import build_native_model_zoo
        layout = build_native_model_zoo()
        self.assertGreaterEqual(len(layout.models), 70)
        groups = {name: members for name, members in layout.groups}
        for family in ("Custom Trees", "Mega Trees", "Stars", "Spinners", "Candy Canes", "Arches", "Snowflakes", "Matrices"):
            self.assertIn("All " + family, groups)
            self.assertTrue(groups["All " + family])
        for group in ("Zoo Left", "Zoo Right", "Zoo Foreground", "Zoo Background",
                      "Zoo Melodic Instruments", "Zoo Rhythmic Accents"):
            self.assertIn(group, groups)
        self.assertEqual(len({model["name"] for model in layout.models}), len(layout.models))

    def test_combined_vocal_models_are_panel_four(self):
        slot = self.lock["slots"][3]
        self.assertEqual(slot["position"], "middle_left")
        self.assertIn("singing_trees", slot["grouping"])
        self.assertIn("coro_faces", slot["grouping"])
        self.assertIn("lead_vocal_only", slot["grouping"])
        self.assertIn("harmony_vocal_only", slot["grouping"])

    def test_native_model_zoo_is_panel_six(self):
        slot = self.lock["slots"][5]
        self.assertEqual(slot["position"], "middle_right")
        for family in ("custom_trees", "stars", "spinners", "candy_canes", "mega_trees"):
            self.assertIn(family, slot["model_families"])
        self.assertIn("by_instrument_role", slot["grouping"])

    def test_all_panels_require_nested_musical_grouping(self):
        policy = self.lock["grouping_policy"]
        self.assertEqual(policy["scope"], "all_nine_panels")
        self.assertIn("submodel_routing", policy["required_capabilities"])
        self.assertIn("distinct_motion_beyond_beat_pulsing", policy["verification"])

    def test_locked_layout_structure(self):
        self.assertEqual(validate(self.lock, self.fixtures, approval=False), [])

    def test_current_plan_fails_approval(self):
        errors = validate(self.lock, self.fixtures)
        self.assertTrue(any("top_middle" in error for error in errors))
        self.assertTrue(any("middle_center" in error for error in errors))
        self.assertTrue(any("real vocal audio" in error for error in errors))

    def test_render_preflight_does_not_require_finished_render(self):
        lock = copy.deepcopy(self.lock)
        for slot in lock["slots"]:
            slot["status"] = "verified"
            if not slot["fixture_id"]:
                slot["fixture_id"] = "ac32_house" if slot["position"] == "top_middle" else (
                    "pixel_starter" if slot["position"] == "middle_left" else "pixel_driveway"
                )
        lock["audio"]["status"] = "verified"
        self.assertEqual(validate(lock, self.fixtures, require_render=False), [])
        self.assertTrue(any("render" in error for error in validate(lock, self.fixtures)))

    def test_reordered_center_is_rejected(self):
        lock = copy.deepcopy(self.lock)
        lock["slots"][4], lock["slots"][5] = lock["slots"][5], lock["slots"][4]
        self.assertTrue(any("ordering" in error for error in validate(lock, self.fixtures, approval=False)))

    def test_unknown_fixture_is_rejected(self):
        lock = copy.deepcopy(self.lock)
        lock["slots"][0]["fixture_id"] = "made_up"
        self.assertTrue(any("unknown fixture" in error for error in validate(lock, self.fixtures, approval=False)))

    def test_duplicate_fixture_is_rejected(self):
        lock = copy.deepcopy(self.lock)
        lock["slots"][2]["fixture_id"] = "ac16_lor"
        self.assertTrue(any("duplicate" in error for error in validate(lock, self.fixtures, approval=False)))


if __name__ == "__main__":
    unittest.main()
