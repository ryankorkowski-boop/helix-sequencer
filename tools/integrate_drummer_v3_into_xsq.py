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
            "sourceDetector": "v3_hpss_onset_classifier",
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


def _tom_class_from_low_centroid(low_centroid_hz: float) -> str:
    """Map an accepted tom onset to the physical HIGH/MID/FLOOR drum."""
    if low_centroid_hz >= 380.0:
        return "high"
    if low_centroid_hz >= 275.0:
        return "mid"
    return "floor"


def _classify_onset(
    *,
    low_ratio: float,
    low_mid_ratio: float,
    mid_ratio: float,
    high_ratio: float,
    centroid_hz: float,
    low_centroid_hz: float,
    decay_100ms: float,
    decay_300ms: float,
) -> tuple[str | None, str | None, str | None]:
    """Return (body, metal, tom_class) for one proven percussive onset.

    The classifier is deliberately sparse.  One onset may contain one body hit
    (kick/snare/tom) and one metal hit (hat/cymbal), which preserves real
    simultaneous kick+hat or snare+hat playing without turning one transient
    into three unrelated drums.
    """
    low = float(low_ratio)
    low_mid = float(low_mid_ratio)
    mid = float(mid_ratio)
    high = float(high_ratio)
    centroid = float(centroid_hz)
    low_centroid = float(low_centroid_hz)

    body: str | None = None
    tom_class: str | None = None

    # Tuned to the isolated HPSS percussive spectrum, not the full mix.
    # A tom has a substantial 180-700 Hz body and a higher low-band centroid
    # than a bass-drum fundamental.  Give that explicit signature precedence.
    tom_signature = (
        low_mid >= 0.28
        and high <= 0.43
        and low_centroid >= 225.0
        and low_mid >= low * 0.78
    )
    if tom_signature:
        body = "tom"
        tom_class = _tom_class_from_low_centroid(low_centroid)
    else:
        kick_score = (2.20 * low) + (0.55 * low_mid) + (0.12 * mid) - (0.35 * high)
        snare_score = (1.65 * mid) + (0.35 * high) + (0.25 * low_mid) - (0.35 * low)

        if low >= 0.18 and low_centroid <= 225.0 and kick_score >= 0.35:
            body = "kick"
        elif mid >= 0.22 and centroid <= 6500.0 and snare_score >= 0.42:
            body = "snare"
        elif (
            low_mid >= 0.22
            and high <= 0.45
            and centroid <= 4300.0
            and low_centroid >= 225.0
        ):
            body = "tom"
            tom_class = _tom_class_from_low_centroid(low_centroid)

    metal: str | None = None
    if high >= 0.46 and centroid >= 3500.0:
        sustained = decay_100ms >= 0.45 or decay_300ms >= 0.20
        if high >= 0.60 and sustained:
            metal = "cymbal"
        else:
            metal = "hihat"

    return body, metal, tom_class


def _analyze_real_audio(audio_path: Path) -> tuple[list[LegacyDrumEvent], dict[str, object]]:
    """Detect drummer hits from one conservative HPSS percussive-onset stream.

    This replaces the previous independent-family detector, which could either
    double-classify one transient across several drums or reject an entire real
    song because its spectral-flatness scale was mismatched.  Full-mix audio
    never originates a hit: every accepted onset must first pass an exact-frame
    HPSS percussive-ratio gate.
    """
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    y = np.asarray(y, dtype=np.float32)
    hop = max(128, int(round(sr * 0.01)))
    n_fft = max(1024, 2 ** int(np.ceil(np.log2(max(1024, int(sr * 0.046))))))

    harmonic, percussive = librosa.effects.hpss(y, margin=2.0)
    p_stft = np.abs(
        librosa.stft(percussive, n_fft=n_fft, hop_length=hop, center=True)
    )
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
    full_rms = librosa.feature.rms(
        y=y,
        frame_length=n_fft,
        hop_length=hop,
        center=True,
    )[0]
    onset_env = librosa.onset.onset_strength(
        y=percussive,
        sr=sr,
        hop_length=hop,
    )

    n = min(
        p_stft.shape[1],
        len(h_rms),
        len(p_rms),
        len(full_rms),
        len(onset_env),
    )
    p_stft = p_stft[:, :n]
    h_rms = h_rms[:n]
    p_rms = p_rms[:n]
    full_rms = full_rms[:n]
    onset_env = onset_env[:n]

    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    def band_sum(low_hz: float, high_hz: float) -> np.ndarray:
        mask = (freqs >= low_hz) & (freqs < high_hz)
        if not np.any(mask):
            return np.zeros(n, dtype=float)
        return np.sum(p_stft[mask], axis=0)

    low = band_sum(30, 180)
    low_mid = band_sum(180, 700)
    mid = band_sum(700, 2500)
    high = band_sum(2500, min(sr / 2, 14000))
    total = np.maximum(low + low_mid + mid + high, 1e-9)
    low_ratio = low / total
    low_mid_ratio = low_mid / total
    mid_ratio = mid / total
    high_ratio = high / total

    centroid = librosa.feature.spectral_centroid(S=p_stft, sr=sr)[0][:n]
    low_mask = (freqs >= 30) & (freqs < 700)
    low_total = np.sum(p_stft[low_mask], axis=0)
    low_centroid = np.sum(
        freqs[low_mask, None] * p_stft[low_mask],
        axis=0,
    ) / np.maximum(low_total, 1e-9)

    flatness = librosa.feature.spectral_flatness(S=p_stft)[0][:n]
    drum_quality = p_rms / np.maximum(p_rms + h_rms, 1e-9)

    onset_frames = np.asarray(
        librosa.onset.onset_detect(
            onset_envelope=onset_env,
            sr=sr,
            hop_length=hop,
            backtrack=False,
            delta=0.06,
            wait=3,
        ),
        dtype=int,
    )
    onset_scale = max(float(np.percentile(onset_env, 99.5)), 1e-9)

    typed: list[LegacyDrumEvent] = []
    rejected_quality = 0
    rejected_support = 0
    rejected_unclassified = 0
    accepted_onsets = 0

    for onset_index, frame in enumerate(onset_frames):
        frame = int(frame)
        if frame < 0 or frame >= n:
            continue

        # Critical false-positive guard: use the exact onset frame.  Taking the
        # maximum from neighbouring frames admitted guitar/piano attacks whose
        # adjacent HPSS frame happened to look percussive.
        quality = float(drum_quality[frame])
        if quality < 0.36:
            rejected_quality += 1
            continue

        local_lo = max(0, frame - 8)
        local_hi = min(n, frame + 9)
        if float(full_rms[frame]) < float(np.median(full_rms[local_lo:local_hi])):
            rejected_support += 1
            continue

        attack = float(np.mean(p_rms[frame:min(n, frame + 3)]))
        tail_100 = (
            float(np.mean(p_rms[min(n, frame + 5):min(n, frame + 12)]))
            if frame + 5 < n
            else 0.0
        )
        tail_300 = (
            float(np.mean(p_rms[min(n, frame + 15):min(n, frame + 35)]))
            if frame + 15 < n
            else 0.0
        )
        decay_100 = tail_100 / max(attack, 1e-9)
        decay_300 = tail_300 / max(attack, 1e-9)

        body, metal, tom_class = _classify_onset(
            low_ratio=float(low_ratio[frame]),
            low_mid_ratio=float(low_mid_ratio[frame]),
            mid_ratio=float(mid_ratio[frame]),
            high_ratio=float(high_ratio[frame]),
            centroid_hz=float(centroid[frame]),
            low_centroid_hz=float(low_centroid[frame]),
            decay_100ms=decay_100,
            decay_300ms=decay_300,
        )
        if body is None and metal is None:
            rejected_unclassified += 1
            continue

        accepted_onsets += 1
        timestamp = float(frame * hop / sr)
        onset_strength = min(1.0, float(onset_env[frame]) / onset_scale)
        confidence = max(
            0.36,
            min(1.0, (quality * 0.72) + (onset_strength * 0.28)),
        )
        velocity = max(
            0.22,
            min(1.0, (quality * 0.62) + (onset_strength * 0.38)),
        )

        common_info: dict[str, object] = {
            "analysis_engine": "v3_hpss_onset_classifier",
            "event_frame": float(frame),
            "percussive_ratio": round(quality, 4),
            "percussive_flatness": round(float(flatness[frame]), 6),
            "low_ratio": round(float(low_ratio[frame]), 4),
            "low_mid_ratio": round(float(low_mid_ratio[frame]), 4),
            "mid_ratio": round(float(mid_ratio[frame]), 4),
            "high_ratio": round(float(high_ratio[frame]), 4),
            "centroid_hz": round(float(centroid[frame]), 2),
            "low_centroid_hz": round(float(low_centroid[frame]), 2),
            "decay_100ms": round(float(decay_100), 4),
            "decay_300ms": round(float(decay_300), 4),
        }

        def append_event(drum_type: str, *, tom: str | None = None) -> None:
            info = dict(common_info)
            if tom is not None:
                info["tom_class"] = tom
                info["tom_class_confidence"] = round(confidence, 4)
            typed.append(
                LegacyDrumEvent(
                    timestamp=round(timestamp, 4),
                    velocity=round(velocity, 3),
                    confidence=round(confidence, 3),
                    frequency_band_info=info,
                    cluster_id=onset_index,
                    drum_type=drum_type,
                    source="v3_hpss_onset_classifier",
                )
            )

        if body is not None:
            append_event(body, tom=tom_class if body == "tom" else None)
        if metal is not None:
            append_event(metal)

    counts = {
        kind: sum(1 for event in typed if event.drum_type == kind)
        for kind in ("kick", "snare", "tom", "hihat", "cymbal")
    }
    tom_counts = {
        tom: sum(
            1
            for event in typed
            if event.drum_type == "tom"
            and event.frequency_band_info.get("tom_class") == tom
        )
        for tom in ("high", "mid", "floor")
    }

    diagnostics: dict[str, object] = {
        "analysis_engine": "v3_hpss_onset_classifier",
        "sample_rate": int(sr),
        "frame_rate": round(sr / hop, 3),
        "onset_candidate_count": int(len(onset_frames)),
        "accepted_onset_count": int(accepted_onsets),
        "typed_event_count": int(len(typed)),
        "event_types": counts,
        "tom_classes": tom_counts,
        "rejected_low_percussive_quality": int(rejected_quality),
        "rejected_weak_local_support": int(rejected_support),
        "rejected_unclassified": int(rejected_unclassified),
        "used_hpss_percussive_evidence": True,
        "min_percussive_ratio": 0.36,
        "percussive_ratio_p10": round(float(np.percentile(drum_quality, 10)), 4) if len(drum_quality) else 0.0,
        "percussive_ratio_median": round(float(np.median(drum_quality)), 4) if len(drum_quality) else 0.0,
        "percussive_ratio_p90": round(float(np.percentile(drum_quality, 90)), 4) if len(drum_quality) else 0.0,
    }
    return typed, diagnostics

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
    # The onset classifier already performs the false-intro quality gate.  Do
    # not suppress isolated but genuine opening kick/hat events a second time.
    resolved = resolve_drum_streams(
        streams,
        config=DrumMappingConfig(intro_gate_enabled=False),
    )
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
        "detector": "v3_hpss_onset_classifier",
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
