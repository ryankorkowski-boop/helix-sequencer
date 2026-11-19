"""Write pitch-specific native XSQ submodel layers without changing a layout."""
from __future__ import annotations

import math
from pathlib import Path
import xml.etree.ElementTree as ET

from core.keyboard_rung_scheduler import schedule_keyboard_rungs


def export_keyboard_rungs(source: Path, layout: Path, output: Path, cues: list[dict],
                          *, model: str = "HX_CENTER_KEYBOARD_HELIX",
                          duration: float, color: str = "#43E6FF") -> dict:
    """Append one independent native layer for each supported note.

    Only the explicitly named, RGB, 88-rung model is eligible. Existing
    sequence layers and layout bytes are retained. No controller addresses
    are generated. Cues must come from a screened pitched-note source.
    """
    if source.resolve() == layout.resolve() or output.resolve() == layout.resolve():
        raise ValueError("Sequence output must not overwrite its layout")
    root = ET.parse(source).getroot()
    definition = next((m for m in ET.parse(layout).getroot().findall("models/model")
                       if m.get("name") == model), None)
    if definition is None or definition.get("StringType") != "RGB Nodes":
        raise ValueError("Keyboard rung export requires the explicit RGB helix model")
    mapping = {str(n): f"KEY_MIDI_{n:03d}" for n in range(21, 109)}
    subs = {s.get("name"): s for s in definition.findall("subModel")}
    if any(name not in subs or not subs[name].get("line0", "").strip()
           for name in mapping.values()):
        raise ValueError("Layout lacks 88 nonempty keyboard rung submodels")
    plan = schedule_keyboard_rungs(cues, mapping, duration=duration)
    head = root.find("head")
    if head is None:
        raise ValueError("XSQ has no sequence head")
    for name, value in {"sequenceDuration": f"{duration:.3f}"}.items():
        node = head.find(name)
        if node is None:
            node = ET.SubElement(head, name)
        node.text = value
    elements = root.find("ElementEffects")
    displays = root.find("DisplayElements")
    palettes = root.find("ColorPalettes")
    db = root.find("EffectDB")
    if any(x is None for x in (elements, displays, palettes, db)):
        raise ValueError("Incomplete native XSQ effect containers")
    parent = next((e for e in elements if e.get("name") == model), None)
    if parent is None:
        parent = ET.SubElement(elements, "Element", {"type": "model", "name": model})
        ET.SubElement(displays, "Element", {"type": "model", "name": model,
                                           "visible": "1", "collapsed": "1"})
    palette_id, setting_id = len(palettes), len(db)
    ET.SubElement(palettes, "ColorPalette").text = f"C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1"
    ET.SubElement(db, "Effect").text = "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=35"
    next_id = max((int(e.get("id", "0")) for e in root.findall(".//Effect")
                   if e.get("id", "0").isdigit()), default=0) + 1
    layers = {}
    for cue in plan:
        part = cue["submodel"]
        if part not in layers:
            existing = [int(e.get("layer", "0")) for e in parent.findall("SubModelEffectLayer")
                        if e.get("name") == part]
            layers[part] = ET.SubElement(parent, "SubModelEffectLayer",
                                         {"name": part, "layer": str(max(existing, default=-1) + 1)})
        start, end = round(cue["start"] * 1000), min(math.ceil(duration * 1000), round(cue["end"] * 1000))
        if end <= start:
            continue
        ET.SubElement(layers[part], "Effect", {"name": "On", "ref": str(setting_id),
            "palette": str(palette_id), "id": str(next_id), "startTime": str(start), "endTime": str(end)})
        next_id += 1
    node = root.find("nextid")
    if node is None:
        node = ET.SubElement(root, "nextid")
    node.text = str(next_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
    return {"model": model, "events": len(plan), "active_rungs": len(layers),
            "duration": duration, "layout_modified": False, "native_playback_verified": False}
