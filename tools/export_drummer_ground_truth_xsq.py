from __future__ import annotations

import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from tools.validate_xsq_structure import validate_xsq


DRUMMER_MODEL = "HX_SNOWMAN_DRUMMER_V3"
# Exactly nine sequenced drummer channels: kick, snare, hi-hat, four toms,
# and left/right cymbals. Stick geometry is contained inside these components.
SUBMODELS = (
    "HX_SNOWMAN_DRUMMER_V3_KICK",
    "HX_SNOWMAN_DRUMMER_V3_SNARE",
    "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_LEFT_2",
    "HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT_2",
)

# The current xmodel exposes two physical tom zones. Keep the nine-channel
# sequencing contract stable by using four logical tom lanes that resolve to
# the available physical tom geometry in the renderer.
POSE_TARGETS = {
    "KICK": SUBMODELS[0],
    "SNARE": SUBMODELS[1],
    "HI_HAT": SUBMODELS[2],
    "TOM_1": SUBMODELS[3],
    "TOM_2": SUBMODELS[4],
    "TOM_3": SUBMODELS[7],
    "TOM_4": SUBMODELS[8],
    "CYMBAL_LEFT": SUBMODELS[5],
    "CYMBAL_RIGHT": SUBMODELS[6],
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
    """Build deterministic ground truth with exactly nine sequenced channels."""
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
    tom_cycle = 0
    cymbal_cycle = 0
    while t < duration:
        beat_i = int(round(t / beat))
        if beat_i % 4 in (0, 2):
            label, target, effect_name = "KICK", POSE_TARGETS["KICK"], "Kick"
        else:
            label, target, effect_name = "SNARE", POSE_TARGETS["SNARE"], "Snare"
        _add_event(track, index, "drummer", label, t, 0.12); index += 1
        _add_effect(elements[target], effect_name, label, t, 0.12, 100, target)

        hat_t = t + beat / 2
        if hat_t < duration:
            _add_event(track, index, "drummer", "HI_HAT", hat_t, 0.07); index += 1
            _add_effect(elements[POSE_TARGETS["HI_HAT"]], "Hi-Hat", "HI_HAT", hat_t, 0.07, 85, POSE_TARGETS["HI_HAT"])

        if beat_i % 8 == 4:
            tom_labels = ("TOM_1", "TOM_2", "TOM_3", "TOM_4")
            for offset, tom_label in zip((0.00, 0.05, 0.10, 0.15), tom_labels):
                et = t + offset
                if et < duration:
                    target = POSE_TARGETS[tom_label]
                    _add_event(track, index, "drummer", tom_label, et, 0.14); index += 1
                    _add_effect(elements[target], tom_label.replace("_", "-"), tom_label, et, 0.14, 100, target)
            tom_cycle += 1

        if beat_i % 16 == 0:
            cym_label = "CYMBAL_LEFT" if cymbal_cycle % 2 == 0 else "CYMBAL_RIGHT"
            target = POSE_TARGETS[cym_label]
            _add_event(track, index, "drummer", cym_label, t, 0.16); index += 1
            _add_effect(elements[target], cym_label.replace("_", "-"), cym_label, t, 0.16, 100, target)
            cymbal_cycle += 1

        t += beat

    _sort_timing_events(track)
    ET.SubElement(effects_root, "effect", {"type": "drummer_ground_truth", "duration": f"{duration:.6f}", "channel_contract": "9"})
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode")


def export_drummer_ground_truth_xsq(output_path: str | Path, duration: float | None = None) -> Path:
    if duration is None:
        duration = float(os.environ.get("HELIX_DURATION", "20"))
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    xsq_text = build_drummer_ground_truth_xsq_text(duration)
    path.write_text(xsq_text, encoding="utf-8")
    validate_xsq(path)
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export deterministic nine-channel drummer ground truth.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=None)
    args = parser.parse_args(argv)
    output_path = export_drummer_ground_truth_xsq(args.output, args.duration)
    print(f"Exported drummer ground-truth XSQ to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
