"""Export selection and worker routing without a display server."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import gui_launcher as gui

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


@pytest.mark.parametrize("selection,mode", [("XSQ", "xLights"), ("LMS", "Light-O-Rama"),
                                            ("Both", "Light-O-Rama")])
def test_export_choice_routes_to_compatible_engine(selection, mode):
    interpreter = gui.tk.Tcl()
    app = SimpleNamespace(export_format_var=gui.tk.StringVar(interpreter, selection),
                          sequence_mode_var=gui.tk.StringVar(interpreter, "xLights"))
    gui.HelixGui._sync_export_format(app)
    assert app.sequence_mode_var.get() == mode
    assert app.export_format_var.get() == selection


def dual_app(tmp_path):
    interpreter = gui.tk.Tcl()
    audio, source = tmp_path / "song.wav", tmp_path / "source.lms"
    audio.touch()
    source.touch()
    values = dict(export_format_var="Both", sequence_mode_var="xLights", variants_var=1,
                  audio_var=str(audio), lor_source_var=str(source), template_var="", layout_var="",
                  output_var=str(tmp_path / "out"), profile_var="master",
                  lor_compatible_var=False, ac_on_only_var=False, generate_mp4_var=False,
                  vendor_bar_var=False, matrix_var=True, polish_var=True, shortlist_var=True,
                  learn_xsq_var=False, birdsong_var=True)
    variables = {name: (gui.tk.BooleanVar(interpreter, value) if isinstance(value, bool)
                       else gui.tk.IntVar(interpreter, value) if isinstance(value, int)
                       else gui.tk.StringVar(interpreter, value)) for name, value in values.items()}
    return SimpleNamespace(**variables, _busy=False, run_button=Mock(), status_label=Mock(),
                           _log=Mock(), _run_subprocess=Mock())


@pytest.mark.parametrize("frozen", [False, True])
def test_both_launches_existing_mapped_dual_export_on_desktop_and_portable(tmp_path, monkeypatch, frozen):
    app = dual_app(tmp_path)
    monkeypatch.setattr(gui.sys, "frozen", frozen, raising=False)
    launch = Mock()
    monkeypatch.setattr(gui.threading, "Thread", launch)
    gui.HelixGui._run_sequence(app)
    launch.assert_called_once()
    command = launch.call_args.kwargs["args"][0]
    assert command[command.index("--helix-lor-source-lms") + 1] == app.lor_source_var.get()
    assert command[command.index("--variants") + 1] == "1"
    assert "--ac-lights-only" in command
    assert "--no-effects-orchestrator" in command
    assert "--matrix-intelligence" not in command and "--birdsong" not in command
    assert app.sequence_mode_var.get() == "Light-O-Rama" and app._busy
    launch.return_value.start.assert_called_once()
    if frozen:
        assert Path(command[0]).name == "HelixCLI.exe" and "--helix-cli" in command


def test_both_requires_real_lor_layout_before_starting_worker(tmp_path, monkeypatch):
    app = dual_app(tmp_path)
    Path(app.lor_source_var.get()).unlink()
    warning, launch = Mock(), Mock()
    monkeypatch.setattr(gui.messagebox, "showwarning", warning)
    monkeypatch.setattr(gui.threading, "Thread", launch)
    gui.HelixGui._run_sequence(app)
    warning.assert_called_once()
    assert warning.call_args.args[0] == "Missing LOR Layout"
    launch.assert_not_called()
    assert not app._busy


def test_gui_has_explicit_ac_dual_export_action():
    source = GUI.read_text(encoding='utf-8')
    assert 'def _export_existing_xsq_both(self)' in source
    assert '"--format", "both", "--channel-map", mapping' in source


def test_frozen_existing_ac_dual_export_uses_bundled_worker(tmp_path, monkeypatch):
    source, mapping = tmp_path / "source.xsq", tmp_path / "approved.csv"
    destination = tmp_path / "new-output"
    destination.mkdir()
    monkeypatch.setattr(gui.sys, "frozen", True, raising=False)
    monkeypatch.setattr(gui.filedialog, "askopenfilename", Mock(side_effect=[str(source), str(mapping)]))
    monkeypatch.setattr(gui.filedialog, "askdirectory", lambda **_: str(destination))
    monkeypatch.setattr(gui.messagebox, "askyesno", lambda *_: True)
    app = SimpleNamespace(_launch_optional_export=Mock())
    gui.HelixGui._export_existing_xsq_both(app)
    command = app._launch_optional_export.call_args.args[0]
    assert Path(command[0]).name == "HelixCLI.exe"
    assert command[1:] == ["--helix-dual-format-export", str(source), str(destination),
                           "--format", "both", "--channel-map", str(mapping)]
