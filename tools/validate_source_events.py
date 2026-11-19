"""Dependency-free integrity checks for source-timed Helix XSQ exports.

Usage: python -m tools.validate_source_events path/to/show.xsq
Checks XML time integrity and rejects false 'independent instruments' claims.
Does not establish audio-to-note accuracy or native LMS compatibility.
"""
from __future__ import annotations
import argparse
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def validate(path: Path) -> dict:
    root = ET.parse(path).getroot()
    groups = defaultdict(list)
    errors = []
    count = 0
    for element in root.findall("./ElementEffects/Element"):
        model = element.get("name", "")
        for effect in element.iter("Effect"):
            if effect.get("sourcePose") == "shared_actuator_union":
                continue
            start, end = effect.get("startTime"), effect.get("endTime")
            try:
                begin = int(start)
                finish = int(end)
            except (TypeError, ValueError):
                errors.append(f"{model}: missing/noninteger event time")
                continue
            if begin < 0 or finish <= begin:
                errors.append(f"{model}: invalid interval {begin}:{finish}")
                continue
            role = effect.get("sourceRole") or model
            if role == "visual_geometry":
                continue
            component = effect.get("sourceComponent") or model
            groups[role].append((begin, finish, component))
            count += 1
    if not count:
        errors.append("no timed musical/source events")
    for role, events in groups.items():
        if len(events) != len(set(events)):
            errors.append(f"{role}: duplicate source events")
    if errors:
        raise ValueError("; ".join(errors[:20]))
    signatures = {role: frozenset((a, b) for a, b, _ in events)
                  for role, events in groups.items()}
    identical = [[a, b] for i, (a, sa) in enumerate(signatures.items())
                 for b, sb in list(signatures.items())[i+1:] if sa == sb]
    return {
        "file": str(path),
        "events": count,
        "roles": {k: len(v) for k, v in sorted(groups.items())},
        "identical_timing_roles": identical,
        "instrument_identity_verified": False,
        "audio_alignment_verified": False,
        "native_lms_import_verified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("xsq", type=Path)
    args = parser.parse_args()
    report = validate(args.xsq)
    print(json.dumps(report, indent=2))
    if report["identical_timing_roles"]:
        raise SystemExit("FAIL: roles share identical event timings; investigate musical independence")


if __name__ == "__main__":
    main()
