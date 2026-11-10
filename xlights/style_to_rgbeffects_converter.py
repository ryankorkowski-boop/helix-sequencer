"""Convert Helix Style Engine effect rows into xLights RGB effects XML.

This module is the first native-shaped xLights conversion path for the Style
Engine pipeline. It intentionally writes a focused, deterministic RGB effects
artifact instead of mutating existing legacy files in place.
"""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from xlights.style_xsq_bridge import validate_xsq_effect_rows


XLIGHTS_EFFECT_NAME_MAP = {
    "beat_pulse": "On",
    "warm_pulse": "On",
    "center_flash": "On",
    "bass_bump": "On",
    "z_pulse": "On",
    "tight_chase": "Single Strand",
    "red_green_chase": "Single Strand",
    "slow_chase": "Single Strand",
    "rapid_chase": "Single Strand",
    "orbital_chase": "Single Strand",
    "bar_sweep": "Bars",
    "whole_house_sweep": "Bars",
    "cinematic_sweep": "Bars",
    "rainbow_sweep": "Bars",
    "helix_spiral_sweep": "Spirals",
    "white_tick_sparkle": "Twinkle",
    "gold_white_sparkle": "Twinkle",
    "starfield_sparkle": "Twinkle",
    "confetti_sparkle": "Twinkle",
    "orbital_sparkle": "Twinkle",
    "impact_burst": "Shockwave",
    "white_gold_burst": "Shockwave",
    "trailer_hit_burst": "Shockwave",
    "party_strobe_burst": "Strobe",
    "z_axis_helix_burst": "Shockwave",
    "soft_fade": "Color Wash",
    "warm_color_fade": "Color Wash",
    "slow_scene_fade": "Color Wash",
    "color_wash_fade": "Color Wash",
    "depth_fade": "Color Wash",
    "low_level_meter_texture": "VU Meter",
    "gentle_twinkle_texture": "Twinkle",
    "ambient_texture": "Color Wash",
    "moving_color_texture": "Butterfly",
    "depth_orbit_texture": "Spirals",
    "blackout": "Off",
}


def _color_string(palette: list[str]) -> str:
    return ",".join(str(color) for color in palette)


def build_xlights_rgbeffects_xml(rows: list[dict], sequence_name: str = "Helix Style Engine Output") -> ET.Element:
    """Build a deterministic xLights-facing RGB effects XML tree."""

    validate_xsq_effect_rows(rows)

    root = ET.Element("xrgb", {"version": "2026.1", "source": "helix-style-engine"})
    sequence = ET.SubElement(root, "sequence", {"name": sequence_name})
    models = ET.SubElement(sequence, "models")

    seen_models: set[str] = set()
    for row in rows:
        model = str(row["model"])
        if model not in seen_models:
            ET.SubElement(models, "model", {"name": model})
            seen_models.add(model)

    effects = ET.SubElement(sequence, "effects")
    for index, row in enumerate(rows):
        native_effect = XLIGHTS_EFFECT_NAME_MAP.get(str(row["effect"]), "On")
        attrs = {
            "id": str(index + 1),
            "model": str(row["model"]),
            "startTime": f"{float(row['start']):.3f}",
            "endTime": f"{float(row['start']) + float(row['duration']):.3f}",
            "duration": f"{float(row['duration']):.3f}",
            "effect": native_effect,
            "helixEffect": str(row["effect"]),
            "intent": str(row["intent"]),
            "palette": _color_string(list(row["palette"])),
            "intensity": f"{float(row['intensity']):.3f}",
        }
        if row.get("motion") is not None:
            attrs["motion"] = str(row["motion"])
        ET.SubElement(effects, "effect", attrs)

    return root


def write_xlights_rgbeffects_xml(rows: list[dict], output_path: str | Path, sequence_name: str = "Helix Style Engine Output") -> Path:
    """Write xLights-facing RGB effects XML from Style Engine effect rows."""

    root = build_xlights_rgbeffects_xml(rows, sequence_name=sequence_name)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path
