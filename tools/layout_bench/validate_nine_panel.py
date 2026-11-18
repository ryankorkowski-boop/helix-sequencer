#!/usr/bin/env python3
"""Validate the owner's locked nine-panel plan before any approval render."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "fixtures/layout_bench/nine_panel_lock.json"
MANIFEST = ROOT / "fixtures/layout_bench/manifest.json"
POSITIONS = (
    "top_left", "top_middle", "top_right",
    "middle_left", "middle_center", "middle_right",
    "bottom_left", "bottom_middle", "bottom_right",
)


def validate(lock: dict, fixtures: list[dict], *, approval: bool = True, require_render: bool = True) -> list[str]:
    errors = []
    grid = lock.get("grid", {})
    if (grid.get("columns"), grid.get("rows"), grid.get("center")) != (3, 3, "middle_center"):
        errors.append("grid must be 3x3 with middle_center band")
    slots = lock.get("slots", [])
    positions = [slot.get("position") for slot in slots]
    if positions != list(POSITIONS):
        errors.append("slot positions or ordering differ from locked 3x3 plan")
    ids = [slot.get("fixture_id") for slot in slots if slot.get("fixture_id")]
    if len(ids) != len(set(ids)):
        errors.append("duplicate fixture assignments")
    known = {item["id"] for item in fixtures}
    for slot in slots:
        position = slot.get("position", "?")
        fixture_id = slot.get("fixture_id")
        if fixture_id is not None and fixture_id not in known:
            errors.append(f"{position}: unknown fixture {fixture_id}")
        if approval and slot.get("status") != "verified":
            errors.append(f"{position}: {slot.get('status', 'unset')} — not verified for approval")
        if approval and not fixture_id:
            errors.append(f"{position}: no fixture")
    if len(slots) == 9 and slots[4].get("position") == "middle_center":
        if "snowman" not in slots[4].get("requirement", "").lower():
            errors.append("center panel must require canonical snowman band")
    if approval:
        if lock.get("audio", {}).get("status") != "verified":
            errors.append("real vocal audio is not verified")
        if require_render and lock.get("render", {}).get("status") != "verified":
            errors.append("native xLights FSEQ and MP4 render are not verified")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=LOCK)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--structural-only", action="store_true", help="Check structure without claiming approval readiness")
    args = parser.parse_args()
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    fixtures = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate(lock, fixtures, approval=not args.structural_only)
    for error in errors:
        print(f"BLOCKED: {error}")
    if errors:
        return 1
    print("Structural checks passed" if args.structural_only else "Approval readiness metadata checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
