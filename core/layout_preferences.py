"""Persist the selected xLights layout outside the installation directory."""
from __future__ import annotations

import json
import os
from pathlib import Path


def settings_path() -> Path:
    override = os.environ.get("HELIX_SETTINGS_PATH")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "HelixSequencer" / "settings.json"


def load_layout() -> str:
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return ""
        value = data.get("layout_file", "")
        return value if isinstance(value, str) and Path(value).is_file() else ""
    except (OSError, ValueError, TypeError):
        return ""


def save_layout(path: str) -> None:
    value = Path(path).expanduser().resolve()
    if not value.is_file() or value.suffix.lower() not in {".xml", ".xbkp"}:
        raise ValueError("Choose an existing xLights layout XML or XBKP file")
    target = settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError, TypeError):
        pass
    data["layout_file"] = str(value)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)

