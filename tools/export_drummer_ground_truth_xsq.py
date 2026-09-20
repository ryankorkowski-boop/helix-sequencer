from __future__ import annotations

import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from tools.validate_xsq_structure import validate_xsq


DRUMMER_MODEL = "HX_SNOWMAN_DRUMMER_V3"
SUBMODELS = (
    "HX_SNOWMAN_DRUMMER_V3_KICK",
    "HX_SNOWMAN_DRUMMER_V3_SNARE",
    "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT",
    "HX_SNOWMAN_DRUMMER_V3_DRUMKIT_ALL",
)
POSE_TARGETS = {
    "KICK": "HX_SNOWMAN_DRUMMER_V3_HIT_KICK",
    "SNARE": "HX_SNOWMAN_DRUMMER_V3_HIT_SNARE",
    "HI_HAT": "HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT",
    "TOM_LEFT": "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_TOM",
    "TOM_RIGHT": "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_TOM",
    "CYMBAL_LEFT": "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_CRASH",
    "CYMBAL_RIGHT": "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_CRASH",
    "DRUMKIT_ALL": "HX_SNOWMAN_DRUMMER_V3_DRUMKIT_ALL",
}


def _add_event(track: ET.Element, index: int, performer: str, phoneme: str, start: float, duration: float) -> None:
    ET.SubElement(track, "phoneme", {
        "index": str(index), "performer": performer, "phoneme": phoneme,
        "start": f"{start:.6f}", "duration": f"{duration:.6f}", "intensity": "1.0000",
    })


def _add_effect(element: ET.Element, name: str, label: str, start: float, duration: float, intensity: int = 100, source_submodel: str | None = None) -> None:
    layer = ET.SubElement(element, "EffectLayer")
    ET.SubElement(layer, "Effect", {
        "name": name, "label": label,
        "startTime": str(int(start * 1000)),
        "endTime": str(int((start + duration) * 1000)),
        "settings": f"Start={intensity}",
        "source": "HelixDrummerV3GroundTruth",
        "sourcePoseSubmodel": source_submodel or label,
    })


def _sort_timing_events(track: ET.Element) -> None:
    events = list(track.findall("phoneme"))
    events.sort(key=lambda event: (float(event.get("start", "0")), int(event.get("index", "0"))))
    for index, event in enumerate(events):
        event.set("index", str(index))
        track.remove(event)
    track.extend(events)


def build_drummer_ground_truth_xsq_text(duration: float = 20.0) -> str:
    duration = max(1.0, float(duration))
    root = ET.Element("xsequence", {"name": "HelixDrummerGroundTruth", "model": DRUMMER_MODEL, "duration": f"{duration:.6f}"})
    track = ET.SubElement(root, "timingtrack", {"name": "HelixDrummerGroundTruth"})
    effects_root = ET.SubElement(root, "effects")
    element_effects = ET.SubElement(root, "ElementEffects")
    elements = {}
    for model in SUBMODELS:
        element = ET.SubElement(element_effects, "Element", {"type": "model", "name": model})
        elements[model] = element

    index = 0
    beat = 0.5
    t = 0.0
    while t < duration:
        if int(round(t / beat)) % 4 in (0, 2):
            label, target, effect_name = "KICK", SUBMODELS[0], "Kick"
        else:
            label, target, effect_name = "SNARE", SUBMODELS[1], "Snare"
        _add_event(track, index, "drummer", label, t, 0.12); index += 1
        _add_effect(elements[target], effect_name, label, t, 0.12, 100, target)

        hat_t = t + beat / 2
        if hat_t < duration:
            _add_event(track, index, "drummer", "HI_HAT", hat_t, 0.07); index += 1
            _add_effect(elements[SUBMODELS[2]], "Hi-Hat", "HI_HAT", hat_t, 0.07, 85, SUBMODELS[2])

        beat_i = int(round(t / beat))
        if beat_i % 8 == 4:
            for offset, label, target in (
                (0.00, "CYMBAL_LEFT", SUBMODELS[3]),
                (0.00, "CYMBAL_RIGHT", SUBMODELS[4]),
                (0.02, "TOM_LEFT", SUBMODELS[5]),
                (0.06, "TOM_RIGHT", SUBMODELS[6]),
            ):
                et = t + offset
                if et < duration:
                    _add_event(track, index, "drummer", label, et, 0.16); index += 1
                    _add_effect(elements[target], label.title().replace("_", "-"), label, et, 0.16, 100, target)

        if beat_i % 16 == 0:
            _add_effect(elements[SUBMODELS[7]], "DrumKitAll", "DRUMKIT_ALL", t, 0.10, 70)

        t += beat

    _sort_timing_events(track)
    ET.SubElement(effects_root, "effect", {"type": "drummer_ground_truth", "duration": f"{duration:.6f}"})
    return ET.tostring(root, encoding="unicode")


def export_drummer_ground_truth_xsq(output_path: str | Path, duration: float | None = None) -> Path:
    if duration is None:
        duration = float(os.environ.get("HELIX_DURATION", "20"))
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_drummer_ground_truth_xsq_text(duration), encoding="utf-8")
    validate_xsq(path)
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a deterministic drummer/submodel ground-truth XSQ.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=None)
    args = parser.parse_args(argv)
    print(export_drummer_ground_truth_xsq(args.output, args.duration))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
