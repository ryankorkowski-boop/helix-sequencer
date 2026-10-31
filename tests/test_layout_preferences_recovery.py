"""Damaged saved preferences must not prevent GUI startup or layout recovery."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core import layout_preferences


class LayoutPreferenceRecoveryTests(unittest.TestCase):
    def test_non_object_preferences_do_not_crash_startup(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "settings.json"
            with patch.dict(os.environ, {"HELIX_SETTINGS_PATH": str(config)}):
                for content in ("[]", "null", "true", "1", '"text"', "{broken"):
                    with self.subTest(content=content):
                        config.write_text(content)
                        self.assertEqual(layout_preferences.load_layout(), "")

    def test_layout_selection_recovers_after_invalid_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "settings.json"
            layout = Path(directory) / "layout.xml"
            layout.write_text("<xrgb><models/></xrgb>")
            with patch.dict(os.environ, {"HELIX_SETTINGS_PATH": str(config)}):
                config.write_text("[]")
                layout_preferences.save_layout(str(layout))
                self.assertEqual(layout_preferences.load_layout(), str(layout.resolve()))
                self.assertEqual(json.loads(config.read_text())["layout_file"],
                                 str(layout.resolve()))

    def test_change_and_missing_layout_recovery_preserve_other_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "settings.json"
            first, second = Path(directory) / "first.xml", Path(directory) / "second.xml"
            first.write_text("<xrgb/>")
            second.write_text("<xrgb/>")
            config.write_text(json.dumps({"theme": "dark"}))
            with patch.dict(os.environ, {"HELIX_SETTINGS_PATH": str(config)}):
                layout_preferences.save_layout(str(first))
                layout_preferences.save_layout(str(second))
                self.assertEqual(layout_preferences.load_layout(), str(second.resolve()))
                self.assertEqual(json.loads(config.read_text())["theme"], "dark")
                second.unlink()
                self.assertEqual(layout_preferences.load_layout(), "")
                layout_preferences.save_layout(str(first))
                self.assertEqual(layout_preferences.load_layout(), str(first.resolve()))


if __name__ == "__main__":
    unittest.main()
