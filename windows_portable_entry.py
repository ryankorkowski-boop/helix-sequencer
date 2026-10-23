"""Packaged Helix entrypoint; never change sequencing decisions in this layer."""
from __future__ import annotations

import sys


def main() -> int:
    # The console-subsystem helper lets the GUI capture native stdout and
    # tracebacks. The windowed Helix.exe remains the only user-facing launcher.
    tool_modes = {
        "--helix-dual-format-export": "tools.dual_format_export",
        "--helix-remote-server": "tools.desktop_remote",
        "--helix-remote-worker": "tools.desktop_remote_worker",
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
            # A clean installation legitimately has no saved layout. Verify
            # the first-run state without inventing a user selection.
            from core.layout_preferences import load_layout
            saved_layout = load_layout()
            if saved_layout:
                assert app.layout_var.get() == saved_layout, "Saved layout not restored"
            else:
                # First-run installs intentionally select a bundled showcase preset.
                assert app.layout_var.get(), "No first-run layout selected"
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
            def widget_labels(widget):
                labels=[]
                try: labels.append(str(widget.cget("text")))
                except Exception: pass
                for child in widget.winfo_children(): labels.extend(widget_labels(child))
                return labels
            assert {"Donate to xLights", "Donate to Helix"}.issubset(widget_labels(app)), "Donation controls missing"
            app._open_phone_remote()
            app.update_idletasks()
            assert app._phone_link_window.winfo_exists(), "Phone remote dialog missing"
            print("Helix GUI initialization OK", flush=True)
        finally:
            app.destroy()
        return 0

    from gui_launcher import main as gui_main
    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
