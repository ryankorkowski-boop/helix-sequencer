from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from audio.drum_detection import detect_drum_event_streams_from_file
from mapping.drum_mapper import map_events_to_drummer_v3_poses, resolve_drum_streams

DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_CHANNELS = {
    257: "HX_DRUMMER_CH01_KICK",
    258: "HX_DRUMMER_CH02_SNARE",
    259: "HX_DRUMMER_CH03_HIHAT",
    260: "HX_DRUMMER_CH04_TOM",
    261: "HX_DRUMMER_CH05_CYMBAL",
    262: "HX_DRUMMER_CH06_LEFT_STICK",
    263: "HX_DRUMMER_CH07_RIGHT_STICK",
    264: "HX_DRUMMER_CH08_BODY_IMPACT",
}
POSE_CHANNELS = {
    "kick_hit": (257, 264),
    "snare_hit": (258, 262, 263),
    "hi_hat_pulse": (259, 262),
    "left_tom_hit": (260, 262),
    "right_tom_hit": (260, 263),
    "left_crash": (261, 262),
    "right_crash": (261, 263),
    "both_crash": (261, 262, 263),
    "downbeat_impact": (264, 257, 258, 261, 262, 263),
}


def _find_or_create_element_effects(root: ET.Element) -> ET.Element:
    container = root.find("ElementEffects")
    if container is not None:
        return container
    # Current xLights-style sequences use ElementEffects. Keep a single
    # canonical container instead of fabricating a legacy <effects> tree.
    return ET.SubElement(root, "ElementEffects")


def _element_map(container: ET.Element) -> dict[str, ET.Element]:
    return {element.get("name", ""): element for element in container.findall("Element") if element.get("name")}


def _layer_for(container: ET.Element, elements: dict[str, ET.Element], name: str, layer_name: str) -> ET.Element:
    element = elements.get(name)
    if element is None:
        element = ET.SubElement(container, "Element", {"type": "model", "name": name})
        elements[name] = element
    for layer in element.findall("EffectLayer"):
        if layer.get("name") == layer_name:
            return layer
    return ET.SubElement(element, "EffectLayer", {"name": layer_name, "visible": "1"})


def _clear_layer(layer: ET.Element) -> None:
    for child in list(layer):
        layer.remove(child)


def _add_on(layer: ET.Element, start_ms: int, end_ms: int, intensity: float, pose: str, source_type: str) -> None:
    ET.SubElement(
        layer,
        "Effect",
        {
            "name": "On",
            "startTime": str(max(0, int(start_ms))),
            "endTime": str(max(int(start_ms) + 50, int(end_ms))),
            "settings": f"E_CHECKBOX_OverlayBkg=0,E_SLIDER_Brightness={max(0.08, min(1.0, float(intensity))):.3f}",
            "palette": "C_BUTTON_Palette1=#FFFFFF,C_BUTTON_Palette2=#FFFFFF,C_BUTTON_Palette3=#FFFFFF",
            "source": "HelixDrummerV3",
            "sourceModel": DRUMMER_V3_MODEL,
            "sourcePose": pose,
            "sourceDrumType": source_type,
        },
    )


def inject_drummer_v3(base_xsq: Path, output_xsq: Path, audio_path: Path, *, layer_name: str = "AUTO_Drummer_V3") -> dict[str, object]:
    if not base_xsq.exists():
        raise FileNotFoundError(base_xsq)
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)

    streams = detect_drum_event_streams_from_file(audio_path)
    resolved = resolve_drum_streams(streams)
    pose_events = map_events_to_drummer_v3_poses(resolved["events"])

    if output_xsq.resolve() != base_xsq.resolve():
        output_xsq.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base_xsq, output_xsq)

    tree = ET.parse(output_xsq)
    root = tree.getroot()
    if root.tag != "xsequence":
        raise ValueError(f"Expected xsequence root, got {root.tag!r}")

    container = _find_or_create_element_effects(root)
    elements = _element_map(container)
    layers: dict[int, ET.Element] = {}
    for channel, name in DRUMMER_CHANNELS.items():
        layers[channel] = _layer_for(container, elements, name, layer_name)
        _clear_layer(layers[channel])

    by_pose = 0
    for event in pose_events:
        pose = str(event["pose"])
        channels = POSE_CHANNELS.get(pose, (264,))
        intensity = float(event["intensity"])
        start = int(event["timestamp_ms"])
        end = int(event["end_ms"])
        source_type = str(event["drum_type"])
        for channel in channels:
            # Keep the distinct V3 semantics while exposing the legacy eight
            # AC channels required by the 256+8 show controller contract.
            _add_on(layers[channel], start, end, intensity, pose, source_type)
            by_pose += 1

    timing_name = layer_name
    existing_timing = {node.get("name") for node in root.findall("timingtrack")}
    if timing_name not in existing_timing:
        ET.SubElement(root, "timingtrack", {"name": timing_name})

    ET.indent(tree, space="  ")
    tree.write(output_xsq, encoding="utf-8", xml_declaration=True)

    return {
        "schema": "helix.drummer_v3_xsq_integration.v1",
        "model": DRUMMER_V3_MODEL,
        "base_xsq": str(base_xsq),
        "output_xsq": str(output_xsq),
        "audio": str(audio_path),
        "layer": layer_name,
        "fallback_mode": resolved["fallback_mode"],
        "event_count": len(pose_events),
        "placement_count": by_pose,
        "pose_counts": {pose: sum(1 for event in pose_events if event["pose"] == pose) for pose in POSE_CHANNELS},
        "channels": DRUMMER_CHANNELS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject detected drum events into the canonical 8-channel Drummer V3 XSQ contract.")
    parser.add_argument("base_xsq", type=Path)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layer", default="AUTO_Drummer_V3")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    report = inject_drummer_v3(args.base_xsq, args.output, args.audio, layer_name=args.layer)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
