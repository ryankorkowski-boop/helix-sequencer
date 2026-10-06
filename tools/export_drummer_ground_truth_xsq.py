from __future__ import annotations

import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from tools.drummer_ground_truth_oracle import TARGETS, fixture_events
from tools.validate_xsq_structure import validate_xsq

DRUMMER_MODEL = "HX_SNOWMAN_DRUMMER_V3"
CHANNELS = TARGETS
PHYSICAL_SUBMODELS = tuple(f"{DRUMMER_MODEL}_{channel}" for channel in CHANNELS)
CHANNEL_TO_PHYSICAL = dict(zip(CHANNELS, PHYSICAL_SUBMODELS))


def _add_event(track: ET.Element, index: int, channel: str, start: float, duration: float) -> None:
    ET.SubElement(track, "phoneme", {
        "index": str(index), "performer": "drummer", "phoneme": channel,
        "channel": channel, "start": f"{start:.6f}", "duration": f"{duration:.6f}",
        "intensity": "1.0000",
    })


def _add_effect(element: ET.Element, channel: str, start: float, duration: float) -> None:
    layer = ET.SubElement(element, "EffectLayer")
    ET.SubElement(layer, "Effect", {
        "name": channel,
        "label": channel,
        "startTime": str(int(round(start * 1000))),
        "endTime": str(int(round((start + duration) * 1000))),
        "settings": "Start=100",
        "source": "HelixDrummerV3GroundTruth",
        "sourcePoseSubmodel": CHANNEL_TO_PHYSICAL[channel],
    })


def build_drummer_ground_truth_xsq_text(duration: float = 20.0) -> str:
    duration = max(1.0, float(duration))
    root = ET.Element("xsequence", {
        "name": "HelixDrummerGroundTruth",
        "model": DRUMMER_MODEL,
        "duration": f"{duration:.6f}",
        "drummerChannels": "8",
        "tomContract": "HIGH_MID_FLOOR",
    })
    track = ET.SubElement(root, "timingtrack", {
        "name": "HelixDrummerGroundTruth",
        "channels": ",".join(CHANNELS),
    })
    effects_root = ET.SubElement(root, "effects")
    element_effects = ET.SubElement(root, "ElementEffects")
    elements = {
        model: ET.SubElement(element_effects, "Element", {"type": "model", "name": model})
        for model in PHYSICAL_SUBMODELS
    }

    for index, event in enumerate(fixture_events(duration)):
        _add_event(track, index, event.target, event.time, event.duration)
        _add_effect(elements[CHANNEL_TO_PHYSICAL[event.target]], event.target, event.time, event.duration)

    ET.SubElement(effects_root, "effect", {
        "type": "drummer_ground_truth",
        "duration": f"{duration:.6f}",
        "event_count": str(len(fixture_events(duration))),
        "channel_contract": "8",
        "tom_contract": "HIGH_MID_FLOOR",
        "stick_channels": "0",
    })
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
    parser = argparse.ArgumentParser(description="Export deterministic eight-lane Drummer V3 ground truth.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=None)
    args = parser.parse_args(argv)
    output = export_drummer_ground_truth_xsq(args.output, args.duration)
    print(f"Exported drummer ground-truth XSQ to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
