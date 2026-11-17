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

    def test_locked_layout_structure(self):
        self.assertEqual(validate(self.lock, self.fixtures, approval=False), [])

    def test_current_plan_fails_approval(self):
        errors = validate(self.lock, self.fixtures)
        self.assertTrue(any("top_middle" in error for error in errors))
        self.assertTrue(any("middle_center" in error for error in errors))
        self.assertTrue(any("real vocal audio" in error for error in errors))

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
