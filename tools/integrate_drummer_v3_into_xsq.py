from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from audio.drum_detection import detect_drum_event_streams_from_file
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_components, resolve_drum_streams

DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER"
DRUMMER_TARGETS = set(DRUMMER_COMPONENTS)


def _find_or_create_element_effects(root):
    return root.find("ElementEffects") or ET.SubElement(root, "ElementEffects")


def _element_map(container):
    return {e.get("name", ""): e for e in container.findall("Element") if e.get("name")}


def _layer_for(container, elements, name, layer_name):
    element = elements.get(name)
    if element is None:
        element = ET.SubElement(container, "Element", {"type": "model", "name": name})
        elements[name] = element
    for layer in element.findall("EffectLayer"):
        if layer.get("name") == layer_name:
            return layer
    return ET.SubElement(element, "EffectLayer", {"name": layer_name, "visible": "1"})


def _clear_layer(layer):
    for child in list(layer):
        layer.remove(child)


def _add_on(layer, start_ms, end_ms, intensity, component, source_type):
    ET.SubElement(layer, "Effect", {
        "name": "On", "startTime": str(max(0, int(start_ms))),
        "endTime": str(max(int(start_ms) + 50, int(end_ms))),
        "settings": f"E_CHECKBOX_OverlayBkg=0,E_SLIDER_Brightness={max(.08, min(1., float(intensity))):.3f}",
        "palette": "C_BUTTON_Palette1=#FFFFFF,C_BUTTON_Palette2=#FFFFFF,C_BUTTON_Palette3=#FFFFFF",
        "source": "HelixDrummerV3", "sourceModel": DRUMMER_V3_MODEL,
        "sourceComponent": component, "sourceDrumType": source_type,
    })


def inject_drummer_v3(base_xsq, output_xsq, audio_path, *, layer_name="AUTO_Drummer_V3"):
    base_xsq, output_xsq, audio_path = Path(base_xsq), Path(output_xsq), Path(audio_path)
    if not base_xsq.exists() or not audio_path.exists():
        raise FileNotFoundError("Missing XSQ or audio input")

    streams = detect_drum_event_streams_from_file(audio_path)
    resolved = resolve_drum_streams(streams)
    component_events = map_events_to_drummer_components(resolved["events"])

    if output_xsq.resolve() != base_xsq.resolve():
        output_xsq.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base_xsq, output_xsq)

    tree = ET.parse(output_xsq)
    root = tree.getroot()
    container = _find_or_create_element_effects(root)
    elements = _element_map(container)
    layers = {}
    for name in sorted(DRUMMER_TARGETS):
        layers[name] = _layer_for(container, elements, name, layer_name)
        _clear_layer(layers[name])

    placements = 0
    for event in component_events:
        component = str(event["component"])
        if component not in DRUMMER_TARGETS:
            raise ValueError(f"Non-canonical drummer target emitted: {component}")
        _add_on(layers[component], event["timestamp_ms"], event["end_ms"], event["intensity"], component, event["drum_type"])
        placements += 1

    if layer_name not in {n.get("name") for n in root.findall("timingtrack")}:
        ET.SubElement(root, "timingtrack", {"name": layer_name})

    ET.indent(tree, space="  ")
    tree.write(output_xsq, encoding="utf-8", xml_declaration=True)
    drum_type_counts = {key.removesuffix("_events"): len(streams.get(key, [])) for key in streams}
    component_counts = {component: sum(1 for event in component_events if event["component"] == component) for component in sorted(DRUMMER_TARGETS)}
    typed_count = sum(v for k, v in drum_type_counts.items() if k != "drum_bus")
    bus_count = drum_type_counts.get("drum_bus", 0)
    return {
        "schema": "helix.drummer_v3_xsq_integration.v4",
        "model": DRUMMER_V3_MODEL, "base_xsq": str(base_xsq),
        "output_xsq": str(output_xsq), "audio": str(audio_path),
        "layer": layer_name, "fallback_mode": resolved["fallback_mode"],
        "event_count": len(component_events), "placement_count": placements,
        "drum_type_counts": drum_type_counts,
        "typed_event_count": typed_count,
        "drum_bus_event_count": bus_count,
        "drum_bus_ratio": round(bus_count / max(1, typed_count + bus_count), 4),
        "component_counts": component_counts,
        "targets": sorted(DRUMMER_TARGETS),
        "target_count": len(DRUMMER_TARGETS),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("base_xsq", type=Path); p.add_argument("audio", type=Path)
    p.add_argument("--output", type=Path, required=True); p.add_argument("--layer", default="AUTO_Drummer_V3")
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    report = inject_drummer_v3(a.base_xsq, a.output, a.audio, layer_name=a.layer)
    print(json.dumps(report, indent=2, sort_keys=True))
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
