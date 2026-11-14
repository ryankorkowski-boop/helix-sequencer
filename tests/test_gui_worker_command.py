from pathlib import Path

import gui_launcher
import windows_portable_entry


def test_packaged_gui_launches_bundled_console_worker(monkeypatch, tmp_path):
    executable = tmp_path / "Helix" / "Helix.exe"
    monkeypatch.setattr(gui_launcher.sys, "frozen", True, raising=False)
    monkeypatch.setattr(gui_launcher.sys, "executable", str(executable))
    assert gui_launcher._worker_command("--helix-cli", gui_launcher.ROOT / "main.py") == [
        str(executable.with_name("HelixCLI.exe")), "--helix-cli",
    ]
    assert gui_launcher._worker_command("--helix-build-helixville", gui_launcher.ROOT / "tools" / "build_helixville_layout.py") == [
        str(executable.with_name("HelixCLI.exe")), "--helix-build-helixville",
    ]


def test_source_gui_launches_python_entrypoint(monkeypatch):
    monkeypatch.delattr(gui_launcher.sys, "frozen", raising=False)
    interpreter, script = gui_launcher._worker_command("--helix-cli", gui_launcher.ROOT / "main.py")
    assert interpreter == gui_launcher.sys.executable
    assert Path(script) == gui_launcher.ROOT / "main.py"


def test_packaged_layout_worker_writes_layout(monkeypatch, tmp_path):
    monkeypatch.setattr(windows_portable_entry.sys, "argv", [
        "HelixCLI.exe", "--helix-build-helixville", "--output-dir", str(tmp_path),
    ])

    assert windows_portable_entry.main() == 0
    assert (tmp_path / "xlights_rgbeffects.xml").is_file()
