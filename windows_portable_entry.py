"""Standalone Windows GUI entrypoint; engine execution stays unchanged."""
import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--helix-cli":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        from core.sequence_builder import main as cli_main
        return cli_main()
    if len(sys.argv) > 1 and sys.argv[1] == "--helix-build-helixville":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        from tools.build_helixville_layout import main as layout_main
        return layout_main()
    from gui_launcher import main as gui_main
    return gui_main()

if __name__ == "__main__":
    raise SystemExit(main())
