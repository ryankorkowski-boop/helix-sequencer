"""Conservative xLights export for physical red/green/white AC circuits.

Only explicitly documented single-color strands qualify. This creates an
editable xLights XSQ containing On effects; it is NOT a Light-O-Rama LMS
or a claim of controller addressing. Use xLights and verify the controller map
before exporting/playing on real hardware.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict, Counter
from pathlib import Path
import xml.etree.ElementTree as ET
import json

COLORS = {
    "single color red": "red",
    "single color green": "green",
    "single color white": "white",
}
ON_SETTINGS = "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"
WHITE_PALETTE = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"


def inventory_layout(layout: Path):
    root = ET.parse(layout).getroot()
    models = {}
    channels = {}
    rejected = Counter()
    for node in root.findall("./models/model"):
        name = (node.get("name") or "").strip()
        string_type = (node.get("StringType") or "").strip().lower()
        channel = (node.get("StartChannel") or "").strip()
        color = COLORS.get(string_type)
        if not name or not color:
            rejected[string_type or "untyped"] += 1
            continue
        if not channel.isdigit() or int(channel) < 1:
            raise ValueError(f"AC model {name!r} has no positive numeric StartChannel. Configure it first.")
        if int(channel) in channels:
            raise ValueError(
                f"AC channel collision at {channel}: {channels[int(channel)]!r} and {name!r}. "
                "Resolve the layout mapping before AC export."
            )
        channels[int(channel)] = name
        models[name] = {"name": name, "color": color, "start_channel": int(channel),
                        "string_type": node.get("StringType", "")}
    if not models:
        raise ValueError(
            "No explicit Single Color Red/Green/White models found. "
            "AC-only mode cannot safely convert an RGB-only layout. "
            "Choose a real AC layout containing separate single-color circuits."
        )

    groups = {}
    for group in root.findall("./modelGroups/modelGroup"):
        name = (group.get("name") or "").strip()
        if name:
            groups[name] = tuple(
                part.strip() for part in (group.get("models") or "").split(",")
                if part.strip()
            )
    return models, groups, dict(rejected)


def _leaves(target, models, groups, seen=None):
    seen = seen or set()
    if target in seen:
        return ()
    if target in models:
        return (target,)
    seen = {*seen, target}
    leaves = []
    for member in groups.get(target, ()):
        leaves.extend(_leaves(member, models, groups, seen))
    return tuple(dict.fromkeys(leaves))


def _merged(intervals):
    result = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(end, result[-1][1]))
        else:
            result.append((start, end))
    return result


def export_ac_on(source: Path, layout: Path, destination: Path, *,
                 min_pulse_warning_ms: int = 100):
    """Export an XSQ with only flat On effects on eligible AC single-color models.

    Preserve all timing-track rows and song metadata. Never overwrite inputs.
    Return validation facts and resource names, not an unverified LMS file.
    """
    source, layout, destination = Path(source), Path(layout), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("Refusing to overwrite input XSQ (use another destination)")
    models, groups, excluded_types = inventory_layout(layout)
    tree = ET.parse(source)
    root = tree.getroot()
    effects_root = root.find("ElementEffects")
    if effects_root is None:
        raise ValueError("Input XSQ contains no ElementEffects")
    time_node = root.find("./head/sequenceDuration")
    duration = int(float(time_node.text) * 1000) if time_node is not None and time_node.text else None
    if duration is None or duration <= 0:
        raise ValueError("XSQ must declare a positive sequence duration")

    # Extract first, then remove ALL source model rows; no RGB/group effects,
    # shaders, backgrounds or stray layers can survive the export.
    pulses = defaultdict(list)
    excluded_effects = 0
    unmapped_targets = set()
    input_count = 0
    for element in list(effects_root.findall("Element")):
        if element.get("type", "").lower() == "timing":
            continue
        target = (element.get("name") or "").strip()
        leaves = _leaves(target, models, groups)
        for effect in element.findall("./EffectLayer/Effect"):
            input_count += 1
            if not leaves:
                excluded_effects += 1
                unmapped_targets.add(target)
                continue
            start = max(0, int(float(effect.get("startTime", "0"))))
            end = min(duration, int(float(effect.get("endTime", "0"))))
            if end <= start:
                excluded_effects += 1
                continue
            for name in leaves:
                pulses[name].append((start, end))
        effects_root.remove(element)

    if not any(pulses.values()):
        raise ValueError(
            "No incoming effects target an eligible AC model or group. "
            "Refusing to produce an empty AC sequence."
        )

    # One white intensity palette controls brightness: the physical red, green,
    # or white bulb attached to each single-color channel determines its hue.
    palette_root = root.find("ColorPalettes")
    if palette_root is None:
        palette_root = ET.Element("ColorPalettes")
        root.insert(1, palette_root)
    palette_root.clear()
    ET.SubElement(palette_root, "ColorPalette").text = WHITE_PALETTE
    db = root.find("EffectDB")
    if db is None:
        db = ET.Element("EffectDB")
        root.insert(2, db)
    db.clear()
    ET.SubElement(db, "Effect").text = ON_SETTINGS

    # Clear DataLayers referencing the original RGB/AC multi-model rendering.
    data_layers = root.find("DataLayers")
    if data_layers is not None:
        data_layers.clear()
    # Keep timing rows, but restrict visible model rows to physical AC models.
    displays = root.find("DisplayElements")
    if displays is not None:
        for element in list(displays):
            if element.get("type", "").lower() != "timing" and element.get("name") not in models:
                displays.remove(element)

    # Some templates display only parent groups. Add every emitted AC row to
    # the view, or xLights may hide valid single-channel effects.
    if displays is not None:
        displayed = {e.get("name") for e in displays.findall("Element")}
        for name in sorted(pulses):
            if name not in displayed:
                ET.SubElement(
                    displays, "Element",
                    {"collapsed": "0", "type": "model", "name": name, "visible": "1"},
                )

    next_id = 1
    short_pulses = 0
    total_pulses = 0
    active_channels = []
    for name in sorted(pulses, key=lambda n: (models[n]["start_channel"], n)):
        intervals = _merged(pulses[name])
        if not intervals:
            continue
        active_channels.append(models[name])
        element = ET.SubElement(effects_root, "Element", {"type": "model", "name": name})
        layer = ET.SubElement(element, "EffectLayer", {"name": "HELIX_AC_ON", "visible": "1"})
        for start, end in intervals:
            ET.SubElement(layer, "Effect", {"name": "On", "startTime": str(start),
                          "endTime": str(end), "palette": "0", "ref": "0", "id": str(next_id)})
            next_id += 1
            total_pulses += 1
            if end - start < min_pulse_warning_ms:
                short_pulses += 1
    nextid = root.find("nextid")
    if nextid is not None:
        nextid.text = str(next_id)

    # Make invalid color settings/effect targets a hard export failure.
    emitted = root.findall("./ElementEffects/Element[@type='model']/EffectLayer/Effect")
    assert len(emitted) == total_pulses
    assert all(e.get("name") == "On" and e.get("palette") == "0" and e.get("ref") == "0"
               for e in emitted)

    destination.parent.mkdir(parents=True, exist_ok=True)
    tree.write(destination, encoding="utf-8", xml_declaration=True)

    map_path = destination.with_suffix(".ac_channel_map.csv")
    with map_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["model", "color", "xlights_start_channel",
                          "controller_unit", "controller_circuit", "string_type"])
        writer.writeheader()
        for model in active_channels:
            writer.writerow({
                "model": model["name"], "color": model["color"],
                "xlights_start_channel": model["start_channel"],
                "controller_unit": "", "controller_circuit": "",
                "string_type": model["string_type"]
            })
    report = {
        "output": str(destination), "channel_map": str(map_path),
        "format": "xLights XSQ with On only; NOT LOR LMS",
        "output_effects": total_pulses, "active_ac_channels": len(active_channels),
        "input_effects": input_count, "excluded_input_effects": excluded_effects,
        "excluded_model_types": excluded_types,
        "unmapped_targets": sorted(unmapped_targets),
        "short_pulses_under_ms": min_pulse_warning_ms,
        "short_pulse_count": short_pulses,
        "requires_manual_lor_unit_circuit_mapping": True,
        "native_xlights_render_verified": False,
        "lor_hardware_verified": False,
    }
    report_path = destination.with_suffix(".ac_validation.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_xsq", type=Path)
    parser.add_argument("--layout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_ac_on(args.input_xsq, args.layout, args.output), indent=2))


if __name__ == "__main__":
    main()
