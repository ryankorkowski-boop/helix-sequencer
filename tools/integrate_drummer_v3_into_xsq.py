from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from audio.audio_intelligence_orchestrator import build_musical_event_map
from mapping.drum_mapper import normalized_events_to_drum_streams, resolve_drum_streams

DRUMMER_MODEL = "HX_SNOWMAN_DRUMMER"
DRUMMER_TIMING_TRACK = "AUTO_Drummer_V3"

# The drummer is a virtual xLights performer. It deliberately has no fixed
# LOR/AC channel allocation. The generated layout gives the model a separate
# high-numbered RGB namespace for preview/sequencing without consuming the
# user's 256-channel show.
DRUM_TYPE_LAYER = {
    "kick": "AUTO_Drummer_Kick",
    "snare": "AUTO_Drummer_Snare",
    "hihat": "AUTO_Drummer_HiHat",
    "tom": "AUTO_Drummer_Tom",
    "tom_left": "AUTO_Drummer_LeftTom",
    "tom_right": "AUTO_Drummer_RightTom",
    "floor_tom": "AUTO_Drummer_FloorTom",
    "cymbal": "AUTO_Drummer_Cymbal",
    "crash": "AUTO_Drummer_Crash",
    "ride": "AUTO_Drummer_Ride",
    "drum_bus": "AUTO_Drummer_Bus",
}


def _element_effects(root: ET.Element) -> ET.Element:
    container = root.find("ElementEffects")
    if container is None:
        container = ET.SubElement(root, "ElementEffects")
    return container


def _elements(container: ET.Element) -> dict[str, ET.Element]:
    return {e.get("name", ""): e for e in container.findall("Element") if e.get("name")}


def _layer_for(
    container: ET.Element,
    elements: dict[str, ET.Element],
    name: str,
    layer_name: str,
) -> ET.Element:
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


def _ensure_display_element(root: ET.Element, name: str) -> ET.Element:
    display = root.find("DisplayElements")
    if display is None:
        display = ET.SubElement(root, "DisplayElements")
    for element in display.findall("Element"):
        if element.get("name") == name:
            element.set("type", "model")
            element.set("visible", "1")
            return element
    return ET.SubElement(
        display,
        "Element",
        {"collapsed": "0", "type": "model", "name": name, "visible": "1"},
    )


def _drummer_submodel_targets(drum_type: str, pose: str, hand: str) -> tuple[str, ...]:
    stick = "LEFT_STICK" if hand == "left" else "RIGHT_STICK" if hand == "right" else None
    targets: list[str] = []
    if drum_type == "kick":
        targets.append("KICK")
    elif drum_type == "snare":
        targets.append("SNARE")
    elif drum_type == "hihat":
        targets.append("HI_HAT")
    elif drum_type in {"cymbal", "crash"}:
        targets.append(
            "CYMBAL_LEFT"
            if pose == "left_crash"
            else "CYMBAL_RIGHT"
            if pose == "right_crash"
            else "CYMBAL_LEFT"
        )
        if pose == "both_crash":
            targets.append("CYMBAL_RIGHT")
    elif drum_type == "ride":
        targets.append("RIDE")
    elif drum_type == "tom_left":
        targets.append("TOM_LEFT")
    elif drum_type == "tom_right":
        targets.append("TOM_RIGHT")
    elif drum_type == "floor_tom":
        targets.append("FLOOR_TOM")
    elif drum_type == "tom":
        targets.append(
            {
                "left_tom_hit": "TOM_LEFT",
                "right_tom_hit": "TOM_RIGHT",
                "floor_tom_hit": "FLOOR_TOM",
            }.get(pose, "TOM_LEFT")
        )
    elif drum_type == "drum_bus":
        targets.extend(("KICK", "SNARE", "CYMBAL_LEFT", "CYMBAL_RIGHT"))
    if stick and drum_type not in {"kick"}:
        targets.append(stick)
    return tuple(dict.fromkeys(targets))


def _add_on(
    layer: ET.Element,
    start_ms: int,
    end_ms: int,
    intensity: float,
    pose: str,
    drum_type: str,
) -> None:
    ET.SubElement(
        layer,
        "Effect",
        {
            "name": "On",
            "startTime": str(max(0, int(start_ms))),
            "endTime": str(max(int(start_ms) + 50, int(end_ms))),
            "settings": (
                "E_CHECKBOX_OverlayBkg=0,"
                f"E_SLIDER_Brightness={max(.08, min(1.0, float(intensity))):.3f}"
            ),
            "palette": "C_BUTTON_Palette1=#FFFFFF,C_BUTTON_Palette2=#FFFFFF,C_BUTTON_Palette3=#FFFFFF",
            "source": "HelixDrummerV3",
            "sourceModel": DRUMMER_MODEL,
            "sourcePose": pose,
            "sourceDrumType": drum_type,
        },
    )


def _ensure_timing_track(root: ET.Element, name: str) -> ET.Element:
    for track in root.findall("timingtrack"):
        if track.get("name") == name:
            return track
    return ET.SubElement(root, "timingtrack", {"name": name})


def _clear_timing_track(track: ET.Element) -> None:
    for child in list(track):
        track.remove(child)


def _add_timing_cue(
    track: ET.Element,
    start_ms: int,
    end_ms: int,
    pose: str,
    drum_type: str,
    intensity: float,
    hand: str,
) -> None:
    ET.SubElement(
        track,
        "Effect",
        {
            "name": pose,
            "startTime": str(max(0, int(start_ms))),
            "endTime": str(max(int(start_ms) + 50, int(end_ms))),
            "settings": (
                f"drum_type={drum_type},"
                f"intensity={max(0.0, min(1.0, float(intensity))):.3f},"
                f"hand={hand}"
            ),
        },
    )


def inject_drummer_v3(
    base_xsq: Path,
    output_xsq: Path,
    audio_path: Path,
    *,
    layer_name: str = "AUTO_Drummer_V3",
    physical_channels: bool = False,
) -> dict[str, object]:
    if not base_xsq.exists() or not audio_path.exists():
        raise FileNotFoundError("Missing XSQ or audio input")

    musical_events = build_musical_event_map(audio_path)
    streams = normalized_events_to_drum_streams(musical_events.events)
    resolved = resolve_drum_streams(streams)
    pose_events = list(resolved["drummer_v3_pose_events"])

    if output_xsq.resolve() != base_xsq.resolve():
        output_xsq.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base_xsq, output_xsq)

    tree = ET.parse(output_xsq)
    root = tree.getroot()
    container = _element_effects(root)
    elements = _elements(container)

    _ensure_display_element(root, DRUMMER_MODEL)
    model_layer = _layer_for(container, elements, DRUMMER_MODEL, layer_name)
    _clear_layer(model_layer)

    type_layers: dict[str, ET.Element] = {}
    for drum_type, layer in DRUM_TYPE_LAYER.items():
        type_layers[drum_type] = _layer_for(container, elements, DRUMMER_MODEL, layer)
        _clear_layer(type_layers[drum_type])

    timing_track = _ensure_timing_track(root, DRUMMER_TIMING_TRACK)
    _clear_timing_track(timing_track)

    placement_count = 0
    for event in pose_events:
        start = int(event["timestamp_ms"])
        end = int(event["end_ms"])
        intensity = float(event["intensity"])
        pose = str(event["pose"])
        drum_type = str(event["drum_type"])

        _add_on(model_layer, start, end, intensity, pose, drum_type)
        if drum_type in type_layers:
            _add_on(type_layers[drum_type], start, end, intensity, pose, drum_type)
        hand = str(event.get("hand", "both"))
        _add_timing_cue(timing_track, start, end, pose, drum_type, intensity, hand)
        for submodel in _drummer_submodel_targets(drum_type, pose, hand):
            target = f"{DRUMMER_MODEL}/{submodel}"
            _ensure_display_element(root, target)
            target_layer = _layer_for(container, elements, target, layer_name)
            _add_on(target_layer, start, end, intensity, pose, drum_type)
            placement_count += 1

    ET.indent(tree, space="  ")
    tree.write(output_xsq, encoding="utf-8", xml_declaration=True)

    by_timestamp: dict[int, int] = {}
    for event in pose_events:
        ts = int(event["timestamp_ms"])
        by_timestamp[ts] = by_timestamp.get(ts, 0) + 1
    polyphony_peak = max(by_timestamp.values(), default=0)

    # Keep the report data-driven. The previous implementation referenced a
    # stale DRUM_POSES symbol that no longer exists after the drummer model was
    # changed to typed performance events. That caused the entire MP4 render
    # stage to abort even though XSQ generation had succeeded.
    pose_names = sorted({str(event["pose"]) for event in pose_events})
    pose_counts = {
        pose: sum(1 for event in pose_events if str(event["pose"]) == pose)
        for pose in pose_names
    }

    return {
        "schema": "helix.drummer_performance.v2",
        "model": DRUMMER_MODEL,
        "timing_track": DRUMMER_TIMING_TRACK,
        "base_xsq": str(base_xsq),
        "output_xsq": str(output_xsq),
        "audio": str(audio_path),
        "audio_intelligence": musical_events.diagnostics,
        "layer": layer_name,
        "fallback_mode": resolved["fallback_mode"],
        "event_count": len(pose_events),
        "pose_counts": pose_counts,
        "placement_count": placement_count,
        "polyphony_peak": polyphony_peak,
        "polyphony_policy": "preserve_independent_drum_types_at_same_timestamp",
        "physical_channels_enabled": False,
        "channels": {},
        "physical_channel_policy": "none",
        "drummer_model_target": DRUMMER_MODEL,
        "contract": {
            "single_visual_target": True,
            "typed_layers": sorted(type_layers),
            "timing_cues": len(pose_events),
            "physical_channel_policy": "none_for_virtual_performer",
            "component_targets": True,
            "polyphonic_events_preserved": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Integrate the normalized drummer performance plan into an XSQ.")
    parser.add_argument("base_xsq", type=Path)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layer", default="AUTO_Drummer_V3")
    parser.add_argument("--physical-channels", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = inject_drummer_v3(
        args.base_xsq,
        args.output,
        args.audio,
        layer_name=args.layer,
        physical_channels=args.physical_channels,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
