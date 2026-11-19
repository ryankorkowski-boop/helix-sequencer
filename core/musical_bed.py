"""Fill long dark gaps with a dim, section-energy bed.

Hit effects stay in place. The bed is only written into gaps and at a much
lower level, so pulses still read as the bright events.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from xlights.layer_blend import blend_settings, stamp_native_blends


# Dark blue, not white. Real sequences resolve Effect palette="N" against
# ColorPalettes. An inline C_BUTTON string is not a palette index, so xLights
# falls through to palette 0, which is white on the shipped templates.
BED_PALETTE = "C_BUTTON_Palette1=#1A2744,C_CHECKBOX_Palette1=1"


def bed_intervals(hits: list[tuple[int, int]], duration_ms: int, *, min_gap_ms: int = 700) -> list[tuple[int, int]]:
    """Return gaps between hits that are long enough for a dim bed."""
    cursor = 0
    gaps = []
    for start, end in sorted(hits):
        if start - cursor >= min_gap_ms:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if duration_ms - cursor >= min_gap_ms:
        gaps.append((cursor, duration_ms))
    return gaps


def bed_level(section_energy: float) -> int:
    """12-28 percent. High enough to see, well under a hit pulse."""
    energy = max(0.0, min(1.0, float(section_energy)))
    return int(round(12 + 16 * energy))


def _bed_palette_index(root: ET.Element) -> str:
    palettes = root.find("ColorPalettes")
    if palettes is None:
        palettes = ET.Element("ColorPalettes")
        root.insert(0, palettes)
    for index, palette in enumerate(list(palettes)):
        if (palette.text or "") == BED_PALETTE:
            return str(index)
    element = ET.SubElement(palettes, "ColorPalette")
    element.text = BED_PALETTE
    return str(len(list(palettes)) - 1)


def apply_musical_bed(xsq_path: Path, duration_ms: int, section_energy: float = 0.45) -> dict:
    tree = ET.parse(xsq_path)
    root = tree.getroot()
    effects_root = root.find("./ElementEffects")
    if effects_root is None:
        return {"models": 0, "beds": 0}
    level = bed_level(section_energy)
    palette_index = _bed_palette_index(root)
    beds = 0
    models = 0
    for element in effects_root.findall("Element"):
        if (element.attrib.get("type") or "").lower() == "timing":
            continue
        layers = element.findall("EffectLayer")
        if not layers:
            continue
        models += 1
        hits = []
        for layer in layers:
            for effect in layer.findall("Effect"):
                start = int(float(effect.attrib.get("startTime", "0") or 0))
                end = int(float(effect.attrib.get("endTime", "0") or 0))
                if end > start:
                    hits.append((start, end))
        gaps = bed_intervals(hits, duration_ms)
        if not gaps:
            continue
        bed_layer = ET.Element("EffectLayer", {"name": "Helix Bed"})
        element.insert(0, bed_layer)
        for start, end in gaps:
            ET.SubElement(bed_layer, "Effect", {
                "name": "On",
                "startTime": str(start),
                "endTime": str(end),
                "settings": blend_settings(
                    f"E_TEXTCTRL_Eff_On_Start={level},E_TEXTCTRL_Eff_On_End={level}",
                    "Average",
                    canvas=False,
                ),
                "palette": palette_index,
                "source": "HelixMusicalBed",
                "label": "CANDIDATE musical bed",
            })
            beds += 1
    stamped = stamp_native_blends(root)
    tree.write(xsq_path, encoding="utf-8", xml_declaration=True)
    return {"models": models, "beds": beds, "level": level, "palette": palette_index, "blends_stamped": stamped}
