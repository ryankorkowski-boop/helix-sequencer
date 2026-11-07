"""Prepare a self-contained xLights show directory without modifying source files."""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


def prepare_show_folder(layout_file: str, audio_file: str, destination: str) -> dict[str, str]:
    layout = Path(layout_file).expanduser().resolve()
    audio = Path(audio_file).expanduser().resolve()
    folder = Path(destination).expanduser().resolve()
    if not layout.is_file() or layout.suffix.lower() not in {".xml", ".xbkp"}:
        raise ValueError("An existing xLights layout XML or XBKP is required")
    if not audio.is_file() or audio.suffix.lower() not in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}:
        raise ValueError("An existing supported audio file is required")
    if layout == audio:
        raise ValueError("Layout and audio must be separate files")
    # Validate before copying: an XBKP may be a ZIP backup, not usable XML.
    try:
        root = ET.parse(layout).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ValueError("Layout is not XML; restore the XBKP backup in xLights and select xlights_rgbeffects.xml") from exc
    if root.tag.lower() not in {"xrgb", "xlights_rgbeffects"}:
        raise ValueError(f"Unexpected xLights layout XML root: {root.tag}")
    target_layout = folder / "xlights_rgbeffects.xml"
    target_audio = folder / audio.name
    for source, target in ((layout, target_layout), (audio, target_audio)):
        if target.exists() and not source.samefile(target):
            raise FileExistsError(f"Refusing to overwrite existing show file: {target}")
    folder.mkdir(parents=True, exist_ok=True)
    if not target_layout.exists():
        shutil.copy2(layout, target_layout)
    if not target_audio.exists():
        shutil.copy2(audio, target_audio)
    return {"show_folder": str(folder), "layout_file": str(target_layout), "audio_file": str(target_audio)}
