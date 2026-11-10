"""Capture an authentic screenshot of the running Helix Tkinter launcher.

No mockup or reconstructed interface. The image is captured directly from
the operating system window of the running GUI process.
"""
from __future__ import annotations

import argparse
import ctypes
import sys
from pathlib import Path


def capture(output: Path) -> None:
    if sys.platform != "win32":
        raise RuntimeError("This evidence capture requires a Windows desktop session")
    from ctypes import wintypes
    from PIL import ImageGrab
    from gui_launcher import HelixGui

    app = HelixGui()
    try:
        app.update_idletasks()
        app.update()
        app.lift()
        app.focus_force()
        hwnd = app.winfo_id()
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise RuntimeError("Could not locate the running GUI window")
        bounds = (rect.left, rect.top, rect.right, rect.bottom)
        if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
            raise RuntimeError(f"Invalid GUI window bounds: {bounds}")
        image = ImageGrab.grab(bbox=bounds, all_screens=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output)
        print(f"Captured actual Helix desktop GUI: {output}")
    finally:
        app.destroy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("desktop-gui-evidence.png"))
    args = parser.parse_args()
    capture(args.output)


if __name__ == "__main__":
    main()
