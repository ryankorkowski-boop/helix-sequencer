from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

import librosa

from audio.drum_detection import DrumDetectionConfig, detect_drum_event_streams
from mapping.drum_mapper import drummer_v3_pose_for_event, DRUMMER_V3_SUBMODELS_BY_POSE, DRUMMER_V3_DURATION_BY_POSE, DRUM_PRIORITY


MODEL = "HX_SNOWMAN_DRUMMER_V3"


def _ms(seconds: float) -> str:
    return str(int(round(seconds * 1000.0)))


def export_drummer_v3_xsq(audio: Path, output: Path, *, sequence_name: str = "DrummerV3GroundTruth") -> dict[str, object]:
    y, sr = librosa.load(str(audio), sr=None, mono=True)
    streams = detect_drum_event_streams(y, sr, DrumDetectionConfig(prefer_recall=True))
    events = []
    for key in streams:
        events.extend(streams[key])
    events.sort(key=lambda e: (e.timestamp_ms, DRUM_PRIORITY.get(e.drum_type, 9), -e.velocity))

    root = Element("xsequence", {"name": sequence_name, "model": MODEL})
    head = SubElement(root, "head")
    SubElement(head, "sequenceDuration").text = f"{len(y) / sr:.6f}"
    SubElement(head, "mediaFile").text = audio.name
    timing = SubElement(root, "timingtrack", {"name": "DrummerV3GroundTruth"})
    effects = SubElement(root, "effects")
    element_effects = SubElement(root, "ElementEffects")

    target_layers: dict[str, object] = {}
    all_targets = sorted({name for pose in DRUMMER_V3_SUBMODELS_BY_POSE.values() for name in pose})
    for target in all_targets:
        el = SubElement(element_effects, "Element", {"name": target, "type": "model"})
        target_layers[target] = SubElement(el, "EffectLayer")

    for index, event in enumerate(events):
        pose = drummer_v3_pose_for_event(event, index)
        duration_ms = DRUMMER_V3_DURATION_BY_POSE.get(pose, 140)
        start_ms = event.timestamp_ms
        end_ms = start_ms + duration_ms
        targets = DRUMMER_V3_SUBMODELS_BY_POSE[pose]
        intensity = max(5, min(100, int(round(event.velocity * 100))))

        marker = SubElement(timing, "phoneme", {
            "index": str(index),
            "performer": "drummer_v3",
            "phoneme": pose,
            "start": f"{event.timestamp:.6f}",
            "duration": f"{duration_ms / 1000.0:.6f}",
            "intensity": f"{event.velocity:.4f}",
            "drum_type": event.drum_type,
            "target_submodels": ",".join(targets),
        })
        effect = SubElement(effects, "effect", {
            "index": str(index),
            "type": "drummer_v3_hit",
            "start": f"{event.timestamp:.6f}",
            "duration": f"{duration_ms / 1000.0:.6f}",
            "pose": pose,
            "target_submodels": ",".join(targets),
            "confidence": f"{event.confidence:.4f}",
        })
        for target in targets:
            node = SubElement(target_layers[target], "Effect", {
                "name": "On",
                "label": f"{pose}:{event.drum_type}:{target}",
                "startTime": _ms(event.timestamp),
                "endTime": _ms(event.timestamp + duration_ms / 1000.0),
                "settings": f"E_VALUECURVE_Intensity=Active=TRUE,Start={intensity},End=0",
                "palette": "C_BUTTON_Palette1=#ffffff,C_BUTTON_Palette2=#ffffff,C_CHECKBOX_Palette1=1,C_CHECKBOX_Palette2=1",
            })

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(tostring(root, encoding="utf-8").decode("utf-8"), encoding="utf-8")
    counts = {key: len(value) for key, value in streams.items()}
    return {"audio": str(audio), "output": str(output), "duration_seconds": len(y) / sr, "event_count": len(events), "stream_counts": counts, "target_count": len(all_targets), "targets": all_targets}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export audio-driven Drummer V3 effects directly to named submodel targets.")
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import json
    print(json.dumps(export_drummer_v3_xsq(args.audio, args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
