"""Render and open a portable show in the local xLights desktop application."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import struct
import xml.etree.ElementTree as ET


def find_xlights(explicit: str | None = None) -> Path:
    candidates = [explicit] if explicit else []
    candidates.extend(shutil.which(name) for name in ("xLights", "xlights", "xLights.exe"))
    if sys.platform == "darwin":
        candidates.extend(str(base / "xLights.app/Contents/MacOS/xLights") for base in
                          (Path("/Applications"), Path.home() / "Applications"))
    elif sys.platform == "win32":
        for name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            base = os.environ.get(name)
            if base:
                candidates.extend(str(Path(base) / suffix) for suffix in
                                  ("xLights/xLights.exe", "Programs/xLights/xLights.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise FileNotFoundError("xLights was not found. Pass --xlights with the installed executable path.")


def launch_commands(executable: Path, root: Path, show: str, sequence: str) -> tuple[list[str], list[str]]:
    folder = (root / show).resolve()
    xsq = (folder / sequence).resolve()
    if not xsq.is_relative_to(folder) or not xsq.is_file():
        raise ValueError("Sequence must exist inside the chosen show folder")
    if not (folder / "xlights_rgbeffects.xml").is_file():
        raise ValueError("Chosen folder has no xLights layout")
    # mediaFile is relative to the show root, including its media/ prefix.
    common = [str(executable), "-q", "-s", str(folder), "-m", str(folder)]
    return (common + ["--headless", "-od", str(folder), str(xsq)], common + [str(xsq)])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--xlights")
    parser.add_argument("--show")
    parser.add_argument("--sequence")
    parser.add_argument("--open-only", action="store_true", help="Use an already rendered sequence")
    parser.add_argument("--render-only", action="store_true", help="Render without opening the desktop")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / "SHOWS.json").read_text())
    show = args.show or manifest["default_show"]
    sequence = args.sequence or manifest["default_sequence"]
    executable = find_xlights(args.xlights)
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        raise RuntimeError("No local desktop display is available; run this on the laptop desktop.")
    render, desktop = launch_commands(executable, root, show, sequence)
    folder = root / show
    if not args.open_only:
        fseq = (folder / sequence).with_suffix(".fseq")
        previous_mtime = fseq.stat().st_mtime_ns if fseq.exists() else None
        with (folder / "laptop_render.log").open("w") as log:
            subprocess.run(render, cwd=folder, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1800)
        if not fseq.is_file() or fseq.stat().st_size < 32:
            raise RuntimeError("xLights exited without producing a nonempty FSEQ; inspect laptop_render.log")
        with fseq.open("rb") as stream:
            header = stream.read(32)
        if header[:4] != b"PSEQ" or header[18] == 0:
            raise RuntimeError("xLights output has no valid native frames")
        duration_ms = round(float(ET.parse(folder / sequence).getroot().findtext("head/sequenceDuration")) * 1000)
        if struct.unpack_from("<I", header, 14)[0] * header[18] != duration_ms:
            raise RuntimeError("xLights output does not span the complete sequence")
        if previous_mtime is not None and fseq.stat().st_mtime_ns == previous_mtime:
            raise RuntimeError("xLights did not update the existing FSEQ; inspect laptop_render.log")
    if not args.render_only:
        subprocess.Popen(desktop, cwd=folder, start_new_session=sys.platform != "win32")
        print(f"Started xLights with {folder / sequence}; show folder: {folder}")


if __name__ == "__main__":
    main()
