"""Packaged Helix entrypoint; never change sequencing decisions in this layer."""
from __future__ import annotations

import sys


def main() -> int:
    # The console-subsystem helper lets the GUI capture native stdout and
    # tracebacks. The windowed Helix.exe remains the only user-facing launcher.
    tool_modes = {
        "--helix-legacy-lms-export": "tools.legacy_lms_export",
        "--helix-native-render": "tools.validate_native_xlights",
        "--helix-fseq-preview": "tools.fseq_pixel_preview",
    }
    if len(sys.argv) > 1 and sys.argv[1] in tool_modes:
        import importlib
        module = tool_modes[sys.argv[1]]
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        return importlib.import_module(module).main() or 0
    if len(sys.argv) > 1 and sys.argv[1] == "--helix-cli":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        from core.sequence_builder import main as cli_main
        return cli_main()
    if len(sys.argv) > 1 and sys.argv[1] == "--helix-build-helixville":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        from tools.build_helixville_layout import main as layout_main
        return layout_main()
    if len(sys.argv) > 1 and sys.argv[1] == "--helix-gui-smoke":
        from gui_launcher import HelixGui
        app = HelixGui()
        try:
            assert app.template_var.get(), "Template not selected"
            assert app.layout_var.get(), "Layout not selected"
            app.sequence_mode_var.set("Light-O-Rama")
            app.update_idletasks()
            assert str(app.template_entry.cget("state")) == "disabled"
            assert str(app.lor_source_entry.cget("state")) == "normal"
            assert str(app.matrix_button.cget("state")) == "disabled"
            assert all(str(w.cget("state")) == "disabled" for w in app.birdsong_frame.winfo_children())
            app.sequence_mode_var.set("xLights")
            app.lor_compatible_var.set(True)
            assert str(app.palette_combo.cget("state")) == "disabled"
            app.lor_compatible_var.set(False)
            assert str(app.palette_combo.cget("state")) == "readonly"
            assert str(app.template_entry.cget("state")) == "normal"
            app.update_idletasks()
            print("Helix GUI initialization OK", flush=True)
        finally:
            app.destroy()
        return 0

    from gui_launcher import main as gui_main
    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
