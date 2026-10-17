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
    assert '"Both outputs are not yet supported by this GUI."' in source
    assert 'self.sequence_mode_var.set("Light-O-Rama" if selected == "LMS" else "xLights")' in source
