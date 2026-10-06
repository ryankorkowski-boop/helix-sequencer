from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from audio.drum_detection import detect_drum_event_streams_from_file
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_v3_poses, resolve_drum_streams

DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_TARGETS = set(DRUMMER_COMPONENTS)
ORACLE_COMMIT = "b27e8d77a63027ed32bcf6851dcff3925472c155"
ORACLE_COUNTS = {
    "kick": 194,
    "snare": 37,
    "tom": 9,
    "hihat": 208,
    "cymbal": 840,
    "drum_bus": 47,
}
ORACLE_SCHEDULED_COUNTS = {
    "kick": 193,
    "snare": 37,
    "tom": 9,
    "hihat": 205,
    "cymbal": 824,
    "drum_bus": 47,
}
ORACLE_POSE_COUNTS = {
    "kick_hit": 193,
    "snare_hit": 37,
    "hi_hat_pulse": 205,
    "right_tom_hit": 5,
    "left_tom_hit": 4,
    "right_crash": 412,
    "left_crash": 412,
    "both_crash": 0,
    "downbeat_impact": 47,
}
ORACLE_TIMELINE_SHA256 = "953386d5d69564abd83fb3c50fc7bf3e2aebb017e5995df8264771eda3b851ea"


def _find_or_create_element_effects(root: ET.Element) -> ET.Element:
    existing = root.find("ElementEffects")
    return existing if existing is not None else ET.SubElement(root, "ElementEffects")


def _element_map(container: ET.Element) -> dict[str, ET.Element]:
    return {e.get("name", ""): e for e in container.findall("Element") if e.get("name")}


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


def _brightness_percent(intensity: float) -> int:
    """Convert 0..1 performance intensity to the percent scale xLights expects."""
    value = max(0.0, min(1.0, float(intensity)))
    return int(round(60.0 + 40.0 * math.sqrt(value)))


def _add_on(
    layer: ET.Element,
    start_ms: int,
    end_ms: int,
    intensity: float,
    component: str,
    source_type: str,
    source_pose: str,
) -> None:
    brightness = _brightness_percent(intensity)
    ET.SubElement(
        layer,
        "Effect",
        {
            "name": "On",
            "startTime": str(max(0, int(start_ms))),
            "endTime": str(max(int(start_ms) + 50, int(end_ms))),
            "settings": (
                f"E_CHECKBOX_OverlayBkg=0,E_SLIDER_Brightness={brightness},"
                f"HELIX_DrummerIntensity={max(0.0, min(1.0, float(intensity))):.3f}"
            ),
            "palette": "C_BUTTON_Palette1=#FFFFFF,C_BUTTON_Palette2=#FFFFFF,C_BUTTON_Palette3=#FFFFFF",
            "source": "HelixDrummerV3",
            "sourceModel": DRUMMER_V3_MODEL,
            "sourceComponent": component,
            "sourceDrumType": source_type,
            "sourcePose": source_pose,
            "sourceDetector": "oracle_compatible_hpss_classifier",
        },
    )


def inject_drummer_v3(
    base_xsq: str | Path,
    output_xsq: str | Path,
    audio_path: str | Path,
    *,
    layer_name: str = "AUTO_Drummer_V3",
) -> dict[str, object]:
    """Detect real audio through the historically approved HPSS/classifier path."""
    base_xsq, output_xsq, audio_path = Path(base_xsq), Path(output_xsq), Path(audio_path)
    if not base_xsq.exists() or not audio_path.exists():
        raise FileNotFoundError("Missing XSQ or audio input")

    streams = detect_drum_event_streams_from_file(audio_path)
    resolved = resolve_drum_streams(streams)
    pose_events = map_events_to_drummer_v3_poses(resolved["events"])

    if output_xsq.resolve() != base_xsq.resolve():
        output_xsq.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base_xsq, output_xsq)

    tree = ET.parse(output_xsq)
    root = tree.getroot()
    container = _find_or_create_element_effects(root)
    elements = _element_map(container)
    layers: dict[str, ET.Element] = {}
    for name in sorted(DRUMMER_TARGETS):
        layers[name] = _layer_for(container, elements, name, layer_name)
        _clear_layer(layers[name])

    placements = 0
    component_counts = {component: 0 for component in sorted(DRUMMER_TARGETS)}
    for event in pose_events:
        components = tuple(str(value) for value in event.get("components", ()))
        if not components:
            raise ValueError(f"Drummer pose emitted no physical components: {event}")
        for component in components:
            if component not in DRUMMER_TARGETS:
                raise ValueError(f"Non-canonical drummer target emitted: {component}")
            _add_on(
                layers[component],
                int(event["timestamp_ms"]),
                int(event["end_ms"]),
                float(event["intensity"]),
                component,
                str(event["drum_type"]),
                str(event["pose"]),
            )
            component_counts[component] += 1
            placements += 1

    if layer_name not in {node.get("name") for node in root.findall("timingtrack")}:
        ET.SubElement(root, "timingtrack", {"name": layer_name})
    ET.indent(tree, space="  ")
    tree.write(output_xsq, encoding="utf-8", xml_declaration=True)

    raw_counts = {key.removesuffix("_events"): len(value) for key, value in streams.items()}
    scheduled_counts = {
        kind: sum(1 for event in resolved["events"] if event.drum_type == kind)
        for kind in ("kick", "snare", "tom", "hihat", "cymbal", "drum_bus")
    }
    pose_counts = {
        pose: sum(1 for event in pose_events if event["pose"] == pose)
        for pose in ORACLE_POSE_COUNTS
    }
    timeline_rows = [
        [int(event["timestamp_ms"]), int(event["end_ms"]), str(event["pose"]), str(event["drum_type"])]
        for event in pose_events
    ]
    timeline_sha256 = hashlib.sha256(
        json.dumps(timeline_rows, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    typed_count = sum(raw_counts.get(k, 0) for k in ("kick", "snare", "tom", "hihat", "cymbal"))
    bus_count = raw_counts.get("drum_bus", 0)
    return {
        "schema": "helix.drummer_v3_xsq_integration.v9",
        "model": DRUMMER_V3_MODEL,
        "base_xsq": str(base_xsq),
        "output_xsq": str(output_xsq),
        "audio": str(audio_path),
        "layer": layer_name,
        "detector": "hpss_classifier_intro_gated",
        "oracle_commit": ORACLE_COMMIT,
        "oracle_reference_counts": ORACLE_COUNTS,
        "fallback_mode": resolved["fallback_mode"],
        "intro_gate_start_ms": resolved.get("intro_gate_start_ms"),
        "intro_gate_suppressed_count": int(resolved.get("intro_gate_suppressed_count", 0) or 0),
        "first_scheduled_event_ms": min((int(event["timestamp_ms"]) for event in pose_events), default=None),
        "event_count": len(pose_events),
        "placement_count": placements,
        "raw_drum_type_counts": raw_counts,
        "scheduled_drum_type_counts": scheduled_counts,
        "oracle_scheduled_counts": ORACLE_SCHEDULED_COUNTS,
        "pose_counts": pose_counts,
        "oracle_pose_counts": ORACLE_POSE_COUNTS,
        "historical_timeline_sha256": timeline_sha256,
        "oracle_timeline_sha256": ORACLE_TIMELINE_SHA256,
        "typed_event_count": typed_count,
        "drum_bus_event_count": bus_count,
        "drum_bus_ratio": round(bus_count / max(1, typed_count + bus_count), 4),
        "component_counts": component_counts,
        "targets": sorted(DRUMMER_TARGETS),
        "target_count": len(DRUMMER_TARGETS),
        "xlights_brightness_scale": "60..100 percent, sqrt velocity curve",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject audio-detected Drummer V3 events into the canonical eight-component contract.")
    parser.add_argument("base_xsq", type=Path)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layer", default="AUTO_Drummer_V3")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = inject_drummer_v3(args.base_xsq, args.output, args.audio, layer_name=args.layer)
    payload = json.dumps(report, indent=2, sort_keys=True)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
