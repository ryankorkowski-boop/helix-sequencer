from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from audio.audio_intelligence_orchestrator import build_musical_event_map
from mapping.drum_mapper import map_events_to_drummer_v3_poses, normalized_events_to_drum_streams, resolve_drum_streams

DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_CHANNELS = {
    257: "HX_DRUMMER_CH01_KICK", 258: "HX_DRUMMER_CH02_SNARE",
    259: "HX_DRUMMER_CH03_HIHAT", 260: "HX_DRUMMER_CH04_TOM",
    261: "HX_DRUMMER_CH05_CYMBAL", 262: "HX_DRUMMER_CH06_LEFT_STICK",
    263: "HX_DRUMMER_CH07_RIGHT_STICK", 264: "HX_DRUMMER_CH08_BODY_IMPACT",
}
POSE_CHANNELS = {
    "kick_hit": (257, 264), "snare_hit": (258, 262, 263),
    "hi_hat_pulse": (259, 262), "left_tom_hit": (260, 262),
    "right_tom_hit": (260, 263), "left_crash": (261, 262),
    "right_crash": (261, 263), "both_crash": (261, 262, 263),
    "downbeat_impact": (264, 257, 258, 261, 262, 263),
}

def _find_or_create_element_effects(root):
    container = root.find("ElementEffects")
    return container if container is not None else ET.SubElement(root, "ElementEffects")

def _element_map(container):
    return {e.get("name",""): e for e in container.findall("Element") if e.get("name")}

def _layer_for(container, elements, name, layer_name):
    element = elements.get(name)
    if element is None:
        element = ET.SubElement(container, "Element", {"type":"model","name":name})
        elements[name] = element
    for layer in element.findall("EffectLayer"):
        if layer.get("name") == layer_name:
            return layer
    return ET.SubElement(element, "EffectLayer", {"name":layer_name,"visible":"1"})

def _clear_layer(layer):
    for child in list(layer):
        layer.remove(child)

def _add_on(layer, start_ms, end_ms, intensity, pose, source_type):
    ET.SubElement(layer, "Effect", {
        "name":"On","startTime":str(max(0,int(start_ms))),
        "endTime":str(max(int(start_ms)+50,int(end_ms))),
        "settings":f"E_CHECKBOX_OverlayBkg=0,E_SLIDER_Brightness={max(.08,min(1.,float(intensity))):.3f}",
        "palette":"C_BUTTON_Palette1=#FFFFFF,C_BUTTON_Palette2=#FFFFFF,C_BUTTON_Palette3=#FFFFFF",
        "source":"HelixDrummerV3","sourceModel":DRUMMER_V3_MODEL,
        "sourcePose":pose,"sourceDrumType":source_type,
    })

def inject_drummer_v3(base_xsq, output_xsq, audio_path, *, layer_name="AUTO_Drummer_V3"):
    base_xsq, output_xsq, audio_path = Path(base_xsq), Path(output_xsq), Path(audio_path)
    if not base_xsq.exists() or not audio_path.exists():
        raise FileNotFoundError("Missing XSQ or audio input")
    musical_events = build_musical_event_map(audio_path)
    streams = normalized_events_to_drum_streams(musical_events.events)
    resolved = resolve_drum_streams(streams)
    pose_events = map_events_to_drummer_v3_poses(resolved["events"])
    if output_xsq.resolve() != base_xsq.resolve():
        output_xsq.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(base_xsq, output_xsq)
    tree = ET.parse(output_xsq); root = tree.getroot()
    container = _find_or_create_element_effects(root); elements = _element_map(container)
    layers = {}
    for channel, name in DRUMMER_CHANNELS.items():
        layers[channel] = _layer_for(container,elements,name,layer_name); _clear_layer(layers[channel])
    by_pose=0
    for event in pose_events:
        pose=str(event["pose"]); channels=POSE_CHANNELS.get(pose,(264,))
        for channel in channels:
            _add_on(layers[channel],int(event["timestamp_ms"]),int(event["end_ms"]),float(event["intensity"]),pose,str(event["drum_type"]))
            by_pose += 1
    if layer_name not in {n.get("name") for n in root.findall("timingtrack")}:
        ET.SubElement(root,"timingtrack",{"name":layer_name})
    ET.indent(tree,space="  "); tree.write(output_xsq,encoding="utf-8",xml_declaration=True)
    return {"schema":"helix.drummer_v3_xsq_integration.v1","model":DRUMMER_V3_MODEL,
            "base_xsq":str(base_xsq),"output_xsq":str(output_xsq),"audio":str(audio_path),
            "audio_intelligence": musical_events.diagnostics,
            "layer":layer_name,"fallback_mode":resolved["fallback_mode"],"event_count":len(pose_events),
            "placement_count":by_pose,
            "pose_counts":{pose:sum(1 for event in pose_events if event["pose"]==pose) for pose in POSE_CHANNELS},
            "channels":DRUMMER_CHANNELS}

def main():
    p=argparse.ArgumentParser(); p.add_argument("base_xsq",type=Path); p.add_argument("audio",type=Path)
    p.add_argument("--output",type=Path,required=True); p.add_argument("--layer",default="AUTO_Drummer_V3")
    p.add_argument("--report",type=Path)
    a=p.parse_args(); report=inject_drummer_v3(a.base_xsq,a.output,a.audio,layer_name=a.layer)
    print(json.dumps(report,indent=2,sort_keys=True))
    if a.report: a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
