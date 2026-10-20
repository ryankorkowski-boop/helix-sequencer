"""Static GUI contract tests: no display server required."""
import ast
from pathlib import Path

GUI = Path(__file__).resolve().parents[1] / "gui_launcher.py"


def test_gui_exposes_all_three_export_choices():
    tree = ast.parse(GUI.read_text(encoding="utf-8"))
    lists = [
        [node.value for node in item.value.elts]
        for item in ast.walk(tree)
        if isinstance(item, ast.keyword)
        and item.arg == "values"
        and isinstance(item.value, ast.List)
        for node in [item.value]
        if all(isinstance(v, ast.Constant) for v in node.elts)
    ]
    assert ["XSQ", "LMS", "Both"] in lists


def test_gui_selects_mapped_ac_mode_for_both():
    import gui_launcher as gui
    from types import SimpleNamespace
    class Var:
        def __init__(self, value): self.value = value
        def get(self): return self.value
        def set(self, value): self.value = value
    app = SimpleNamespace(export_format_var=Var("Both"), ac_on_only_var=Var(False),
                          lor_compatible_var=Var(True), sequence_mode_var=Var("Light-O-Rama"))
    gui.HelixGui._sync_export_format(app)
    assert app.export_format_var.get() == "Both"
    assert app.ac_on_only_var.get() is True
    assert app.lor_compatible_var.get() is False
    assert app.sequence_mode_var.get() == "xLights"


def test_gui_has_explicit_ac_dual_export_action():
    source = GUI.read_text(encoding='utf-8')
    assert 'def _export_existing_xsq_both(self)' in source
    assert '"--format", "both", "--channel-map", mapping' in source
    assert 'if getattr(sys, "frozen", False):' in source
