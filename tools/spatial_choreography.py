"""Optional geometric chorus-onset accents over an existing Helix XSQ.

This is a deliberately small, additive pass. It never rewrites the core audio
engine or existing effect layers. Each detected chorus gets a left-to-right
accent across actual RGB leaf models, timed within a musical transition.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import json


def add_spatial_accents(xsq: Path, layout: Path, output: Path, *,
                        spread_ms: int = 720, pulse_ms: int = 170,
                        max_sections: int = 8):
    xsq, layout, output = Path(xsq), Path(layout), Path(output)
    if xsq.resolve() == output.resolve():
        raise ValueError("Spatial accent pass requires a distinct output path")
    root = ET.parse(xsq).getroot()
    layout_root = ET.parse(layout).getroot()
    candidates = []
    for m in layout_root.findall("./models/model"):
        name = m.get("name", "")
        kind = (m.get("StringType") or "").lower()
        if not name or not kind.startswith("rgb"):
            continue
        try:
            x = float(m.get("WorldPosX", "0"))
        except ValueError:
            continue
        candidates.append((x, name))
    candidates.sort()
    # A one- or two-prop display cannot visibly form a spatial chase.
    if len(candidates) < 3:
        report = {"added": 0, "reason": "fewer than three RGB leaf models"}
        return report
    sections = []
    for track in root.findall("./ElementEffects/Element[@type='timing']"):
        if "parts" not in (track.get("name") or "").lower():
            continue
        for effect in track.findall("./EffectLayer/Effect"):
            label = (effect.get("label") or "").upper()
            if "CHORUS" in label or "DROP" in label:
                sections.append(int(effect.get("startTime", "0")))
        if sections:
            break
    duration = round(float(root.findtext("./head/sequenceDuration", "0")) * 1000)
    sections = [t for t in sorted(set(sections)) if 0 <= t < duration]
    if not sections:
        return {"added": 0, "reason": "no chorus/drop timing track"}
    sections = sections[:max_sections]

    db = root.find("EffectDB")
    if db is None:
        db = ET.Element("EffectDB")
        root.insert(1, db)
    values = [e.text or "" for e in db.findall("Effect")]
    on_settings = "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"
    if on_settings in values:
        ref = values.index(on_settings)
    else:
        ref = len(values)
        ET.SubElement(db, "Effect").text = on_settings

    palettes = root.findall("./ColorPalettes/ColorPalette")
    if not palettes:
        palette_root = root.find("ColorPalettes")
        if palette_root is None:
            palette_root = ET.Element("ColorPalettes")
            root.insert(1, palette_root)
        ET.SubElement(palette_root, "ColorPalette").text = (
            "C_BUTTON_Palette1=#00D9FF,C_CHECKBOX_Palette1=1"
        )
        palettes = palette_root.findall("ColorPalette")
    colored = [i for i, p in enumerate(palettes) if "#FFFFFF" not in (p.text or "")]
    palette_index = colored[0] if colored else 0

    element_root = root.find("ElementEffects")
    if element_root is None:
        raise ValueError("Missing ElementEffects")
    by_name = {
        e.get("name"): e for e in element_root.findall("Element")
        if e.get("type") == "model"
    }
    display = root.find("DisplayElements")
    current_display = {
        e.get("name") for e in display.findall("Element")
    } if display is not None else set()
    ids = [int(e.get("id")) for e in root.findall(".//Effect") if (e.get("id") or "").isdigit()]
    next_id = max(ids, default=0) + 1

    # Space the existing physical RGB models across a <=720 ms travel.
    added = 0
    for start in sections:
        for i, (_x, name) in enumerate(candidates):
            t = start + round(i * spread_ms / max(1, len(candidates) - 1))
            end = min(duration, t + pulse_ms)
            if end <= t:
                continue
            row = by_name.get(name)
            if row is None:
                row = ET.SubElement(element_root, "Element", {"type": "model", "name": name})
                by_name[name] = row
            # Do not overlay a showpiece on the model's own existing effects.
            existing = list(row.findall("./EffectLayer/Effect"))
            if any(int(e.get("startTime", "0")) < end and
                   int(e.get("endTime", "0")) > t for e in existing):
                continue
            accent_layer = next(
                (layer for layer in row.findall("EffectLayer")
                 if layer.get("name") == "HELIX_SPATIAL_ACCENTS"), None
            )
            if accent_layer is None:
                accent_layer = ET.SubElement(
                    row, "EffectLayer", {"name": "HELIX_SPATIAL_ACCENTS", "visible": "1"}
                )
            ET.SubElement(accent_layer, "Effect", {
                "name": "On", "startTime": str(t), "endTime": str(end),
                "palette": str(palette_index), "ref": str(ref), "id": str(next_id)
            })
            next_id += 1
            added += 1
            if display is not None and name not in current_display:
                ET.SubElement(display, "Element", {"type": "model", "name": name, "visible": "1"})
                current_display.add(name)
    nextid = root.find("nextid")
    if nextid is not None:
        nextid.text = str(max(int(nextid.text or "1"), next_id))
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
    return {"added": added, "rgb_candidates": len(candidates),
            "chorus_starts": sections, "spread_ms": spread_ms,
            "note": "additive RGB model-level onset chase; does not modify existing effects"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xsq", type=Path)
    parser.add_argument("--layout", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(add_spatial_accents(args.xsq, args.layout, args.output), indent=2))


if __name__ == "__main__":
    main()
