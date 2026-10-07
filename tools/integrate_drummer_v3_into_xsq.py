from __future__ import annotations

import argparse
import json
import math
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from audio.drummer_v3 import analyze_drummer_audio as _analyze_real_audio
from audio.drummer_v3 import ANALYSIS_ENGINE
from tools.drummer_v3_visual_masks import load_spec
from mapping.drum_mapper import (
    DRUMMER_COMPONENTS,
    DrumMappingConfig,
    map_events_to_drummer_v3_poses,
    resolve_drum_streams,
)

ROOT = Path(__file__).resolve().parents[1]
DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_TARGETS = set(DRUMMER_COMPONENTS)
XMODEL = ROOT / "fixtures" / "band_geometry" / "models" / "HX_SNOWMAN_DRUMMER_V3.xmodel"

COMPONENT_HEX = {
    f"{DRUMMER_V3_MODEL}_KICK": "#DC2D1C",
    f"{DRUMMER_V3_MODEL}_SNARE": "#D65CBE",
    f"{DRUMMER_V3_MODEL}_HI_HAT": "#DCA416",
    f"{DRUMMER_V3_MODEL}_TOM_HIGH": "#2CB242",
    f"{DRUMMER_V3_MODEL}_TOM_MID": "#2CB242",
    f"{DRUMMER_V3_MODEL}_TOM_FLOOR": "#2CB242",
    f"{DRUMMER_V3_MODEL}_CYMBAL_LEFT": "#DCA416",
    f"{DRUMMER_V3_MODEL}_CYMBAL_RIGHT": "#DCA416",
}


def component_visual_parts() -> dict:
    source_colors = {node.get("name"): node.get("HelixSourceColor")
                     for node in ET.parse(XMODEL).getroot().findall("./subModels/subModel")}
    result = {}
    for item in load_spec()["lighting_targets"]:
        component = f"{DRUMMER_V3_MODEL}_{item['id']}"
        parts = [(f"{DRUMMER_V3_MODEL}_{item['surface']}", COMPONENT_HEX[component])]
        for actuator in item["actuators"]:
            name = f"{DRUMMER_V3_MODEL}_{actuator}"
            if actuator.endswith("_ARM_STICK"):
                for suffix in ("NEUTRAL", "WOOD"):
                    part = f"{name}_{suffix}"
                    color = source_colors.get(part)
                    if not color:
                        raise ValueError(f"Missing native source-color partition: {part}")
                    parts.append((part, color))
            else:
                parts.append((name, "#805825"))  # subtle source-brown pedal/foot
        result[component] = tuple(parts)
    return result


# Compatibility value; injection refreshes it from the current generated xmodel.
COMPONENT_VISUAL_PARTS = component_visual_parts()


def _find_or_create_element_effects(root: ET.Element) -> ET.Element:
    existing = root.find("ElementEffects")
    return existing if existing is not None else ET.SubElement(root, "ElementEffects")


def _element_map(container: ET.Element) -> dict[str, ET.Element]:
    return {
        element.get("name", ""): element
        for element in container.findall("Element")
        if element.get("name")
    }


def _layer_for(
    container: ET.Element,
    elements: dict[str, ET.Element],
    name: str,
    layer_name: str,
    *,
    visible: bool,
) -> ET.Element:
    element = elements.get(name)
    if element is None:
        element = ET.SubElement(container, "Element", {"type": "model", "name": name})
        elements[name] = element
    for layer in element.findall("EffectLayer"):
        if layer.get("name") == layer_name:
            layer.set("visible", "1" if visible else "0")
            return layer
    return ET.SubElement(
        element,
        "EffectLayer",
        {"name": layer_name, "visible": "1" if visible else "0"},
    )


def _clear_layer(layer: ET.Element) -> None:
    for child in list(layer):
        layer.remove(child)


def _brightness_percent(intensity: float) -> int:
    value = max(0.0, min(1.0, float(intensity)))
    return int(round(68.0 + 32.0 * math.sqrt(value)))


def _add_on(
    layer: ET.Element,
    start_ms: int,
    end_ms: int,
    intensity: float,
    *,
    palette_hex: str,
    source_component: str,
    source_type: str,
    source_pose: str,
    role: str,
    source_detector: str = ANALYSIS_ENGINE,
) -> None:
    brightness = _brightness_percent(intensity)
    if role == "visual_pedal":
        brightness = round(brightness * 0.32)
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
            "palette": ",".join(
                f"C_BUTTON_Palette{index}={palette_hex}"
                for index in (1, 2, 3)
            ),
            "source": "HelixDrummerV3",
            "sourceModel": DRUMMER_V3_MODEL,
            "sourceComponent": source_component,
            "sourceDrumType": source_type,
            "sourcePose": source_pose,
            "sourceRole": role,
            "sourceDetector": source_detector,
        },
    )


def event_audit(typed_events, pose_events) -> list[dict[str, object]]:
    assignments = {(row["timestamp_ms"], row["drum_type"]): row for row in pose_events}
    rows = []
    for event in typed_events:
        mapped = assignments.get((event.timestamp_ms, event.drum_type))
        rows.append({"timestamp": event.timestamp, "type": event.drum_type,
                     "confidence": event.confidence, "velocity": event.velocity,
                     "source_onset_index": event.frequency_band_info.get("onset_index"),
                     **event.frequency_band_info,
                     "physical_component": mapped["component"] if mapped else None,
                     "scheduled": mapped is not None})
    return rows


def _visual_submodel_names() -> set[str]:
    root = ET.parse(XMODEL).getroot()
    return {
        node.get("name", "")
        for node in root.findall("./subModels/subModel")
        if node.get("name")
    }


def _merge_visual_events(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    if not rows:
        return []
    ordered = sorted(rows, key=lambda row: (int(row["start_ms"]), int(row["end_ms"])))
    merged: list[dict[str, object]] = []
    for row in ordered:
        if not merged or int(row["start_ms"]) > int(merged[-1]["end_ms"]):
            merged.append(dict(row))
            continue
        previous = merged[-1]
        previous["end_ms"] = max(int(previous["end_ms"]), int(row["end_ms"]))
        if float(row["intensity"]) > float(previous["intensity"]):
            previous["intensity"] = row["intensity"]
        previous["source_type"] = "composite"
        previous["source_pose"] = "shared_actuator_union"
    return merged


def inject_drummer_v3(
    base_xsq: str | Path,
    output_xsq: str | Path,
    audio_path: str | Path,
    *,
    layer_name: str = "AUTO_Drummer_V3",
    transcription_path: str | Path | None = None,
) -> dict[str, object]:
    base_xsq = Path(base_xsq)
    output_xsq = Path(output_xsq)
    audio_path = Path(audio_path)
    if not base_xsq.exists() or not audio_path.exists():
        raise FileNotFoundError("Missing XSQ or audio input")

    if transcription_path is None:
        typed_events, diagnostics = _analyze_real_audio(audio_path)
    else:
        from audio.drum_transcription import load_drum_transcription
        typed_events, diagnostics = load_drum_transcription(transcription_path, audio_path)
    engine = diagnostics.get("analysis_engine", ANALYSIS_ENGINE)
    streams = {
        "kick_events": [event for event in typed_events if event.drum_type == "kick"],
        "snare_events": [event for event in typed_events if event.drum_type == "snare"],
        "tom_events": [event for event in typed_events if event.drum_type == "tom"],
        "hihat_events": [event for event in typed_events if event.drum_type == "hihat"],
        "cymbal_events": [event for event in typed_events if event.drum_type == "cymbal"],
        "drum_bus_events": [],
    }
    # The onset classifier already performs the false-intro quality gate.  Do
    # not suppress isolated but genuine opening kick/hat events a second time.
    resolved = resolve_drum_streams(
        streams,
        config=DrumMappingConfig(intro_gate_enabled=False),
    )
    pose_events = map_events_to_drummer_v3_poses(resolved["events"])
    assignments = {(e["timestamp_ms"],e["drum_type"]):e for e in pose_events}
    for row in diagnostics.get("onset_audit", []):
        if row["rejection_reason"] is None:
            mapped = assignments.get((round(row["timestamp"]*1000),row["drum_family"]))
            row["scheduler_decision"] = "scheduled" if mapped else "merge_or_clutter_suppressed"
            row["physical_target"] = mapped["component"] if mapped else None


    if output_xsq.resolve() != base_xsq.resolve():
        output_xsq.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base_xsq, output_xsq)

    tree = ET.parse(output_xsq)
    root = tree.getroot()
    container = _find_or_create_element_effects(root)
    elements = _element_map(container)

    # Re-injection must retire generated generic-arm layers from earlier V3
    # versions; otherwise both the old raised arm and the new strike illuminate.
    for element in container.findall("Element"):
        for layer in list(element.findall("EffectLayer")):
            if layer.get("name") in {layer_name, f"{layer_name}_LOGIC"}:
                element.remove(layer)

    # Eight public lanes remain the logical contract, but they are hidden in the
    # native renderer. Visible effects are placed on exact surface/actuator
    # geometry so a green tom never turns the drummer's arm green.
    logical_layer_name = f"{layer_name}_LOGIC"
    logical_layers: dict[str, ET.Element] = {}
    for component in sorted(DRUMMER_TARGETS):
        logical_layers[component] = _layer_for(
            container,
            elements,
            component,
            logical_layer_name,
            visible=False,
        )
        _clear_layer(logical_layers[component])

    visual_parts = component_visual_parts()
    required_visual = {
        name
        for parts in visual_parts.values()
        for name, _ in parts
    }
    available_visual = _visual_submodel_names()
    missing_visual = required_visual - available_visual
    if missing_visual:
        raise ValueError(f"Drummer xmodel missing visual submodels: {sorted(missing_visual)}")

    visual_layers: dict[str, ET.Element] = {}
    for name in sorted(required_visual):
        visual_layers[name] = _layer_for(
            container,
            elements,
            name,
            layer_name,
            visible=True,
        )
        _clear_layer(visual_layers[name])

    component_counts = {component: 0 for component in sorted(DRUMMER_TARGETS)}
    visual_rows: dict[str, list[dict[str, object]]] = {
        name: [] for name in required_visual
    }

    for event in pose_events:
        component = str(event["component"])
        if component not in DRUMMER_TARGETS:
            raise ValueError(f"Non-canonical drummer target emitted: {component}")
        start_ms = int(event["timestamp_ms"])
        end_ms = int(event["end_ms"])
        intensity = float(event["intensity"])
        drum_type = str(event["drum_type"])
        pose = str(event["pose"])

        _add_on(
            logical_layers[component],
            start_ms,
            end_ms,
            intensity,
            palette_hex=COMPONENT_HEX[component],
            source_component=component,
            source_type=drum_type,
            source_pose=pose,
            role="logical_component",
            source_detector=engine,
        )
        component_counts[component] += 1

        for visual_name, visual_color in visual_parts[component]:
            visual_rows[visual_name].append(
                {
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "intensity": intensity,
                    "palette_hex": visual_color,
                    "source_component": component,
                    "source_type": drum_type,
                    "source_pose": pose,
                }
            )

    visual_placements = 0
    for visual_name, rows in visual_rows.items():
        for row in _merge_visual_events(rows):
            _add_on(
                visual_layers[visual_name],
                int(row["start_ms"]),
                int(row["end_ms"]),
                float(row["intensity"]),
                palette_hex=str(row["palette_hex"]),
                source_component=str(row["source_component"]),
                source_type=str(row["source_type"]),
                source_pose=str(row["source_pose"]),
                role="visual_pedal" if visual_name.endswith("_HI_HAT_FOOT") else "visual_geometry",
                source_detector=engine,
            )
            visual_placements += 1

    if layer_name not in {node.get("name") for node in root.findall("timingtrack")}:
        ET.SubElement(root, "timingtrack", {"name": layer_name})
    ET.indent(tree, space="  ")
    tree.write(output_xsq, encoding="utf-8", xml_declaration=True)

    scheduled_counts = {
        kind: sum(1 for event in resolved["events"] if event.drum_type == kind)
        for kind in ("kick", "snare", "tom", "hihat", "cymbal")
    }
    first_ms = min(
        (int(event["timestamp_ms"]) for event in pose_events),
        default=None,
    )
    early_5s = sum(1 for event in pose_events if int(event["timestamp_ms"]) < 5000)
    early_10s = sum(1 for event in pose_events if int(event["timestamp_ms"]) < 10000)

    return {
        "schema": "helix.drummer_v3_xsq_integration.v11",
        "model": DRUMMER_V3_MODEL,
        "base_xsq": str(base_xsq),
        "output_xsq": str(output_xsq),
        "audio": str(audio_path),
        "layer": layer_name,
        "logical_layer": logical_layer_name,
        "detector": engine,
        "fallback_mode": resolved["fallback_mode"],
        "intro_gate_start_ms": resolved.get("intro_gate_start_ms"),
        "intro_gate_suppressed_count": int(resolved.get("intro_gate_suppressed_count", 0) or 0),
        "ambiguous_bus_rejected_count": int(resolved.get("ambiguous_bus_rejected_count", 0) or 0),
        "first_scheduled_event_ms": first_ms,
        "early_event_count_5s": early_5s,
        "early_event_count_10s": early_10s,
        "event_count": len(pose_events),
        "visual_placement_count": visual_placements,
        "scheduled_drum_type_counts": scheduled_counts,
        "component_counts": component_counts,
        "targets": sorted(DRUMMER_TARGETS),
        "target_count": len(DRUMMER_TARGETS),
        "visual_submodels": sorted(required_visual),
        "analysis": diagnostics,
        "event_audit": event_audit(typed_events, pose_events),
        "xlights_brightness_scale": "68..100 percent, sqrt velocity curve",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject conservative audio-detected Drummer V3 events into the canonical eight-component contract."
    )
    parser.add_argument("base_xsq", type=Path)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layer", default="AUTO_Drummer_V3")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--drum-events", type=Path, help="Source-hash-verified polyphonic drum transcription JSON")
    args = parser.parse_args()

    report = inject_drummer_v3(
        args.base_xsq,
        args.output,
        args.audio,
        layer_name=args.layer,
        transcription_path=args.drum_events,
    )
    payload = json.dumps(report, indent=2, sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k not in {"analysis", "event_audit"}}, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
