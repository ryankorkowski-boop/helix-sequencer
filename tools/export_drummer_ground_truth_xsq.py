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


def _add_event(track: ET.Element, index: int, performer: str, phoneme: str, start: float, duration: float) -> None:
    node = ET.SubElement(track, "phoneme", {
        "index": str(index),
        "performer": performer,
        "phoneme": phoneme,
        "start": f"{start:.6f}",
        "duration": f"{duration:.6f}",
        "intensity": "1.0000",
    })


def build_drummer_ground_truth_xsq_text(duration: float = 20.0) -> str:
    duration = max(1.0, float(duration))
    root = ET.Element("xsequence", {
        "name": "HelixDrummerGroundTruth",
        "model": DRUMMER_MODEL,
        "duration": f"{duration:.6f}",
    })
    track = ET.SubElement(root, "timingtrack", {"name": "HelixDrummerGroundTruth"})
    effects_root = ET.SubElement(root, "effects")
    element_effects = ET.SubElement(root, "ElementEffects")

    for model in SUBMODELS:
        element = ET.SubElement(element_effects, "Element", {"type": "model", "name": model})
        ET.SubElement(element, "EffectLayer")

    index = 0
    beat = 0.5
    t = 0.0
    while t < duration:
        beat_i = int(round(t / beat))
        # Kick on beats 1/3, snare on 2/4, hats on every half beat.
        if beat_i % 4 in (0, 2):
            _add_event(track, index, "drummer", "KICK", t, 0.12)
            index += 1
            target = SUBMODELS[0]
            effect = ET.SubElement(element_effects.find(f"Element[@name='{target}']"), "EffectLayer")
            ET.SubElement(effect, "Effect", {"name": "Kick", "label": "KICK", "startTime": str(int(t * 1000)), "endTime": str(int((t + 0.12) * 1000)), "settings": "Start=100"})
        elif beat_i % 4 in (1, 3):
            _add_event(track, index, "drummer", "SNARE", t, 0.12)
            index += 1
            target = SUBMODELS[1]
            effect = ET.SubElement(element_effects.find(f"Element[@name='{target}']"), "EffectLayer")
            ET.SubElement(effect, "Effect", {"name": "Snare", "label": "SNARE", "startTime": str(int(t * 1000)), "endTime": str(int((t + 0.12) * 1000)), "settings": "Start=100"})
        # Hi-hat gets its own visible pulse every half beat.
        hat_t = t + beat / 2
        if hat_t < duration:
            _add_event(track, index, "drummer", "HI_HAT", hat_t, 0.07)
            index += 1
            target = SUBMODELS[2]
            effect = ET.SubElement(element_effects.find(f"Element[@name='{target}']"), "EffectLayer")
            ET.SubElement(effect, "Effect", {"name": "Hi-Hat", "label": "HI_HAT", "startTime": str(int(hat_t * 1000)), "endTime": str(int((hat_t + 0.07) * 1000)), "settings": "Start=85"})
        # Four extra instrument accents prove the remaining real submodel targets.
        if beat_i % 8 == 4:
            for offset, target, label in ((0.0, SUBMODELS[3], "CYMBAL_LEFT"), (0.0, SUBMODELS[4], "CYMBAL_RIGHT"), (0.02, SUBMODELS[5], "TOM_LEFT"), (0.06, SUBMODELS[6], "TOM_RIGHT")):
                et = t + offset
                if et >= duration:
                    continue
                _add_event(track, index, "drummer", label, et, 0.16)
                index += 1
                element = element_effects.find(f"Element[@name='{target}']")
                layer = ET.SubElement(element, "EffectLayer")
                ET.SubElement(layer, "Effect", {"name": label.title().replace("_", "-"), "label": label, "startTime": str(int(et * 1000)), "endTime": str(int((et + 0.16) * 1000)), "settings": "Start=100"})
        # Whole-kit accent ties the ground-truth event to the complete drummer.
        if beat_i % 16 == 0:
            element = element_effects.find(f"Element[@name='{SUBMODELS[7]}'")
            if element is not None:
                layer = ET.SubElement(element, "EffectLayer")
                ET.SubElement(layer, "Effect", {"name": "DrumKitAll", "label": "DRUMKIT_ALL", "startTime": str(int(t * 1000)), "endTime": str(int((t + 0.10) * 1000)), "settings": "Start=70"})
        t += beat

    # Keep a simple effects container for structural compatibility.
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
