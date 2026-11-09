"""Shared choices backed by existing engine palettes and native layout files."""
from __future__ import annotations

import json
from pathlib import Path

OPTIONS = json.loads((Path(__file__).resolve().parents[1] / "config/gui_options.json").read_text(encoding="utf-8"))
PALETTES = {item["title"]: item["key"] for item in OPTIONS["palettes"]}
PALETTE_KEYS = frozenset(PALETTES.values())


def palette_key(value: str) -> str:
    # Preserve settings from earlier desktop and phone builds.
    legacy = {"Default colors": "default", "Musical neon palettes": "neon"}
    key = PALETTES.get(value, legacy.get(value, value))
    if key not in PALETTE_KEYS:
        raise ValueError("Unsupported color palette")
    return key


def layout_options() -> list[dict[str, str]]:
    return OPTIONS["layouts"] + OPTIONS["stages"]


def resolve_layout(root: Path, key: str) -> Path:
    item = next((item for item in layout_options() if item["key"] == key), None)
    if item is None:
        raise ValueError("Unknown sample layout")
    for base in (root, root / "_internal"):
        candidate = base / item["path"]
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Sample layout is missing: {item['title']}")
