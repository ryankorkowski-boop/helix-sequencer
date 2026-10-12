"""Conservative xLights XSQ fence for LOR-compatible single-color shows.

This is NOT an LMS converter and does not infer hardware addresses. It keeps
Helix's timing and channel choreography intact, while preventing unsupported
pixel-only effect names/targets from escaping an --ac-lights-only build.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

# LOR can express steady intensity, fades, shimmer, twinkle and off. xLights
# native 'On' expresses both steady intensity and fades through settings.
AC_EFFECTS = frozenset({"On", "Off", "Shimmer", "Twinkle"})
SHIMMER_SETTINGS = ""
ON_SETTINGS = "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"
FADE_SETTINGS = "E_TEXTCTRL_Eff_On_Start=0,E_TEXTCTRL_Eff_On_End=100"
WHITE_PALETTE = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"


def ac_layout_targets(layout: Path):
    """Preserve *all* single-color models, including generic Intensity AC."""
    root = ET.parse(layout).getroot()
    safe: set[str] = set()
    other: set[str] = set()
    for m in root.findall("./models/model"):
        name = (m.get("name") or "").strip()
        if not name:
            continue
        kind = (m.get("StringType") or "").strip().lower()
        if "single color" in kind:
            safe.add(name)
        else:
            other.add(name)
    if not safe:
        raise ValueError("No xLights Single Color AC models found in this layout")
    groups: dict[str, tuple[str, ...]] = {}
    for m in root.findall("./modelGroups/modelGroup"):
        name = (m.get("name") or "").strip()
        if name:
            groups[name] = tuple(
                part.strip() for part in (m.get("models") or "").split(",")
                if part.strip()
            )
    return safe, other, groups


def _safe_leaves(name: str, safe: set[str], groups: dict, seen=None) -> set[str]:
    seen = set() if seen is None else seen
    if name in seen:
        return set()
    if name in safe:
        return {name}
    members = groups.get(name)
    if not members:
        return set()
    leaves: set[str] = set()
    for member in members:
        leaves.update(_safe_leaves(member, safe, groups, seen | {name}))
    return leaves


def _all_leaves(name: str, known: set[str], groups: dict, seen=None) -> set[str]:
    seen = set() if seen is None else seen
    if name in seen:
        return set()
    if name in known:
        return {name}
    return set().union(*[
        _all_leaves(member, known, groups, seen | {name})
        for member in groups.get(name, ())
    ])


def _resolve_settings(root):
    db = root.find("EffectDB")
    if db is None:
        db = ET.Element("EffectDB")
        root.insert(0, db)
    return db, [el.text or "" for el in db.findall("Effect")]


def _setting_ref(db, texts: list[str], text: str) -> str:
    if text not in texts:
        ET.SubElement(db, "Effect").text = text
        texts.append(text)
    return str(texts.index(text))


def _palette_ref(root) -> str:
    palettes = root.find("ColorPalettes")
    if palettes is None:
        palettes = ET.Element("ColorPalettes")
        root.insert(0, palettes)
    current = palettes.findall("ColorPalette")
    if not current:
        ET.SubElement(palettes, "ColorPalette").text = WHITE_PALETTE
        return "0"
    for i, entry in enumerate(current):
        if "#FFFFFF" in (entry.text or "").upper():
            return str(i)
    ET.SubElement(palettes, "ColorPalette").text = WHITE_PALETTE
    return str(len(current))


def _transform_effect(effect, stats, db, settings, palette_fallback: str, palette_count: int):
    name = (effect.get("name") or "").strip()
    if name == "On":
        stats["On_preserved"] += 1
    elif name == "Ramp":
        effect.set("name", "On")
        effect.set("ref", _setting_ref(db, settings, FADE_SETTINGS))
        stats["Ramp_to_On_fade"] += 1
    elif name == "Strobe":
        effect.set("name", "Shimmer")
        effect.set("ref", _setting_ref(db, settings, SHIMMER_SETTINGS))
        stats["Strobe_to_Shimmer"] += 1
    elif name in AC_EFFECTS:
        stats[f"{name}_preserved"] += 1
    else:
        # Timings and spatial choreography are retained; only unsafe effect
        # vocabulary is conservatively replaced by steady intensity.
        effect.set("name", "On")
        effect.set("ref", _setting_ref(db, settings, ON_SETTINGS))
        stats["unsupported_to_On"] += 1
        stats[f"converted:{name or '<missing>'}"] += 1
    raw_palette = effect.get("palette")
    if raw_palette is None or not raw_palette.isdecimal() or int(raw_palette) >= palette_count:
        effect.set("palette", palette_fallback)
        stats["missing_palettes_fixed"] += 1
    raw_ref = effect.get("ref")
    if raw_ref is None or not raw_ref.isdecimal() or int(raw_ref) >= len(settings):
        effect.set("ref", _setting_ref(db, settings, ON_SETTINGS if effect.get("name") == "On" else ""))
        stats["missing_settings_fixed"] += 1


def enforce_lor_xsq(source: Path, dest: Path, layout: Path) -> dict:
    """Build new xLights XSQ; never edit the input/template or layout in place."""
    source, dest, layout = Path(source), Path(dest), Path(layout)
    if source.resolve() == dest.resolve():
        raise ValueError("Cannot overwrite source XSQ in LOR sanitizer")
    safe, other, groups = ac_layout_targets(layout)
    tree = ET.parse(source)
    root = tree.getroot()
    effects = root.find("ElementEffects")
    if effects is None:
        raise ValueError("XSQ has no ElementEffects")
    stats = Counter()
    db, settings = _resolve_settings(root)
    default_palette = _palette_ref(root)
    palette_count = len(root.findall("./ColorPalettes/ColorPalette"))
    all_known = safe | other
    used_models: set[str] = set()
    removed_rows: list[str] = []
    # Group targets are expanded only when they include unsupported RGB props;
    # all-AC groups retain their original compact effect layering and timing.
    for row in list(effects.findall("Element")):
        if row.get("type") == "timing":
            continue
        target = (row.get("name") or "").strip()
        targets = _safe_leaves(target, safe, groups)
        all_targets = _all_leaves(target, all_known, groups)
        if not targets or (target not in safe and target not in groups):
            removed_rows.append(target)
            effects.remove(row)
            stats["unmapped_or_rgb_rows_removed"] += 1
            continue
        if all_targets <= safe:
            for layer in row.findall("EffectLayer"):
                for effect in layer.findall("Effect"):
                    _transform_effect(effect, stats, db, settings, default_palette, palette_count)
                    stats["effects_retained"] += 1
            used_models.update(targets)
            continue
        # Mixed RGB+AC groups cannot remain as-is: they would light RGB data.
        for leaf in sorted(targets):
            cloned = copy.deepcopy(row)
            cloned.set("name", leaf)
            for layer in cloned.findall("EffectLayer"):
                for effect in layer.findall("Effect"):
                    _transform_effect(effect, stats, db, settings, default_palette, palette_count)
                    stats["effects_retained"] += 1
            effects.append(cloned)
            used_models.add(leaf)
        removed_rows.append(target)
        effects.remove(row)
        stats["mixed_groups_expanded"] += 1

    if not stats["effects_retained"]:
        raise ValueError(
            "No compatible single-color lighting effects remain. "
            "Check the AC layout and XSQ model names."
        )
    # Prevent duplicate effect IDs when cloning group layers.
    ids = 1
    for row in effects.findall("Element"):
        if row.get("type") == "timing":
            continue
        for event in row.findall("./EffectLayer/Effect"):
            event.set("id", str(ids))
            ids += 1
    nextid = root.find("nextid")
    if nextid is not None:
        nextid.text = str(ids)
    displays = root.find("DisplayElements")
    if displays is not None:
        for row in list(displays.findall("Element")):
            if row.get("type") == "timing":
                continue
            name = row.get("name", "")
            if name not in safe and not (_all_leaves(name, all_known, groups) <= safe
                                        and _all_leaves(name, all_known, groups)):
                displays.remove(row)
        present = {row.get("name") for row in displays.findall("Element")}
        for name in sorted(used_models):
            if name not in present:
                ET.SubElement(displays, "Element", {
                    "type": "model", "name": name, "visible": "1", "collapsed": "0"
                })
    # Opaque render layers are not AC sequences and may carry RGB data.
    data_layers = root.find("DataLayers")
    if data_layers is not None and list(data_layers):
        stats["data_layers_removed"] += len(data_layers)
        data_layers.clear()
    forbidden = []
    for row in effects.findall("Element"):
        if row.get("type") == "timing":
            continue
        for event in row.findall("./EffectLayer/Effect"):
            if event.get("name") not in AC_EFFECTS:
                forbidden.append(event.get("name"))
    if forbidden:
        raise ValueError(f"Forbidden effects survived LOR filter: {forbidden[:8]}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tree.write(dest, encoding="utf-8", xml_declaration=True)
    return {
        "format": "xLights XSQ for LOR via xLights (not an LMS file)",
        "allowed_effects": sorted(AC_EFFECTS),
        "layout_single_color_models": len(safe),
        "layout_non_ac_models": len(other),
        "used_single_color_models": len(used_models),
        "removed_rows": removed_rows[:60],
        "counts": dict(stats),
        "native_xlights_import_verified": False,
        "lor_conversion_verified": False,
    }


def inspect_lor_xsq(xsq: Path, layout: Path) -> dict:
    """Strict final assertion: all lighting rows/effects fit the AC contract."""
    safe, other, groups = ac_layout_targets(layout)
    root = ET.parse(xsq).getroot()
    bad = []
    count = 0
    for row in root.findall("./ElementEffects/Element"):
        if row.get("type") == "timing":
            continue
        target = row.get("name", "")
        if target not in safe and (
            target not in groups or not _all_leaves(target, safe | other, groups) <= safe
        ):
            bad.append(f"not AC target: {target}")
        for event in row.findall("./EffectLayer/Effect"):
            count += 1
            if event.get("name") not in AC_EFFECTS:
                bad.append(f"not AC effect: {target}/{event.get('name')}")
    return {"valid": not bad and count > 0, "effect_count": count,
            "issues": bad[:50]}


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("xsq", type=Path)
    p.add_argument("--layout", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(enforce_lor_xsq(args.xsq, args.output, args.layout), indent=2))


if __name__ == "__main__":
    main()
