from __future__ import annotations

import argparse
import json
import math
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import librosa
import numpy as np

from audio.drum_classification import DrumEvent as LegacyDrumEvent
from core.drummer_v3_analysis import DrumType, analyze_drummer_features
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_v3_poses, resolve_drum_streams

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
ACTUATOR_HEX = "#FFF0C8"

COMPONENT_VISUAL_PARTS = {
    f"{DRUMMER_V3_MODEL}_KICK": (
        (f"{DRUMMER_V3_MODEL}_KICK_SURFACE", "#DC2D1C"),
    ),
    f"{DRUMMER_V3_MODEL}_SNARE": (
        (f"{DRUMMER_V3_MODEL}_SNARE_SURFACE", "#D65CBE"),
        (f"{DRUMMER_V3_MODEL}_LEFT_ARM_STICK", ACTUATOR_HEX),
    ),
    f"{DRUMMER_V3_MODEL}_HI_HAT": (
        (f"{DRUMMER_V3_MODEL}_HI_HAT_SURFACE", "#DCA416"),
        (f"{DRUMMER_V3_MODEL}_HI_HAT_FOOT", ACTUATOR_HEX),
    ),
    f"{DRUMMER_V3_MODEL}_TOM_HIGH": (
        (f"{DRUMMER_V3_MODEL}_TOM_HIGH_SURFACE", "#2CB242"),
        (f"{DRUMMER_V3_MODEL}_RIGHT_ARM_STICK", ACTUATOR_HEX),
    ),
    f"{DRUMMER_V3_MODEL}_TOM_MID": (
        (f"{DRUMMER_V3_MODEL}_TOM_MID_SURFACE", "#2CB242"),
        (f"{DRUMMER_V3_MODEL}_LEFT_ARM_STICK", ACTUATOR_HEX),
    ),
    f"{DRUMMER_V3_MODEL}_TOM_FLOOR": (
        (f"{DRUMMER_V3_MODEL}_TOM_FLOOR_SURFACE", "#2CB242"),
        (f"{DRUMMER_V3_MODEL}_LEFT_ARM_STICK", ACTUATOR_HEX),
    ),
    f"{DRUMMER_V3_MODEL}_CYMBAL_LEFT": (
        (f"{DRUMMER_V3_MODEL}_CYMBAL_LEFT_SURFACE", "#DCA416"),
        (f"{DRUMMER_V3_MODEL}_LEFT_ARM_STICK", ACTUATOR_HEX),
    ),
    f"{DRUMMER_V3_MODEL}_CYMBAL_RIGHT": (
        (f"{DRUMMER_V3_MODEL}_CYMBAL_RIGHT_SURFACE", "#DCA416"),
        (f"{DRUMMER_V3_MODEL}_RIGHT_ARM_STICK", ACTUATOR_HEX),
    ),
}


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
            "sourceDetector": "v3_multi_detector_hpss",
        },
    )


def _band_energy(
    magnitude: np.ndarray,
    freqs: np.ndarray,
    low: float,
    high: float,
) -> np.ndarray:
    mask = (freqs >= low) & (freqs < high)
    if not np.any(mask):
        return np.zeros(magnitude.shape[1], dtype=float)
    return np.sqrt(np.mean(np.square(magnitude[mask]), axis=0))


def _analyze_real_audio(audio_path: Path) -> tuple[list[LegacyDrumEvent], dict[str, object]]:
    """Conservative one-source drummer analysis using isolated percussive evidence."""
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    y = np.asarray(y, dtype=np.float32)
    hop = max(128, int(round(sr * 0.01)))
    n_fft = max(1024, 2 ** int(np.ceil(np.log2(max(1024, int(sr * 0.046))))))

    stft = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop, center=True))
    harmonic, percussive = librosa.effects.hpss(y, margin=2.0)
    p_stft = np.abs(librosa.stft(percussive, n_fft=n_fft, hop_length=hop, center=True))
    h_rms = librosa.feature.rms(
        y=harmonic,
        frame_length=n_fft,
        hop_length=hop,
        center=True,
    )[0]
    p_rms = librosa.feature.rms(
        y=percussive,
        frame_length=n_fft,
        hop_length=hop,
        center=True,
    )[0]
    n = min(stft.shape[1], p_stft.shape[1], len(h_rms), len(p_rms))
    stft = stft[:, :n]
    p_stft = p_stft[:, :n]
    h_rms = h_rms[:n]
    p_rms = p_rms[:n]

    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    low = _band_energy(stft, freqs, 35, 180)
    mid = _band_energy(stft, freqs, 180, 2400)
    high = _band_energy(stft, freqs, 2400, min(sr / 2, 12000))
    drum_low = _band_energy(p_stft, freqs, 35, 220)
    drum_mid = _band_energy(p_stft, freqs, 220, 2400)
    drum_high = _band_energy(p_stft, freqs, 2400, min(sr / 2, 14000))

    drum_quality = p_rms / np.maximum(p_rms + h_rms, 1e-9)
    flatness = librosa.feature.spectral_flatness(S=p_stft)[0][:n]
    rms = librosa.feature.rms(
        y=y,
        frame_length=n_fft,
        hop_length=hop,
        center=True,
    )[0][:n]
    times = librosa.frames_to_time(np.arange(n), sr=sr, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(
        y=y,
        sr=sr,
        hop_length=hop,
        units="frames",
    )
    beats = np.asarray(beats, dtype=int)

    detected = analyze_drummer_features(
        low=low,
        mid=mid,
        high=high,
        rms=rms,
        times=times,
        drum_low=drum_low,
        drum_mid=drum_mid,
        drum_high=drum_high,
        beat_indices=beats,
        frame_rate=sr / hop,
        drum_percussive_ratio=drum_quality,
        percussive_flatness=flatness,
        min_percussive_ratio=.34,
    )

    legacy: list[LegacyDrumEvent] = []
    for index, event in enumerate(detected):
        if event.kind == DrumType.KICK:
            drum_type = "kick"
        elif event.kind == DrumType.SNARE:
            drum_type = "snare"
        elif event.kind == DrumType.HI_HAT:
            drum_type = "hihat"
        elif event.kind == DrumType.CYMBAL:
            drum_type = "cymbal"
        elif event.kind in (DrumType.TOM_HIGH, DrumType.TOM_MID, DrumType.TOM_FLOOR):
            drum_type = "tom"
        else:
            continue

        tom_class = {
            DrumType.TOM_HIGH: "high",
            DrumType.TOM_MID: "mid",
            DrumType.TOM_FLOOR: "floor",
        }.get(event.kind)
        frame = min(n - 1, max(0, int(round(event.time * sr / hop))))
        info: dict[str, object] = {
            "analysis_engine": "v3_multi_detector",
            "event_frame": float(round(event.time * sr / hop)),
            "percussive_ratio": round(float(drum_quality[frame]), 4),
            "percussive_flatness": round(float(flatness[frame]), 4),
        }
        if tom_class:
            info["tom_class"] = tom_class
            info["tom_class_confidence"] = round(float(event.confidence), 4)

        legacy.append(
            LegacyDrumEvent(
                timestamp=float(event.time),
                velocity=float(max(.12, min(1.0, event.confidence))),
                confidence=float(event.confidence),
                frequency_band_info=info,
                cluster_id=index,
                drum_type=drum_type,
                source="v3_multi_detector",
            )
        )

    counts = {
        kind.value: sum(1 for event in detected if event.kind == kind)
        for kind in DrumType
    }
    diagnostics: dict[str, object] = {
        "analysis_engine": "v3_multi_detector",
        "sample_rate": int(sr),
        "frame_rate": round(sr / hop, 3),
        "tempo_bpm": float(np.asarray(tempo).reshape(-1)[0]) if np.asarray(tempo).size else 0.0,
        "beat_count": int(len(beats)),
        "typed_event_count": len(legacy),
        "event_types": counts,
        "used_hpss_percussive_evidence": True,
        "min_percussive_ratio": .34,
        "percussive_ratio_p10": round(float(np.percentile(drum_quality, 10)), 4) if len(drum_quality) else 0.0,
        "percussive_ratio_median": round(float(np.median(drum_quality)), 4) if len(drum_quality) else 0.0,
        "percussive_flatness_median": round(float(np.median(flatness)), 4) if len(flatness) else 0.0,
    }
    return legacy, diagnostics


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
) -> dict[str, object]:
    base_xsq = Path(base_xsq)
    output_xsq = Path(output_xsq)
    audio_path = Path(audio_path)
    if not base_xsq.exists() or not audio_path.exists():
        raise FileNotFoundError("Missing XSQ or audio input")

    typed_events, diagnostics = _analyze_real_audio(audio_path)
    streams = {
        "kick_events": [event for event in typed_events if event.drum_type == "kick"],
        "snare_events": [event for event in typed_events if event.drum_type == "snare"],
        "tom_events": [event for event in typed_events if event.drum_type == "tom"],
        "hihat_events": [event for event in typed_events if event.drum_type == "hihat"],
        "cymbal_events": [event for event in typed_events if event.drum_type == "cymbal"],
        "drum_bus_events": [],
    }
    resolved = resolve_drum_streams(streams)
    pose_events = map_events_to_drummer_v3_poses(resolved["events"])

    if output_xsq.resolve() != base_xsq.resolve():
        output_xsq.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base_xsq, output_xsq)

    tree = ET.parse(output_xsq)
    root = tree.getroot()
    container = _find_or_create_element_effects(root)
    elements = _element_map(container)

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

    required_visual = {
        name
        for parts in COMPONENT_VISUAL_PARTS.values()
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
        )
        component_counts[component] += 1

        for visual_name, visual_color in COMPONENT_VISUAL_PARTS[component]:
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
                role="visual_geometry",
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
        "schema": "helix.drummer_v3_xsq_integration.v10",
        "model": DRUMMER_V3_MODEL,
        "base_xsq": str(base_xsq),
        "output_xsq": str(output_xsq),
        "audio": str(audio_path),
        "layer": layer_name,
        "logical_layer": logical_layer_name,
        "detector": "v3_multi_detector_hpss",
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
    args = parser.parse_args()

    report = inject_drummer_v3(
        args.base_xsq,
        args.output,
        args.audio,
        layer_name=args.layer,
    )
    payload = json.dumps(report, indent=2, sort_keys=True)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
