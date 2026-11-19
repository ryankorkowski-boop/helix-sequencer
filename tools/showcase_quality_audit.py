"""XSQ showcase audit with explicit optional gating; does not invent effects."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def inspect_showcase(path: Path, *, neon_expected: bool = False):
    root = ET.parse(path).getroot()
    duration = float(root.findtext("./head/sequenceDuration", "0"))
    effects = []
    per_target = Counter()
    per_palette = Counter()
    intervals = []
    for row in root.findall("./ElementEffects/Element[@type='model']"):
        target = row.get("name", "")
        for e in row.findall("./EffectLayer/Effect"):
            start = int(float(e.get("startTime", 0)))
            end = int(float(e.get("endTime", 0)))
            if start >= end:
                continue
            effects.append(e)
            per_target[target] += 1
            per_palette[e.get("palette", "<missing>")] += 1
            intervals.append((start, end))

    section_counts = defaultdict(int)
    sections = []
    for row in root.findall("./ElementEffects/Element[@type='timing']"):
        if "parts" not in (row.get("name") or "").lower():
            continue
        for e in row.findall("./EffectLayer/Effect"):
            lo, hi = int(e.get("startTime", 0)), int(e.get("endTime", 0))
            if hi > lo:
                sections.append((lo, hi, e.get("label", "")))
        if sections:
            break
    for lo, hi, name in sections:
        section_counts[name] += sum(
            1 for e in effects if lo <= int(e.get("startTime", 0)) < hi
        )

    palette_count = len(root.findall("./ColorPalettes/ColorPalette"))
    used_count = len(per_palette)
    total = len(effects)
    dominance = (max(per_palette.values()) / total) if total else 1.0
    warnings = []
    blockers = []
    if total == 0:
        blockers.append("no model lighting effects")
    if not duration or duration < 0:
        blockers.append("no valid sequence duration")
    if neon_expected and total >= 20 and used_count < 2:
        blockers.append("neon mode only uses one effect palette")
    if neon_expected and total >= 40 and dominance > 0.80:
        blockers.append(f"neon palette dominance {dominance:.1%} exceeds 80%")
    if not sections:
        warnings.append("No song-parts timing track: section contrast cannot be assessed")
    if len(per_target) <= 1 and total >= 50:
        warnings.append("Only one model/group receives effects")

    if intervals:
        merged = []
        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        live_ms = sum(hi - lo for lo, hi in merged)
    else:
        live_ms = 0
    activity = (live_ms / (duration * 1000)) if duration else 0

    report = {
        "xsq": str(path), "duration_s": duration, "effects": total,
        "active_models_or_groups": len(per_target),
        "palette_definitions": palette_count, "used_palettes": dict(per_palette),
        "dominant_palette_fraction": round(dominance, 4),
        "timeline_activity_fraction": round(min(1.0, activity), 4),
        "music_sections": len(sections),
        "effects_by_section": dict(section_counts),
        "warnings": warnings, "blockers": blockers,
        "quality_gate_pass": not blockers,
        "native_xlights_render_verified": False,
    }
    return report


def write_showcase_audit(xsq: Path, *, neon_expected: bool = False, strict: bool = False):
    report = inspect_showcase(xsq, neon_expected=neon_expected)
    out = Path(xsq).with_suffix(".showcase_audit.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if strict and report["blockers"]:
        raise ValueError("Showcase quality gate failed: " + "; ".join(report["blockers"]))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xsq", type=Path)
    parser.add_argument("--neon-expected", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    print(json.dumps(write_showcase_audit(
        args.xsq, neon_expected=args.neon_expected, strict=args.strict
    ), indent=2))


if __name__ == "__main__":
    main()
