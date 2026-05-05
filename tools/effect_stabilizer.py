"""Stabilize Helix effect rows before xLights export.

This layer prevents stem-driven output from becoming visually chaotic by:
- snapping timings to a small grid
- dropping near-duplicate triggers
- enforcing per-model overlap limits
- applying musical priority rules
- preserving higher-value performer actions over texture/noise
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


PRIORITY_BY_INTENT = {
    "drop": 100,
    "hit": 95,
    "kick": 90,
    "snare": 88,
    "cymbal": 82,
    "tom": 78,
    "hi_hat": 72,
    "hihat": 72,
    "beat": 70,
    "vocal": 68,
    "pluck": 64,
    "strum": 62,
    "note": 60,
    "build": 58,
    "texture": 20,
}

PRIORITY_BY_EFFECT = {
    "snare_crack": 95,
    "kick_thump": 92,
    "cymbal_decay": 84,
    "tom_roll": 80,
    "hat_tick": 72,
    "lead_face_phoneme": 88,
    "female_face_phoneme": 86,
    "backup_face_phoneme": 76,
    "string_ripple": 70,
    "bass_string_pulse": 70,
    "pick_flicker": 62,
    "bass_pluck": 62,
    "arm_motion": 48,
    "stick_motion": 52,
}


@dataclass(frozen=True)
class StabilizerConfig:
    timing_grid_seconds: float = 0.05
    duplicate_window_seconds: float = 0.04
    max_simultaneous_per_model: int = 3
    min_duration_seconds: float = 0.05
    max_duration_seconds: float = 4.0


def _priority(row: dict) -> int:
    effect = str(row.get("effect", ""))
    intent = str(row.get("intent", ""))
    return max(PRIORITY_BY_EFFECT.get(effect, 0), PRIORITY_BY_INTENT.get(intent, 0), int(float(row.get("intensity", 0.0)) * 50))


def _snap(value: float, grid: float) -> float:
    if grid <= 0:
        return round(value, 4)
    return round(round(value / grid) * grid, 4)


def _normalized_row(row: dict, config: StabilizerConfig) -> dict:
    out = dict(row)
    start = _snap(float(out.get("start", 0.0)), config.timing_grid_seconds)
    duration = max(config.min_duration_seconds, min(config.max_duration_seconds, float(out.get("duration", 0.1))))
    out["start"] = start
    out["duration"] = round(duration, 4)
    out["priority"] = _priority(out)
    return out


def _is_duplicate(a: dict, b: dict, window: float) -> bool:
    return (
        a.get("model") == b.get("model")
        and a.get("effect") == b.get("effect")
        and a.get("submodel") == b.get("submodel")
        and abs(float(a.get("start", 0.0)) - float(b.get("start", 0.0))) <= window
    )


def _overlaps(a: dict, b: dict) -> bool:
    a_start = float(a.get("start", 0.0))
    a_end = a_start + float(a.get("duration", 0.0))
    b_start = float(b.get("start", 0.0))
    b_end = b_start + float(b.get("duration", 0.0))
    return a_start < b_end and b_start < a_end


def stabilize_effect_rows(rows: Iterable[dict], config: StabilizerConfig = StabilizerConfig()) -> list[dict]:
    """Return stabilized effect rows sorted by time and priority."""

    normalized = [_normalized_row(row, config) for row in rows]
    normalized.sort(key=lambda row: (float(row["start"]), -int(row["priority"]), str(row.get("model", ""))))

    deduped: list[dict] = []
    for row in normalized:
        duplicate_index = next((i for i, existing in enumerate(deduped) if _is_duplicate(row, existing, config.duplicate_window_seconds)), None)
        if duplicate_index is None:
            deduped.append(row)
            continue
        if int(row["priority"]) > int(deduped[duplicate_index]["priority"]):
            deduped[duplicate_index] = row

    accepted: list[dict] = []
    for row in sorted(deduped, key=lambda item: (-int(item["priority"]), float(item["start"]))):
        model = row.get("model")
        overlapping_same_model = [existing for existing in accepted if existing.get("model") == model and _overlaps(row, existing)]
        if len(overlapping_same_model) >= config.max_simultaneous_per_model:
            lowest = min(overlapping_same_model, key=lambda item: int(item["priority"]))
            if int(row["priority"]) > int(lowest["priority"]):
                accepted.remove(lowest)
                accepted.append(row)
            continue
        accepted.append(row)

    final_rows = sorted(accepted, key=lambda row: (float(row["start"]), str(row.get("model", "")), -int(row["priority"])))
    for row in final_rows:
        row.pop("priority", None)
    return final_rows
