"""Packaged Helix entrypoint; never change sequencing decisions in this layer."""
from __future__ import annotations

import sys


def main() -> int:
    # The console-subsystem helper lets the GUI capture native stdout and
    # tracebacks. The windowed Helix.exe remains the only user-facing launcher.
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
            app.update_idletasks()
            print("Helix GUI initialization OK", flush=True)
        finally:
            app.destroy()
        return 0

    from gui_launcher import main as gui_main
    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
