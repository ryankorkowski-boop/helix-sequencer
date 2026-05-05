from __future__ import annotations

from core import model_parser as xmp
from helix_layout.semantic_alias_mapper import semantic_alias


def classify_prop_role(model: xmp.Model) -> list[str]:
    alias = semantic_alias(model.display_as or model.type or model.name)
    roles: list[str] = []
    roles.append("pixel_prop" if model.is_rgb_capable() else "AC_channel" if model.is_single_color() else "pixel_prop")
    if alias in {"matrix"}:
        roles.extend(["matrix", "hero_prop", "vocal_prop"])
    if alias in {"mega_tree", "tree"}:
        roles.extend(["mega_tree", "upper_prop", "rhythm_prop"])
    if alias in {"mini_tree"}:
        roles.extend(["mini_tree", "accent_prop", "ground_prop"])
    if alias in {"arches"}:
        roles.extend(["arch", "rhythm_prop"])
    if alias in {"star", "spinner"}:
        roles.extend(["accent_prop", "upper_prop"])
    if "face" in alias or "singing" in alias:
        roles.extend(["singing_face", "vocal_prop", "hero_prop"])
    if "roof" in alias:
        roles.extend(["roofline", "background_prop"])
    if "snowman" in model.name.lower():
        roles.extend(["custom_character", "snowman_band_member", "hero_prop"])
    if not roles:
        roles.append("background_prop")
    return sorted(dict.fromkeys(roles))
