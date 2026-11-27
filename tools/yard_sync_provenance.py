"""Detect shared beat clocks on ordinary yard props before native acceptance.

The 2026-11-27 pulsing regression copied the roof's onset schedule to dozens
of unrelated models. This checks *authored XSQ clocks*, not decoded FSEQ/MP4
brightness, and intentionally does not claim visual owner approval.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


def _family(name: str, display: str = "") -> str:
    """Coarse physical families, never performer roles or identity guesses."""
    name = name.upper()
    for family, tokens in (
        ("roof", ("ROOF", "RIDGE", "EAVE")),
        ("arch", ("ARCH",)),
        ("tree", ("TREE", "MEGA")),
        ("matrix", ("MATRIX", "PANEL")),
        ("cane", ("CANE",)),
        ("snowflake", ("SNOWFLAKE",)),
        ("spinner", ("SPINNER",)),
        ("window", ("WINDOW", "DOOR")),
        ("star", ("STAR",)),
    ):
        if any(token in name for token in tokens):
            return family
    return "display:" + (display.lower() or "other")


def analyze_yard_sync(root: ET.Element, layout: Path | None = None) -> dict:
    """Group ordinary Prime props by their exact 50-ms onset fingerprints.

    Paired/symmetric fixtures may legitimately share a musical clock. A
    candidate is a *broad* repeating clock involving >=6 individual models,
    >=3 physically different families and >=4 distinct positive onsets.
    """
    displays = {}
    if layout is not None and Path(layout).is_file():
        for model in ET.parse(layout).getroot().findall("./models/model"):
            displays[model.get("name", "")] = model.get("DisplayAs", "")
    fingerprints = defaultdict(list)
    eligible = 0
    for element in root.findall("./ElementEffects/Element"):
        if element.get("type", "model") != "model":
            continue
        name = element.get("name", "")
        # Only ordinary Prime props are in scope: exclude approved band
        # performers, vocal faces, keyboard and custom spatial specialists.
        starts = set()
        for effect in element.findall("./EffectLayer/Effect") + element.findall("./SubModelEffectLayer/Effect"):
            if effect.get("sourceMethod") != "layout_prime_placement":
                continue
            try:
                start = int(effect.get("startTime", "0"))
            except ValueError:
                continue
            if start > 0:
                starts.add(start // 50)
        if len(starts) < 4:
            continue
        eligible += 1
        fingerprints[tuple(sorted(starts))].append((name, _family(name, displays.get(name, ""))))

    candidates = []
    for starts, members in fingerprints.items():
        families = sorted(set(family for _, family in members))
        if len(members) >= 6 and len(families) >= 3:
            candidates.append({
                "models": len(members),
                "families": families,
                "distinct_onsets": len(starts),
                "first_onsets_ms": [onset * 50 for onset in starts[:8]],
                "sample_models": sorted(name for name, _ in members)[:12],
            })
    candidates.sort(key=lambda item: (-item["models"], -len(item["families"])))
    return {
        "schema": "helix.yard_onset_independence.v1",
        "scope": "layout_prime_placement source-tagged XSQ effects only",
        "eligible_models": eligible,
        "broad_common_clock_count": len(candidates),
        "candidates": candidates[:10],
        "status": "suspected_synchronized_yard" if candidates else "no_broad_common_clock_detected",
        "native_fseq_verified": False,
        "owner_approved": False,
    }


def assert_yard_sync_safe(audit: dict) -> None:
    if audit["broad_common_clock_count"]:
        candidate = audit["candidates"][0]
        raise ValueError(
            "Broad repeated yard onset clock detected: "
            f"{candidate['models']} models across {len(candidate['families'])} "
            "physical families. Inspect source routing, not brightness thresholds."
        )
