from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REQUIRED_ROOT = "xsequence"
REQUIRED_CHILDREN = {"timingtrack", "effects"}


class ValidationError(Exception):
    pass



def validate_xsq(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()

    if root.tag != REQUIRED_ROOT:
        raise ValidationError(f"Root node must be '{REQUIRED_ROOT}'")

    child_tags = {child.tag for child in root}

    missing = REQUIRED_CHILDREN - child_tags
    if missing:
        raise ValidationError(f"Missing required nodes: {sorted(missing)}")

    timingtrack = root.find("timingtrack")
    if timingtrack is None:
        raise ValidationError("Missing timingtrack")

    indexes = set()
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

        start_f = float(start)
        duration_f = float(duration)

        if start_f < 0:
            raise ValidationError("Negative start time detected")

        if duration_f <= 0:
            raise ValidationError("Non-positive duration detected")

        if start_f < previous_start:
            raise ValidationError("Timing entries are not ordered")

        previous_start = start_f


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
