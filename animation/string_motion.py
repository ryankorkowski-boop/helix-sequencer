from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from audio.instrument_detection import InstrumentEvent


@dataclass(frozen=True)
class StringMotionConfig:
    guitar_delay_min_ms: int = 12
    guitar_delay_max_ms: int = 46
    bass_delay_min_ms: int = 24
    bass_delay_max_ms: int = 72
    seed: int = 414


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _string_index_for_pitch(pitch_midi: float | None) -> int:
    if pitch_midi is None:
        return 2
    clamped = min(67.0, max(36.0, float(pitch_midi)))
    return int(min(4, max(1, round(((clamped - 36.0) / 31.0) * 3.0) + 1)))


def _neck_position_for_pitch(pitch_midi: float | None) -> int:
    if pitch_midi is None:
        return 2
    clamped = min(84.0, max(42.0, float(pitch_midi)))
    return int(min(4, max(1, round(((clamped - 42.0) / 42.0) * 3.0) + 1)))


def _part_label(parts: Iterable[Any], target_ms: int) -> str:
    for part in parts:
        start_ms = int(getattr(part, "start_ms", 0) or 0)
        end_ms = int(getattr(part, "end_ms", start_ms) or start_ms)
        if start_ms <= target_ms < end_ms:
            return str(getattr(part, "label", "SECTION") or "SECTION").upper()
    return "SECTION"


def _focus_at(sync_payload: Mapping[str, Any] | None, target_ms: int) -> str:
    for frame in list((sync_payload or {}).get("performer_focus", []) or []):
        start_ms = int(frame.get("start_ms", 0) or 0)
        end_ms = int(frame.get("end_ms", start_ms) or start_ms)
        if start_ms <= target_ms < end_ms:
            return str(frame.get("primary_focus", "") or "")
    for frame in list((sync_payload or {}).get("state_frames", []) or []):
        start_ms = int(frame.get("start_ms", 0) or 0)
        end_ms = int(frame.get("end_ms", start_ms) or start_ms)
        if start_ms <= target_ms < end_ms:
            return str(frame.get("primary_focus", "") or "")
    return ""


def _energy_allocation(sync_payload: Mapping[str, Any] | None, performer: str, target_ms: int) -> float | None:
    for frame in list((sync_payload or {}).get("energy_distributions", []) or []):
        start_ms = int(frame.get("start_ms", 0) or 0)
        end_ms = int(frame.get("end_ms", start_ms) or start_ms)
        if start_ms <= target_ms < end_ms:
            allocations = dict(frame.get("allocations", {}) or {})
            if performer in allocations:
                try:
                    return float(allocations[performer])
                except (TypeError, ValueError):
                    return None
    return None


def _sync_scale(sync_payload: Mapping[str, Any] | None, performer: str, target_ms: int) -> float:
    focus = _focus_at(sync_payload, target_ms)
    allocation = _energy_allocation(sync_payload, performer, target_ms)
    scale = 1.0
    if focus == performer:
        scale += 0.28
    elif focus and focus not in {"", performer}:
        scale -= 0.18
    if allocation is not None:
        scale *= 0.78 + _clamp(allocation) * 0.58
    return _clamp(scale, 0.45, 1.35)


def build_guitar_motion_cues(
    events: Iterable[InstrumentEvent],
    *,
    parts: Iterable[Any] = (),
    band_sync_payload: Mapping[str, Any] | None = None,
    config: StringMotionConfig = StringMotionConfig(),
) -> list[dict[str, Any]]:
    rng = random.Random(config.seed)
    cues: list[dict[str, Any]] = []
    stroke_down = True
    for idx, event in enumerate(sorted(events, key=lambda item: item.start_ms)):
        delay = rng.randint(config.guitar_delay_min_ms, config.guitar_delay_max_ms)
        if event.event_type in {"sustained_note"}:
            delay += 18
        softened = event.confidence < 0.42 or (idx % 13 == 7)
        intensity = event.intensity * (0.72 if softened else 1.0) * _sync_scale(band_sync_payload, "guitarist", event.start_ms)
        direction = "downstroke" if stroke_down else "upstroke"
        if event.event_type in {"strum", "picking"}:
            stroke_down = not stroke_down
        submodel = {
            "strum": "strum_zone",
            "picking": "strum_zone",
            "chord_change": "fret_zone",
            "sustained_note": "guitar_body",
        }.get(event.event_type, "strum_zone")
        start_ms = max(0, event.start_ms + delay)
        duration = max(110, min(680, event.end_ms - event.start_ms))
        cues.append(
            {
                "performer": "guitarist",
                "start_ms": start_ms,
                "end_ms": start_ms + duration,
                "kind": event.event_type,
                "section": _part_label(parts, event.start_ms),
                "submodel": submodel,
                "neck_position": _neck_position_for_pitch(event.pitch_midi),
                "pitch_midi": round(float(event.pitch_midi), 2) if event.pitch_midi is not None else None,
                "motion": {
                    "stroke": direction,
                    "amplitude": round(_clamp(0.28 + intensity * (0.45 if event.event_type == "picking" else 0.68)), 3),
                    "tightness": "tight" if duration < 210 else "expressive",
                    "humanized_offset_ms": delay,
                    "softened_hit": softened,
                    "micro_idle": event.event_type in {"sustained_note", "chord_change"},
                    "vibrato": event.event_type == "sustained_note",
                },
                "expression": {
                    "brightness": round(_clamp(intensity * (1.12 if event.event_type == "strum" else 0.88)), 3),
                    "accent": bool(intensity >= 0.78 or event.event_type == "chord_change"),
                    "phrase_emphasis": idx % 8 == 0,
                },
                "spatial_impulse": {
                    "enabled": event.event_type in {"strum", "chord_change"},
                    "mode": "guitar_sweep",
                    "direction": "stage_left_to_right" if direction == "downstroke" else "stage_right_to_left",
                    "strength": round(_clamp(intensity * event.confidence), 3),
                },
                "confidence": round(event.confidence, 3),
                "source_reason": event.reason,
            }
        )
    return cues


def build_bass_motion_cues(
    events: Iterable[InstrumentEvent],
    *,
    parts: Iterable[Any] = (),
    band_sync_payload: Mapping[str, Any] | None = None,
    config: StringMotionConfig = StringMotionConfig(),
) -> list[dict[str, Any]]:
    rng = random.Random(config.seed + 17)
    cues: list[dict[str, Any]] = []
    for idx, event in enumerate(sorted(events, key=lambda item: item.start_ms)):
        delay = rng.randint(config.bass_delay_min_ms, config.bass_delay_max_ms)
        double_pluck = event.event_type == "pluck" and idx % 9 == 4 and event.confidence >= 0.55
        intensity = event.intensity * _sync_scale(band_sync_payload, "bassist", event.start_ms)
        submodel = {
            "pluck": "pluck_zone",
            "sustained_note": "bass_body",
            "transition": "neck_zone",
        }.get(event.event_type, "pluck_zone")
        start_ms = max(0, event.start_ms + delay)
        duration = max(170, min(880, event.end_ms - event.start_ms + (90 if double_pluck else 0)))
        cues.append(
            {
                "performer": "bassist",
                "start_ms": start_ms,
                "end_ms": start_ms + duration,
                "kind": event.event_type,
                "section": _part_label(parts, event.start_ms),
                "submodel": submodel,
                "string_index": _string_index_for_pitch(event.pitch_midi),
                "neck_position": _neck_position_for_pitch(event.pitch_midi),
                "pitch_midi": round(float(event.pitch_midi), 2) if event.pitch_midi is not None else 43.0,
                "motion": {
                    "weight": "heavy",
                    "amplitude": round(_clamp(0.22 + intensity * 0.62), 3),
                    "humanized_offset_ms": delay,
                    "body_sway": True,
                    "double_pluck": double_pluck,
                    "vibrato": event.event_type == "sustained_note",
                },
                "expression": {
                    "brightness": round(_clamp(intensity * 0.72), 3),
                    "low_frequency_emphasis": round(_clamp(intensity * 1.1), 3),
                    "accent": bool(double_pluck or idx % 4 == 0),
                    "phrase_emphasis": idx % 8 == 0,
                },
                "spatial_impulse": {
                    "enabled": event.event_type == "pluck",
                    "mode": "ground_level_bass_pulse",
                    "direction": "floor_outward",
                    "strength": round(_clamp(intensity * event.confidence), 3),
                },
                "confidence": round(event.confidence, 3),
                "source_reason": event.reason,
                "head_bob": event.event_type == "pluck",
            }
        )
    return cues
