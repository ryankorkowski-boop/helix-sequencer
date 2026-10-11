"""Non-destructive xLights XSQ palette assignment and optional compatibility export.

This module does not alter musical timing, effect targets, model definitions, or
sequencing logic. The source must differ from the destination.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

NEON_SCENES = (
    ("#FF2ED1", "#00D9FF", "#6448FF"),
    ("#19FFAD", "#005BFF", "#FC32B3"),
    ("#FF7518", "#F8F000", "#FF2E63"),
    ("#26F7FD", "#BC47FF", "#4CFF6C"),
    ("#FF3162", "#27B8FF", "#FFF06C"),
    ("#AD5BFF", "#00F6FF", "#FF4AB9"),
)
FADE_SETTINGS = "E_TEXTCTRL_Eff_On_Start=25,E_TEXTCTRL_Eff_On_End=100"


def _palette(colors):
    return ",".join(
        [f"C_BUTTON_Palette{i}={c}" for i, c in enumerate(colors, 1)]
        + [f"C_CHECKBOX_Palette{i}=1" for i in range(1, len(colors) + 1)]
    )


def _model_effects(root):
    for row in root.findall("./ElementEffects/Element"):
        if row.get("type") != "model":
            continue
        for layer in row.findall("EffectLayer"):
            for effect in layer.findall("Effect"):
                yield row, layer, effect


def _sections(root):
    for row in root.findall("./ElementEffects/Element"):
        if row.get("type") != "timing" or "parts" not in (row.get("name") or "").lower():
            continue
        out = []
        for e in row.findall("./EffectLayer/Effect"):
            try:
                start, end = int(e.get("startTime", "0")), int(e.get("endTime", "0"))
                if end > start:
                    out.append((start, end, (e.get("label") or "").upper()))
            except ValueError:
                pass
        if out:
            return out
    return []


def _scene(target, effect, sections):
    start = int(effect.get("startTime", "0"))
    middle = (start + int(effect.get("endTime", "0"))) // 2
    section = next((name for lo, hi, name in sections if lo <= middle < hi), "")
    if "CHORUS" in section or "DROP" in section:
        return (2 + (start // 30000) % 2) % len(NEON_SCENES)
    if "BRIDGE" in section:
        return 3
    if "PRECHORUS" in section or "BUILD" in section:
        return 4
    family = target.split("/")[0]
    stable_hash = int.from_bytes(hashlib.sha256(family.encode("utf-8")).digest()[:8], "big")
    return (stable_hash + start // 8000) % len(NEON_SCENES)


def repair_xsq(source, destination, *, palette_mode="neon", portable=False, media_file=None):
    """Fill missing palette refs; leave explicitly colored effects untouched.

    portable=True explicitly converts unsupported sample-run effects and removes
    missing-resource Pictures/Text effects. This is never the implicit default.
    """
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("Refusing to overwrite an input XSQ")
    if palette_mode != "neon":
        raise ValueError("Only explicit palette_mode='neon' is supported")

    tree = ET.parse(source)
    root = tree.getroot()
    palette_root = root.find("ColorPalettes")
    if palette_root is None:
        palette_root = ET.Element("ColorPalettes")
        root.insert(1, palette_root)
    original_palettes = [e.text or "" for e in palette_root.findall("ColorPalette")]
    palette_map = {p: i for i, p in enumerate(original_palettes)}
    for colors in NEON_SCENES:
        pal = _palette(colors)
        if pal not in palette_map:
            palette_map[pal] = len(palette_map)
            ET.SubElement(palette_root, "ColorPalette").text = pal

    db = root.find("EffectDB")
    if db is None:
        db = ET.Element("EffectDB")
        root.insert(2, db)
    settings = [e.text or "" for e in db.findall("Effect")]

    def ref_for(setting):
        if setting in settings:
            return settings.index(setting)
        index = len(settings)
        ET.SubElement(db, "Effect").text = setting
        settings.append(setting)
        return index

    default_ref = ref_for("")
    fade_ref = ref_for(FADE_SETTINGS) if portable else default_ref
    sections = _sections(root)
    duration_text = root.findtext("./head/sequenceDuration")
    duration_ms = round(float(duration_text) * 1000) if duration_text else None
    used_ids = [int(e.get("id")) for _, _, e in _model_effects(root)
                if (e.get("id") or "").isdigit()]
    next_id = max(used_ids, default=0) + 1
    stats = Counter()

    for row, layer, effect in list(_model_effects(root)):
        name = effect.get("name", "")
        if portable and name in {"Pictures", "Text"}:
            layer.remove(effect)
            stats["omitted_resource_dependent"] += 1
            continue
        if portable and name == "Ramp":
            effect.set("name", "On")
            effect.set("ref", str(fade_ref))
            stats["ramp_converted_to_on_fade"] += 1
        if portable and name == "Single Strand":
            effect.set("name", "SingleStrand")
            stats["effect_names_normalized"] += 1
        if portable and duration_ms is not None and int(effect.get("endTime", "0")) > duration_ms:
            effect.set("endTime", str(duration_ms))
            stats["end_times_clipped"] += 1
        if effect.get("ref") is None:
            effect.set("ref", str(default_ref))
            stats["settings_refs_added"] += 1
        if effect.get("palette") is None:
            index = _scene(row.get("name", ""), effect, sections)
            effect.set("palette", str(palette_map[_palette(NEON_SCENES[index])]))
            stats["palettes_assigned"] += 1
        else:
            stats["original_palette_refs_preserved"] += 1
        if effect.get("id") is None:
            effect.set("id", str(next_id))
            next_id += 1
            stats["ids_added"] += 1

    nextid_node = root.find("nextid")
    if nextid_node is not None:
        nextid_node.text = str(max(next_id, int(nextid_node.text or "1")))
    if media_file is not None:
        media = root.find("./head/mediaFile")
        if media is not None:
            media.text = media_file

    palette_count = len(palette_root.findall("ColorPalette"))
    effects = list(_model_effects(root))
    for _, _, e in effects:
        if not 0 <= int(e.get("palette", "-1")) < palette_count:
            raise ValueError("Invalid palette reference in output")
        if not 0 <= int(e.get("ref", "-1")) < len(settings):
            raise ValueError("Invalid settings reference in output")
        if int(e.get("endTime", "0")) <= int(e.get("startTime", "0")):
            raise ValueError("Invalid effect interval")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tree.write(destination, encoding="utf-8", xml_declaration=True)
    return {
        "source": str(source), "destination": str(destination),
        "portable": portable, "palette_count": palette_count,
        "preserved_template_palettes": len(original_palettes),
        "effects_after": len(effects), "changes": dict(stats),
        "native_xlights_import_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--palette-mode", choices=["neon"], default="neon")
    parser.add_argument("--portable", action="store_true")
    parser.add_argument("--media-file")
    args = parser.parse_args()
    print(json.dumps(repair_xsq(args.source, args.destination, palette_mode=args.palette_mode,
                               portable=args.portable, media_file=args.media_file), indent=2))


if __name__ == "__main__":
    main()
