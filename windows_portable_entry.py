"""Packaged Helix entrypoint. Sequencing decisions stay in the engine."""
from __future__ import annotations

import sys


def main() -> int:
    from core.helix_version import TITLE, VERSION

    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(f"{TITLE} ({VERSION})")
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "--helix-cli":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        from core.sequence_builder import main as cli_main
        return cli_main()
    if len(sys.argv) > 1 and sys.argv[1] == "--helix-gui-smoke":
        from gui_launcher import HelixGui

        app = HelixGui()
        try:
            assert TITLE in app.title(), app.title()
            print("Helix GUI initialization OK", flush=True)
        finally:
            app.destroy()
        return 0
    from gui_launcher import main as gui_main
    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
