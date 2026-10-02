from __future__ import annotations

import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from tools.validate_xsq_structure import validate_xsq


DRUMMER_MODEL = "HX_SNOWMAN_DRUMMER_V3"
# Nine logical sequencer lanes. Sticks are intentionally absent: their pixels
# live inside the corresponding physical hit/contact geometry.
CHANNELS = (
    "KICK", "SNARE", "HI_HAT", "TOM_1", "TOM_2", "TOM_3", "TOM_4",
    "CYMBAL_LEFT", "CYMBAL_RIGHT",
)
# Only these physical model elements currently exist in the xmodel. TOM_1/2
# resolve to the left/right physical tom zones; TOM_3/4 reuse those physical
# zones until the visual model itself is expanded. No stick element is emitted.
PHYSICAL_SUBMODELS = (
    "HX_SNOWMAN_DRUMMER_V3_KICK",
    "HX_SNOWMAN_DRUMMER_V3_SNARE",
    "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
)
CHANNEL_TO_PHYSICAL = {
    "KICK": PHYSICAL_SUBMODELS[0],
    "SNARE": PHYSICAL_SUBMODELS[1],
    "HI_HAT": PHYSICAL_SUBMODELS[2],
    "TOM_1": PHYSICAL_SUBMODELS[3],
    "TOM_2": PHYSICAL_SUBMODELS[4],
    "TOM_3": PHYSICAL_SUBMODELS[3],
    "TOM_4": PHYSICAL_SUBMODELS[4],
    "CYMBAL_LEFT": PHYSICAL_SUBMODELS[5],
    "CYMBAL_RIGHT": PHYSICAL_SUBMODELS[6],
}


def _add_event(track: ET.Element, index: int, channel: str, start: float, duration: float) -> None:
    ET.SubElement(track, "phoneme", {
        "index": str(index), "performer": "drummer", "phoneme": channel,
        "channel": channel, "start": f"{start:.6f}", "duration": f"{duration:.6f}",
        "intensity": "1.0000",
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
    """Build deterministic ground truth with exactly nine logical channels."""
    duration = max(1.0, float(duration))
    root = ET.Element("xsequence", {"name": "HelixDrummerGroundTruth", "model": DRUMMER_MODEL, "duration": f"{duration:.6f}", "drummerChannels": "9"})
    track = ET.SubElement(root, "timingtrack", {"name": "HelixDrummerGroundTruth", "channels": ",".join(CHANNELS)})
    effects_root = ET.SubElement(root, "effects")
    element_effects = ET.SubElement(root, "ElementEffects")
    elements = {}
    for model in PHYSICAL_SUBMODELS:
        element = ET.SubElement(element_effects, "Element", {"type": "model", "name": model})
        elements[model] = element

    index = 0
    beat = 0.5
    t = 0.0
    cymbal_cycle = 0
    while t < duration:
        beat_i = int(round(t / beat))
        channel = "KICK" if beat_i % 4 in (0, 2) else "SNARE"
        _add_event(track, index, channel, t, 0.12); index += 1
        target = CHANNEL_TO_PHYSICAL[channel]
        _add_effect(elements[target], channel.title().replace("_", "-"), channel, t, 0.12, 100, target)

        hat_t = t + beat / 2
        if hat_t < duration:
            channel = "HI_HAT"
            _add_event(track, index, channel, hat_t, 0.07); index += 1
            target = CHANNEL_TO_PHYSICAL[channel]
            _add_effect(elements[target], "Hi-Hat", channel, hat_t, 0.07, 85, target)

        if beat_i % 8 == 4:
            for offset, channel in zip((0.00, 0.05, 0.10, 0.15), ("TOM_1", "TOM_2", "TOM_3", "TOM_4")):
                et = t + offset
                if et < duration:
                    _add_event(track, index, channel, et, 0.14); index += 1
                    target = CHANNEL_TO_PHYSICAL[channel]
                    _add_effect(elements[target], channel.replace("_", "-"), channel, et, 0.14, 100, target)

        if beat_i % 16 == 0:
            channel = "CYMBAL_LEFT" if cymbal_cycle % 2 == 0 else "CYMBAL_RIGHT"
            cymbal_cycle += 1
            _add_event(track, index, channel, t, 0.16); index += 1
            target = CHANNEL_TO_PHYSICAL[channel]
            _add_effect(elements[target], channel.replace("_", "-"), channel, t, 0.16, 100, target)

        t += beat

    _sort_timing_events(track)
    ET.SubElement(effects_root, "effect", {"type": "drummer_ground_truth", "duration": f"{duration:.6f}", "channel_contract": "9", "stick_channels": "0"})
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
