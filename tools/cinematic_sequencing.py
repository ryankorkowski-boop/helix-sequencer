"""Cinematic sequencing layer for Helix effect rows.

This layer restores the show-arc rulebook behavior for the new stem pipeline:
- repeated verses/choruses should grow instead of resetting
- chorus should generally exceed verse intensity
- finale should reserve peak brightness and broadest coverage
- buildup/drop events should receive controlled escalation

It operates on effect-row dictionaries so it can sit between realism mapping and
stabilization without changing lower-level stem routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SECTION_ORDER = {
    "intro": 0,
    "verse": 1,
    "pre_chorus": 2,
    "build": 3,
    "chorus": 4,
    "bridge": 5,
    "drop": 6,
    "finale": 7,
    "outro": 5,
}

PEAK_INTENTS = {"drop", "hit", "finale", "chorus_hit"}
BUILD_INTENTS = {"build", "buildup", "pre_drop", "pre-chorus", "pre_chorus"}
VOCAL_INTENTS = {"vocal", "lead_vocal", "female_vocal", "backup_vocal"}


@dataclass(frozen=True)
class CinematicConfig:
    min_scale: float = 0.55
    max_scale: float = 1.0
    finale_scale: float = 1.0
    chorus_bonus: float = 0.12
    build_bonus: float = 0.08
    drop_bonus: float = 0.16
    vocal_protection_floor: float = 0.62


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _section(row: dict) -> str:
    raw = str(row.get("section", row.get("intent", "unknown"))).lower().replace(" ", "_")
    for section in SECTION_ORDER:
        if section in raw:
            return section
    return "unknown"


def _song_position(row: dict, song_end: float) -> float:
    if song_end <= 0:
        return 0.0
    return _clamp(float(row.get("start", 0.0)) / song_end)


def _base_arc_scale(position: float, config: CinematicConfig) -> float:
    # Smoothly grows through the song. The quadratic curve keeps early sections
    # restrained and lets the final third bloom.
    return config.min_scale + (config.max_scale - config.min_scale) * (position ** 0.72)


def _section_bonus(section: str, intent: str, config: CinematicConfig) -> float:
    bonus = 0.0
    if section == "chorus":
        bonus += config.chorus_bonus
    if section in {"build", "pre_chorus"} or intent in BUILD_INTENTS:
        bonus += config.build_bonus
    if section in {"drop", "finale"} or intent in PEAK_INTENTS:
        bonus += config.drop_bonus
    if section == "finale":
        bonus += 0.25
    return bonus


def _coverage_scale(section: str, position: float, intent: str) -> float:
    if section == "finale" or intent in PEAK_INTENTS:
        return 1.0
    if section == "chorus":
        return _clamp(0.68 + position * 0.22)
    if section in {"build", "pre_chorus"}:
        return _clamp(0.55 + position * 0.24)
    if section == "verse":
        return _clamp(0.42 + position * 0.18)
    if section == "intro":
        return 0.35
    return _clamp(0.48 + position * 0.2)


def apply_cinematic_arc(rows: Iterable[dict], config: CinematicConfig = CinematicConfig()) -> list[dict]:
    """Apply a cinematic song arc to effect rows.

    The function is deterministic. It does not delete rows; it annotates them
    and scales intensity/coverage so later stabilization can make informed
    pruning decisions.
    """

    row_list = [dict(row) for row in rows]
    if not row_list:
        return []

    song_end = max(float(row.get("start", 0.0)) + float(row.get("duration", 0.0)) for row in row_list)
    section_counts: dict[str, int] = {}
    output: list[dict] = []

    for row in sorted(row_list, key=lambda item: (float(item.get("start", 0.0)), str(item.get("model", "")))):
        section = _section(row)
        intent = str(row.get("intent", "")).lower().replace(" ", "_")
        position = _song_position(row, song_end)
        section_counts[section] = section_counts.get(section, 0) + 1
        repeat_index = section_counts[section]

        scale = _base_arc_scale(position, config) + _section_bonus(section, intent, config)
        # Repeated section appearances should climb. This preserves the rule:
        # verse_2 > verse_1, chorus_2 > chorus_1, etc.
        if section in {"verse", "chorus", "build", "drop"}:
            scale += min(0.18, (repeat_index - 1) * 0.035)

        if section == "finale":
            scale = config.finale_scale

        if intent in VOCAL_INTENTS or "face" in str(row.get("effect", "")):
            scale = max(scale, config.vocal_protection_floor)

        coverage = _coverage_scale(section, position, intent)
        intensity = _clamp(float(row.get("intensity", 0.5)) * _clamp(scale, config.min_scale, 1.25))

        row["intensity"] = round(intensity, 3)
        row["cinematicScale"] = round(_clamp(scale, config.min_scale, 1.25), 3)
        row["coverageScale"] = round(coverage, 3)
        row["songPosition"] = round(position, 3)
        row["section"] = section
        row["sectionRepeatIndex"] = repeat_index
        row["arcRole"] = "peak" if section == "finale" or intent in PEAK_INTENTS else ("build" if section in {"build", "pre_chorus"} or intent in BUILD_INTENTS else "support")
        output.append(row)

    return output
