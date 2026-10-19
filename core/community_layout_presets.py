"""Community-informed Helix layout archetypes and inventory matching.

These are design presets, NOT a statistically sampled Facebook dataset.
No existing user layout or controller mapping is changed by this module.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from typing import Mapping


@dataclass(frozen=True)
class LayoutPreset:
    key: str
    title: str
    models: tuple[tuple[str, int], ...]
    kind: str = "rgb"

    @property
    def model_count(self) -> int:
        return sum(count for _, count in self.models)

    def inventory(self) -> dict[str, int]:
        return dict(self.models)


PRESETS = (
    LayoutPreset("starter", "Starter Yard", (("house_outline", 1), ("mega_tree", 1), ("star", 1), ("arch", 4))),
    LayoutPreset("classic", "Classic Christmas", (("house_outline", 1), ("mega_tree", 1), ("star", 1), ("arch", 6), ("mini_tree", 8), ("candy_cane", 8), ("snowflake", 4))),
    LayoutPreset("standard_rgb", "Standard RGB", (("house_outline", 2), ("mega_tree", 1), ("star", 2), ("arch", 8), ("mini_tree", 8), ("snowflake", 8), ("spinner", 4), ("matrix", 1))),
    LayoutPreset("vocal", "Vocal Showcase", (("house_outline", 2), ("mega_tree", 1), ("arch", 8), ("mini_tree", 8), ("snowflake", 6), ("singing_face", 2), ("matrix", 1))),
    LayoutPreset("large", "Large Residential", (("house_outline", 4), ("mega_tree", 2), ("star", 4), ("arch", 16), ("mini_tree", 16), ("candy_cane", 16), ("snowflake", 16), ("spinner", 8), ("matrix", 2))),
    LayoutPreset("ultimate", "Ultimate Helix", (("house_outline", 12), ("mega_tree", 4), ("star", 12), ("arch", 24), ("mini_tree", 24), ("candy_cane", 24), ("snowflake", 24), ("spinner", 16), ("matrix", 4), ("singing_face", 4), ("band_performer", 8))),
    LayoutPreset("legacy_ac16", "Legacy AC 16", (("ac_channel", 16),), kind="ac"),
    LayoutPreset("legacy_ac256", "Legacy AC 256", (("ac_channel", 256),), kind="ac"),
)


def normalize_model_type(name: str) -> str:
    value = name.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "megatree": "mega_tree", "megatrees": "mega_tree",
        "minitree": "mini_tree", "minitrees": "mini_tree",
        "arches": "arch", "stars": "star", "snowflakes": "snowflake",
        "spinners": "spinner", "matrices": "matrix",
        "candycanes": "candy_cane", "singing_faces": "singing_face",
        "roofline": "house_outline", "roof_outline": "house_outline",
    }
    return aliases.get(value, value)


def rank_layouts(user_inventory: Mapping[str, int], *, kind: str = "rgb") -> list[dict]:
    """Rank by weighted model overlap, penalizing excess and missing props.

    This is an import-assistance heuristic, not an automatic xLights mapping.
    """
    inventory = Counter()
    for name, count in user_inventory.items():
        amount = int(count)
        if amount < 0:
            raise ValueError("Model counts must not be negative")
        inventory[normalize_model_type(name)] += amount
    ranked = []
    for preset in PRESETS:
        if preset.kind != kind:
            continue
        wanted = preset.inventory()
        common = sum(min(inventory.get(name, 0), n) for name, n in wanted.items())
        user_total = sum(inventory.values())
        preset_total = preset.model_count
        score = (2 * common / (user_total + preset_total)) if user_total + preset_total else 0.0
        ranked.append({
            "preset": preset.key,
            "title": preset.title,
            "score": round(score, 4),
            "matching_models": common,
            "missing_models": {k: max(0, v - inventory.get(k, 0)) for k, v in wanted.items() if v > inventory.get(k, 0)},
            "extra_models": {k: max(0, v - wanted.get(k, 0)) for k, v in inventory.items() if v > wanted.get(k, 0)},
        })
    return sorted(ranked, key=lambda item: (-item["score"], item["preset"]))
