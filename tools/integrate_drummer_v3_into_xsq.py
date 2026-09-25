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
    "cymbal": "AUTO_Drummer_Cymbal",
    "drum_bus": "AUTO_Drummer_Bus",
}


def _element_effects(root: ET.Element) -> ET.Element:
    return root.find("ElementEffects") or ET.SubElement(root, "ElementEffects")


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
                f"intensity={max(0.0, min(1.0, float(intensity))):.3f}"
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

    # The performer model is the canonical visual target. It must exist in both
    # ElementEffects and DisplayElements; adding only ElementEffects creates XML
    # that our lightweight renderer can parse but that xLights cannot present as
    # a normal model in the sequence editor.
    _ensure_display_element(root, DRUMMER_MODEL)
    model_layer = _layer_for(container, elements, DRUMMER_MODEL, layer_name)
    _clear_layer(model_layer)

    type_layers: dict[str, ET.Element] = {}
    for drum_type, layer in DRUM_TYPE_LAYER.items():
        type_layers[drum_type] = _layer_for(container, elements, DRUMMER_MODEL, layer)
        _clear_layer(type_layers[drum_type])

    timing_track = _ensure_timing_track(root, DRUMMER_TIMING_TRACK)
    _clear_timing_track(timing_track)

    # physical_channels is retained only as a backwards-compatible CLI flag.
    # It is intentionally ignored: the drummer integration no longer invents
    # physical AC channels. Physical routing, if ever desired, belongs in a
    # separate routing profile.
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
        _add_timing_cue(timing_track, start, end, pose, drum_type, intensity)

        if physical_channels:
            for channel in POSE_CHANNELS.get(pose, (264,)):
                _add_on(
                    physical_layers[channel],
                    start,
                    end,
                    intensity,
                    pose,
                    drum_type,
                )
                placement_count += 1

    ET.indent(tree, space="  ")
    tree.write(output_xsq, encoding="utf-8", xml_declaration=True)

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
        "pose_counts": {
            pose: sum(1 for event in pose_events if event["pose"] == pose)
            for pose in POSE_CHANNELS
        },
        "placement_count": placement_count,
        "physical_channels_enabled": False,
        "channels": {},
        "physical_channel_policy": "none",
        "drummer_model_target": DRUMMER_MODEL,
        "contract": {
            "single_visual_target": True,
            "typed_layers": sorted(type_layers),
            "timing_cues": len(pose_events),
            "physical_channel_policy": "none_for_virtual_performer",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Integrate the normalized drummer performance plan into an XSQ.")
    parser.add_argument("base_xsq", type=Path)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layer", default="AUTO_Drummer_V3")
    # Kept as a deprecated no-op so older automation does not break while the
    # physical routing layer is being separated from performer generation.
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
