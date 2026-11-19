"""Fill long dark gaps with a dim, section-energy bed.

Hit effects stay in place. The bed is only written into gaps and at a much
lower level, so pulses still read as the bright events.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


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


def apply_musical_bed(xsq_path: Path, duration_ms: int, section_energy: float = 0.45) -> dict:
    tree = ET.parse(xsq_path)
    root = tree.getroot()
    effects_root = root.find("./ElementEffects")
    if effects_root is None:
        return {"models": 0, "beds": 0}
    level = bed_level(section_energy)
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
        layer = layers[0]
        for start, end in bed_intervals(hits, duration_ms):
            ET.SubElement(layer, "Effect", {
                "name": "On",
                "startTime": str(start),
                "endTime": str(end),
                "settings": f"E_TEXTCTRL_Eff_On_Start={level},E_TEXTCTRL_Eff_On_End={level}",
                "palette": "C_BUTTON_Palette1=#3355AA,C_CHECKBOX_Palette1=1",
                "source": "HelixMusicalBed",
                "label": "CANDIDATE musical bed",
            })
            beds += 1
    tree.write(xsq_path, encoding="utf-8", xml_declaration=True)
    return {"models": models, "beds": beds, "level": level}
