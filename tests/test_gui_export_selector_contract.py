"""Static GUI contract tests: no display server required."""
import ast
from pathlib import Path

GUI = Path(__file__).resolve().parents[1] / "gui_launcher.py"


def test_gui_exposes_all_three_export_choices():
    tree = ast.parse(GUI.read_text(encoding="utf-8"))
    lists = [
        [node.value for node in item.elts]
        for item in ast.walk(tree)
        if isinstance(item, ast.keyword)
        and item.arg == "values"
        and isinstance(item.value, ast.List)
        for node in [item.value]
        if all(isinstance(v, ast.Constant) for v in node.elts)
    ]
    assert ["XSQ", "LMS", "Both"] in lists


def test_gui_rejects_unimplemented_dual_export():
    source = GUI.read_text(encoding="utf-8")
    assert 'if selected == "Both":' in source
    assert '"Automatic XSQ + LMS generation is not connected. "' in source
    assert 'self.sequence_mode_var.set("Light-O-Rama" if selected == "LMS" else "xLights")' in source


def test_gui_has_explicit_ac_dual_export_action():
    source = GUI.read_text(encoding='utf-8')
    assert 'def _export_existing_xsq_both(self)' in source
    assert '"--format", "both", "--channel-map", mapping' in source
    assert 'if getattr(sys, "frozen", False):' in source
