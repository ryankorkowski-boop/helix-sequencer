from __future__ import annotations

import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from tools.validate_xsq_structure import validate_xsq

DRUMMER_MODEL = "HX_SNOWMAN_DRUMMER_V3"
# Nine logical lanes: kick, snare, hi-hat, high/mid/floor toms, L/R crashes and ride.
# Contacting sticks are embedded in the corresponding physical hit geometry.
CHANNELS = ("KICK", "SNARE", "HI_HAT", "TOM_HIGH", "TOM_MID", "TOM_FLOOR", "CYMBAL_LEFT", "CYMBAL_RIGHT", "RIDE")

# Canonical physical xmodel submodels. These names must match
# fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel exactly.
PHYSICAL_SUBMODELS = (
    "HX_SNOWMAN_DRUMMER_V3_KICK",
    "HX_SNOWMAN_DRUMMER_V3_SNARE",
    "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH",
    "HX_SNOWMAN_DRUMMER_V3_TOM_MID",
    "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
    "HX_SNOWMAN_DRUMMER_V3_RIDE",
)
CHANNEL_TO_PHYSICAL = dict(zip(CHANNELS, PHYSICAL_SUBMODELS))


def _add_event(track: ET.Element, index: int, channel: str, start: float, duration: float) -> None:
    ET.SubElement(track, "phoneme", {"index": str(index), "performer": "drummer", "phoneme": channel, "channel": channel, "start": f"{start:.6f}", "duration": f"{duration:.6f}", "intensity": "1.0000"})


def _add_effect(element: ET.Element, name: str, label: str, start: float, duration: float, intensity: int = 100, source_submodel: str | None = None) -> None:
    layer = ET.SubElement(element, "EffectLayer")
    ET.SubElement(layer, "Effect", {"name": name, "label": label, "startTime": str(int(start * 1000)), "endTime": str(int((start + duration) * 1000)), "settings": f"E_CHECKBOX_OverlayBkg=0,E_TEXTCTRL_Eff_On_Start={intensity},E_TEXTCTRL_Eff_On_End=0", "palette": "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1", "source": "HelixDrummerV3GroundTruth", "sourcePoseSubmodel": source_submodel or label})


def _sort_timing_events(track: ET.Element) -> None:
    events = list(track.findall("phoneme"))
    events.sort(key=lambda event: (float(event.get("start", "0")), int(event.get("index", "0"))))
    for index, event in enumerate(events):
        event.set("index", str(index))
        track.remove(event)
    track.extend(events)


def build_drummer_ground_truth_xsq_text(duration: float = 20.0) -> str:
    """Build deterministic ground truth with all nine lanes and canonical High/Mid/Floor tom zones."""
    duration = max(1.0, float(duration))
    root = ET.Element("xsequence", {"name": "HelixDrummerGroundTruth", "model": DRUMMER_MODEL, "duration": f"{duration:.6f}", "drummerChannels": "9", "tomContract": "HIGH_MID_FLOOR"})
    track = ET.SubElement(root, "timingtrack", {"name": "HelixDrummerGroundTruth", "channels": ",".join(CHANNELS)})
    effects_root = ET.SubElement(root, "effects")
    element_effects = ET.SubElement(root, "ElementEffects")
    elements = {}
    for model in PHYSICAL_SUBMODELS:
        elements[model] = ET.SubElement(element_effects, "Element", {"type": "model", "name": model})

    index = 0
    beat = 0.5
    t = 0.0
    cymbal_cycle = 0
    while t < duration:
        beat_i = int(round(t / beat))
        channel = "KICK" if beat_i % 4 in (0, 2) else "SNARE"
        _add_event(track, index, channel, t, 0.12)
        index += 1
        target = CHANNEL_TO_PHYSICAL[channel]
        _add_effect(elements[target], channel.title().replace("_", "-"), channel, t, 0.12, 100, target)

        hat_t = t + beat / 2
        if hat_t < duration:
            _add_event(track, index, "HI_HAT", hat_t, 0.07)
            index += 1
            target = CHANNEL_TO_PHYSICAL["HI_HAT"]
            _add_effect(elements[target], "Hi-Hat", "HI_HAT", hat_t, 0.07, 85, target)

        if beat_i % 8 == 4:
            for offset, channel in zip((0.00, 0.05, 0.10), ("TOM_HIGH", "TOM_MID", "TOM_FLOOR")):
                et = t + offset
                if et < duration:
                    _add_event(track, index, channel, et, 0.14)
                    index += 1
                    target = CHANNEL_TO_PHYSICAL[channel]
                    _add_effect(elements[target], channel.replace("_", "-"), channel, et, 0.14, 100, target)

        if beat_i % 16 == 0:
            channel = "CYMBAL_LEFT" if cymbal_cycle % 2 == 0 else "CYMBAL_RIGHT"
            cymbal_cycle += 1
            _add_event(track, index, channel, t, 0.16)
            index += 1
            target = CHANNEL_TO_PHYSICAL[channel]
            _add_effect(elements[target], channel.replace("_", "-"), channel, t, 0.16, 100, target)
        # The lower ride cymbal is a distinct physical target, not a renamed
        # right crash. Use explicit ground-truth hits; do not infer from audio.
        if beat_i % 8 == 6:
            ride_t = t + 0.125
            if ride_t < duration:
                _add_event(track, index, "RIDE", ride_t, 0.12)
                index += 1
                ride_target = CHANNEL_TO_PHYSICAL["RIDE"]
                _add_effect(elements[ride_target], "On", "RIDE", ride_t, 0.12, 84, ride_target)
        t += beat

    _sort_timing_events(track)
    ET.SubElement(effects_root, "effect", {"type": "drummer_ground_truth", "duration": f"{duration:.6f}", "channel_contract": "9", "tom_contract": "HIGH_MID_FLOOR", "stick_channels": "0"})
    ET.indent(root, space="  ")
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
    parser = argparse.ArgumentParser(description="Export deterministic nine-lane drummer ground truth using the canonical V3 xmodel High/Mid/Floor tom zones.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=None)
    args = parser.parse_args(argv)
    output_path = export_drummer_ground_truth_xsq(args.output, args.duration)
    print(f"Exported drummer ground-truth XSQ to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
