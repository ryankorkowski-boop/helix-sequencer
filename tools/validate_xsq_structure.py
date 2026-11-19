from __future__ import annotations

import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REQUIRED_ROOT = "xsequence"


class ValidationError(Exception):
    pass


def _find_timing_tracks(root: ET.Element) -> list[ET.Element]:
    # Current xLights exports can use one or more timingtrack nodes.
    return [node for node in root.findall("timingtrack")]


def _has_native_xlights_timing(root: ET.Element) -> bool:
    """Native xLights XSQ stores timing rows in DisplayElements/ElementEffects.

    Reject empty timing placeholders: a named timing row must have real effects
    in ElementEffects and a corresponding DisplayElements entry.
    """
    display = root.find("DisplayElements")
    effects = root.find("ElementEffects")
    if display is None or effects is None:
        return False
    visible = {
        e.get("name")
        for e in display.findall("Element")
        if (e.get("type") or "").lower() == "timing" and e.get("name")
    }
    return any(
        e.get("name") in visible and bool(e.findall(".//Effect"))
        for e in effects.findall("Element")
        if (e.get("type") or "").lower() == "timing"
    )


def _find_effect_containers(root: ET.Element) -> list[ET.Element]:
    # Older synthetic XSQs used <effects>; current Helix/xLights sequences
    # use <ElementEffects>. Accept both without weakening XML validation.
    containers: list[ET.Element] = []
    for tag in ("effects", "ElementEffects"):
        node = root.find(tag)
        if node is not None:
            containers.append(node)
    return containers


def validate_xsq(path: Path) -> None:
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as exc:
        raise ValidationError(f"Unable to parse XSQ: {exc}") from exc

    root = tree.getroot()
    if root.tag != REQUIRED_ROOT:
        raise ValidationError(f"Root node must be '{REQUIRED_ROOT}'")

    timingtracks = _find_timing_tracks(root)
    effect_containers = _find_effect_containers(root)

    if not timingtracks and not _has_native_xlights_timing(root):
        raise ValidationError("Missing timingtrack or populated native xLights timing rows")
    if not effect_containers:
        raise ValidationError("Missing effects/ElementEffects container")

    # Validate legacy phoneme timing entries when present. Current Helix
    # sequences may have timing tracks containing beats/labels instead.
    for timingtrack in timingtracks:
        indexes: set[str] = set()
        previous_start = -1.0
        for phoneme in timingtrack.findall("phoneme"):
            index = phoneme.attrib.get("index")
            start = phoneme.attrib.get("start")
            duration = phoneme.attrib.get("duration")

            if index is None:
                raise ValidationError("Phoneme missing index")
            if index in indexes:
                raise ValidationError(f"Duplicate phoneme index: {index}")
            indexes.add(index)

            if start is None or duration is None:
                raise ValidationError("Missing timing values")

            try:
                start_f = float(start)
                duration_f = float(duration)
            except ValueError as exc:
                raise ValidationError("Non-numeric timing values detected") from exc

            if not math.isfinite(start_f) or not math.isfinite(duration_f):
                raise ValidationError("Non-finite timing values detected")
            if start_f < 0:
                raise ValidationError("Negative start time detected")
            if duration_f <= 0:
                raise ValidationError("Non-positive duration detected")
            if start_f < previous_start:
                raise ValidationError("Timing entries are not ordered")
            previous_start = start_f

    # Current sequences store model effects under ElementEffects/Element.
    # Require at least one model/timing element so a completely empty XML
    # document cannot pass as a sequence.
    effect_elements = [
        element
        for container in effect_containers
        for element in container.findall("Element")
    ]
    if not effect_elements:
        raise ValidationError("No Element entries found in effects container")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_xsq_structure.py <xsq-file>")
        sys.exit(1)

    target = Path(sys.argv[1])

    try:
        validate_xsq(target)
    except ValidationError as exc:
        print(f"VALIDATION FAILED: {exc}")
        sys.exit(2)

    print("XSQ VALIDATION PASSED")
