"""GUI modernization smoke checks without a display or audio dependencies."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GuiModernizationSmoke(unittest.TestCase):
    def test_desktop_sources_parse(self):
        for name in ("gui_launcher.py", "gui_lightshow.py", "gui_launcher_drummer.py"):
            with self.subTest(name=name):
                ast.parse((ROOT / name).read_text(encoding="utf-8"))

    def test_desktop_worker_marshals_updates(self):
        module = ast.parse((ROOT / "gui_launcher.py").read_text(encoding="utf-8"))
        gui = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "HelixGui")
        worker = next(node for node in gui.body if isinstance(node, ast.FunctionDef) and node.name == "_run_subprocess")
        calls = [node for node in ast.walk(worker) if isinstance(node, ast.Call)]
        self.assertFalse(any(isinstance(call.func, ast.Attribute) and call.func.attr in
                             ("configure", "set_running", "after", "_log") for call in calls))

    def test_support_links_remain_configured(self):
        links = json.loads((ROOT / "config/support_links.json").read_text(encoding="utf-8"))
        self.assertTrue(links["helix"].startswith("https://"))
        self.assertTrue(links["xlights"].startswith("https://"))
        desktop = (ROOT / "gui_launcher.py").read_text(encoding="utf-8")
        android = (ROOT / "android/app/src/main/java/org/helixsequencer/android/MainActivity.java").read_text(encoding="utf-8")
        for label in ("Donate to Helix", "Donate to xLights", "Instructions", "View License"):
            self.assertIn(label, desktop)
        for label in ("Instructions", "Legal", "SupportLinks.add"):
            self.assertIn(label, android)

    def test_android_animation_class_and_lifecycle(self):
        base = ROOT / "android/app/src/main/java/org/helixsequencer/android"
        animation = (base / "SequencingLightShowView.java").read_text(encoding="utf-8")
        activity = (base / "MainActivity.java").read_text(encoding="utf-8")
        for name in ("drawArches", "drawTree", "setRunning", "onDetachedFromWindow"):
            self.assertIn(name, animation)
        self.assertIn("lightShow.setRunning(false)", activity)


if __name__ == "__main__":
    unittest.main()
