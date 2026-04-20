from __future__ import annotations

"""One-click entrypoint for Dream Sequence Weaver's GUI and CLI workflows."""

import sys


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv[:1] == ["--render-preview"]:
        from tools import preview_renderer

        return preview_renderer.main(argv[1:])
    if argv[:1] == ["--showcase-clip"]:
        from tools import showcase_clip

        return showcase_clip.main(argv[1:])

    if not argv:
        try:
            from core.gui_launcher import run_gui

            return run_gui()
        except Exception as exc:
            # Fall back to CLI mode if GUI is unavailable in the current environment.
            print(f"GUI launcher unavailable ({exc}). Falling back to CLI mode.")

    from core.sequence_builder import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
