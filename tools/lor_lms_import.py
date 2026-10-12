"""Import a legacy LOR LMS as an authoritative channel list for Helix.

Never guess a LOR unit/circuit from channel order: this adapter keeps the
source's actual deviceType/unit/circuit/savedIndex, and creates a temporary
virtual xLights-compatible workspace only to reuse Helix's audio engine.
This module deliberately does not parse proprietary S5/S6 .loredit files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def _source_channels(source: Path):
    source = Path(source)
    if source.suffix.lower() != ".lms":
        raise ValueError(
            "LOR input must be a legacy .lms sequence. Modern .loredit "
            "is not supported; export a legacy LMS from LOR first."
        )
    root = ET.parse(source).getroot()
    if root.tag != "sequence" or root.find("channels") is None:
        raise ValueError("Not an LMS <sequence> with <channels>")
    names, circuits, indices = set(), set(), set()
    result = []
    for channel in root.findall("./channels/channel"):
        device = (channel.get("deviceType") or "").strip().upper()
        if device != "LOR":
            continue  # Unsupported proprietary or other controller type
        unit, circuit = tuple(
            (channel.get(k) or "").strip() for k in ("unit", "circuit")
        )
        if not unit.isdecimal() or not circuit.isdecimal():
            raise ValueError("LMS LOR channel has no numeric Unit ID/Circuit")
        if int(unit) <= 0 or int(circuit) <= 0:
            raise ValueError("LMS LOR channel has nonpositive Unit ID/Circuit")
        if (int(unit), int(circuit)) in circuits:
            raise ValueError(f"Duplicate LOR Unit/Circuit: {unit}/{circuit}")
        circuits.add((int(unit), int(circuit)))
        saved_index = (channel.get("savedIndex") or "").strip()
        if not saved_index.isdecimal() or saved_index in indices:
            raise ValueError("LMS savedIndex is absent or duplicated")
        indices.add(saved_index)
        native_name = (channel.get("name") or "").strip() or f"Unit {unit} Circuit {circuit}"
        # Namespace by channel address to avoid repeating labels in layout.
        sanitized = re.sub(r"[,\r\n\t]+", " ", native_name)
        model = f"{sanitized} [LOR U{unit} C{circuit}]"
        if model in names:
            raise ValueError(f"Ambiguous LOR model identity: {model}")
        names.add(model)
        result.append({
            "model": model,
            "name": native_name,
            "unit": int(unit),
            "circuit": int(circuit),
            "savedIndex": saved_index,
            "color": channel.get("color") or "16777215",
        })
    if not result:
        raise ValueError(
            "LMS contains no supported LOR channels with explicit Unit/Circuit. "
            "Supply an LMS exported from the actual LOR show."
        )
    return root, result


def prepare_lms_workspace(source: Path, workspace: Path) -> dict:
    """Write generated model geometry + template under a dedicated workspace."""
    source, workspace = Path(source), Path(workspace)
    root, channels = _source_channels(source)
    workspace.mkdir(parents=True, exist_ok=True)
    layout = workspace / "xlights_rgbeffects.xml"
    template = workspace / "lor_virtual_template.xsq"
    root_layout = ET.Element("xrgb")
    models = ET.SubElement(root_layout, "models")
    # Deterministic grid visualization only. LMS does not supply prop geometry.
    columns = 16
    for i, entry in enumerate(channels):
        try:
            lor_color = int(entry["color"])
        except ValueError:
            lor_color = 0xFFFFFF
        # LOR stores its display swatch as 0xBBGGRR. This is an indication
        # of appearance for the virtual channel-grid preview, NOT proof of
        # the type of bulb actually wired to the unit/circuit.
        rr = lor_color & 255
        gg = (lor_color >> 8) & 255
        bb = (lor_color >> 16) & 255
        if rr > 0 and not gg and not bb:
            string_type = "Single Color Red"
        elif gg > 0 and not rr and not bb:
            string_type = "Single Color Green"
        elif rr == gg == bb and rr > 0:
            string_type = "Single Color White"
        else:
            string_type = "Single Color Intensity"
        ET.SubElement(models, "model", {
            "name": entry["model"], "DisplayAs": "Single Line",
            "StringType": string_type, "StartChannel": str(i + 1),
            "CustomColor": f"#{rr:02X}{gg:02X}{bb:02X}",
            "parm1": "1", "parm2": "1", "parm3": "1",
            "WorldPosX": str((i % columns) * 40),
            "WorldPosY": str((i // columns) * 40),
            "WorldPosZ": "0", "ModelBrightness": "100",
        })
    groups = ET.SubElement(root_layout, "modelGroups")
    ET.SubElement(groups, "modelGroup", {
        "name": "01_ALL", "models": ",".join(x["model"] for x in channels),
    })
    ET.ElementTree(root_layout).write(layout, encoding="utf-8", xml_declaration=True)

    sequence = ET.Element("xsequence", {
        "BaseChannel": "0", "ChanCtrlBasic": "0",
        "ChanCtrlColor": "0", "FixedPointTiming": "1",
    })
    head = ET.SubElement(sequence, "head")
    ET.SubElement(head, "sequenceType").text = "Media"
    ET.SubElement(head, "sequenceTiming").text = "50 ms"
    ET.SubElement(head, "sequenceDuration").text = "1"
    ET.SubElement(head, "mediaFile").text = ""
    ET.SubElement(sequence, "nextid").text = "1"
    ET.SubElement(sequence, "ColorPalettes")
    db = ET.SubElement(sequence, "EffectDB")
    ET.SubElement(db, "Effect").text = (
        "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"
    )
    ET.SubElement(sequence, "DataLayers")
    displayed = ET.SubElement(sequence, "DisplayElements")
    element_effects = ET.SubElement(sequence, "ElementEffects")
    for entry in channels:
        ET.SubElement(displayed, "Element", {
            "type": "model", "name": entry["model"],
            "visible": "1", "collapsed": "0",
        })
        row = ET.SubElement(element_effects, "Element", {
            "type": "model", "name": entry["model"],
        })
        ET.SubElement(row, "EffectLayer")
    ET.ElementTree(sequence).write(template, encoding="utf-8", xml_declaration=True)
    manifest = workspace / "lor_import_manifest.json"
    payload = {
        "schema": "helix.lor_import.v1",
        "source_lms_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_lms_name": source.name,
        "channels": channels,
        "layout": str(layout),
        "template": str(template),
        "geometry": "synthetic 16-column channel grid; no physical coordinates in LMS",
    }
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {**payload, "manifest": str(manifest)}
