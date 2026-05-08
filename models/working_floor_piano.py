from __future__ import annotations

from typing import Any, Iterable, Mapping

from models.helixia_props import build_floor_piano_structure, prop_definition_to_dict


FLOOR_PIANO_SCHEMA = "helix.working_floor_piano.v1"
FLOOR_PIANO_KEY_COUNT = 24
FLOOR_PIANO_MIN_MIDI = 36.0
FLOOR_PIANO_MID_MIDI = 60.0
FLOOR_PIANO_MAX_MIDI = 84.0


FLOOR_PIANO_DEFAULT_CUES = [
    {
        "start_ms": 0,
        "end_ms": 140,
        "kind": "bass_kick_key",
        "submodel": "HX_FLOOR_PIANO_KEY_01",
        "secondary_submodels": ["HX_FLOOR_PIANO_BASE_FRAME", "HX_FLOOR_PIANO_KEY_GROUP"],
        "intensity": 0.95,
        "motion": "floor_piano_low_key_step",
        "xlights_effect_hint": "Percussive low-key flash on kick or bass pulse",
    },
    {
        "start_ms": 140,
        "end_ms": 280,
        "kind": "mid_chord_step",
        "submodel": "HX_FLOOR_PIANO_KEY_12",
        "secondary_submodels": ["HX_FLOOR_PIANO_KEY_10", "HX_FLOOR_PIANO_KEY_14"],
        "intensity": 0.78,
        "motion": "floor_piano_chord_step",
        "xlights_effect_hint": "Three-key chord splash from note clusters or part hits",
    },
    {
        "start_ms": 280,
        "end_ms": 420,
        "kind": "high_melody_key",
        "submodel": "HX_FLOOR_PIANO_KEY_21",
        "secondary_submodels": ["HX_FLOOR_PIANO_KEY_20", "HX_FLOOR_PIANO_KEY_22"],
        "intensity": 0.72,
        "motion": "floor_piano_high_key_step",
        "xlights_effect_hint": "High-key sparkle for vocal/guitar melody notes",
    },
    {
        "start_ms": 420,
        "end_ms": 620,
        "kind": "keyboard_sweep",
        "submodel": "HX_FLOOR_PIANO_KEY_GROUP",
        "secondary_submodels": ["HX_FLOOR_PIANO_BASE_LEFT_EDGE", "HX_FLOOR_PIANO_BASE_RIGHT_EDGE"],
        "intensity": 0.66,
        "motion": "floor_piano_left_to_right_sweep",
        "xlights_effect_hint": "Short sweep across all keys on phrase or fill transition",
    },
]


def _key_name(index: int) -> str:
    clamped = max(1, min(FLOOR_PIANO_KEY_COUNT, int(index)))
    return f"HX_FLOOR_PIANO_KEY_{clamped:02d}"


def _key_index_for_pitch(pitch_midi: float | None) -> int:
    """Map MIDI pitches onto the 24 physical floor keys.

    The floor piano is a stage prop, not a full chromatic keyboard. We pin the
    useful musical range to stable visual anchors:
    - MIDI 36 -> key 01
    - MIDI 60 -> key 12
    - MIDI 84 -> key 24
    """

    if pitch_midi is None:
        return 12
    clamped = max(FLOOR_PIANO_MIN_MIDI, min(FLOOR_PIANO_MAX_MIDI, float(pitch_midi)))
    if clamped <= FLOOR_PIANO_MID_MIDI:
        ratio = (clamped - FLOOR_PIANO_MIN_MIDI) / (FLOOR_PIANO_MID_MIDI - FLOOR_PIANO_MIN_MIDI)
        return max(1, min(12, round(1 + ratio * 11)))
    ratio = (clamped - FLOOR_PIANO_MID_MIDI) / (FLOOR_PIANO_MAX_MIDI - FLOOR_PIANO_MID_MIDI)
    return max(12, min(FLOOR_PIANO_KEY_COUNT, round(12 + ratio * 12)))


def _event_start_ms(event: Any) -> int:
    return max(0, int(getattr(event, "start_ms", 0) or 0))


def _event_end_ms(event: Any, fallback_ms: int = 180) -> int:
    start_ms = _event_start_ms(event)
    return max(start_ms + 50, int(getattr(event, "end_ms", start_ms + fallback_ms) or (start_ms + fallback_ms)))


def _extract_notes(event: Any) -> list[tuple[float, float]]:
    notes: list[tuple[float, float]] = []
    for raw_note in list(getattr(event, "notes", []) or []):
        if isinstance(raw_note, (list, tuple)) and raw_note:
            try:
                pitch = float(raw_note[0])
                velocity = float(raw_note[1]) if len(raw_note) > 1 else 0.62
                notes.append((pitch, max(0.0, min(1.0, velocity))))
            except (TypeError, ValueError):
                continue
        else:
            try:
                pitch = float(getattr(raw_note, "pitch"))
                velocity = float(getattr(raw_note, "velocity", 0.62))
                notes.append((pitch, max(0.0, min(1.0, velocity))))
            except (AttributeError, TypeError, ValueError):
                continue
    if not notes and hasattr(event, "pitch"):
        try:
            notes.append((float(getattr(event, "pitch")), float(getattr(event, "velocity", 0.62))))
        except (TypeError, ValueError):
            pass
    return notes


def _all_submodel_names() -> list[str]:
    prop = build_floor_piano_structure()
    names = [submodel.name for submodel in prop.submodels]
    names.extend(group.name for group in prop.groups)
    names.extend(model.name for model in prop.models)
    return sorted(dict.fromkeys(names))


def build_working_floor_piano() -> dict[str, Any]:
    prop = build_floor_piano_structure()
    available_submodels = _all_submodel_names()
    required_submodels = [
        "HX_FLOOR_PIANO_BASE_FRAME",
        "HX_FLOOR_PIANO_BASE_LEFT_EDGE",
        "HX_FLOOR_PIANO_BASE_RIGHT_EDGE",
        "HX_FLOOR_PIANO_KEY_GROUP",
        *[_key_name(index) for index in range(1, FLOOR_PIANO_KEY_COUNT + 1)],
    ]
    missing_required = [name for name in required_submodels if name not in available_submodels]
    animation_frames = [
        {
            "frame": index,
            "time_ms": int(cue["start_ms"]),
            "active_submodel": str(cue["submodel"]),
            "secondary_submodels": list(cue["secondary_submodels"]),
            "motion": str(cue["motion"]),
            "intensity": float(cue["intensity"]),
        }
        for index, cue in enumerate(FLOOR_PIANO_DEFAULT_CUES)
    ]
    return {
        "schema": FLOOR_PIANO_SCHEMA,
        "role": "floor_piano",
        "status": "working_stage_prop_slice",
        "model_id": "HX_FLOOR_PIANO",
        "display_name": "Helixia Floor Piano",
        "key_count": FLOOR_PIANO_KEY_COUNT,
        "prop_structure": prop_definition_to_dict(prop),
        "required_submodels": required_submodels,
        "missing_required_submodels": missing_required,
        "available_submodels": available_submodels,
        "animation_frames": animation_frames,
        "default_cues": list(FLOOR_PIANO_DEFAULT_CUES),
        "validation": {
            "has_required_submodels": not missing_required,
            "has_animation_frames": bool(animation_frames),
            "has_24_keys": all(_key_name(index) in available_submodels for index in range(1, FLOOR_PIANO_KEY_COUNT + 1)),
        },
        "xlights_export_contract": {
            "target_model_type": "stage_prop_with_key_submodels",
            "node_order": "left_to_right_low_to_high",
            "must_export_submodels": required_submodels,
            "first_sequence_smoke_test": "Trigger low, mid, high, and full-key sweep cues across HX_FLOOR_PIANO_KEY_01..24.",
        },
    }


def build_reactive_floor_piano(
    *,
    note_events: Iterable[Any] = (),
    beat_ms: Iterable[int] = (),
    drum_cues: Iterable[Mapping[str, Any]] = (),
    phrase_hits: Iterable[int] = (),
) -> dict[str, Any]:
    """Build floor-piano cues from notes, beats, drum hooks, and phrase hits."""
    payload = build_working_floor_piano()
    reactive_cues: list[dict[str, Any]] = []

    for event in sorted(list(note_events), key=_event_start_ms):
        notes = _extract_notes(event)
        if not notes:
            continue
        start_ms = _event_start_ms(event)
        end_ms = _event_end_ms(event)
        for idx, (pitch, velocity) in enumerate(notes[:6]):
            key_index = _key_index_for_pitch(pitch)
            reactive_cues.append(
                {
                    "performer": "floor_piano",
                    "role": "note_key",
                    "start_ms": start_ms + idx * 12,
                    "end_ms": min(end_ms, start_ms + idx * 12 + 220),
                    "kind": "note_key_press",
                    "submodel": _key_name(key_index),
                    "pitch_midi": round(pitch, 2),
                    "key_index": key_index,
                    "velocity": round(velocity, 3),
                    "confidence": 0.78,
                    "source": "note_events",
                    "xlights": {"effect": "On", "timing_track": "notes", "target_submodel": _key_name(key_index)},
                }
            )

    for cue in drum_cues:
        hook = dict(cue.get("visual_effect", {}).get("player_piano_hook", {}) or cue.get("player_piano_hook", {}) or {})
        if not hook.get("enabled"):
            continue
        start_ms = int(cue.get("start_ms", 0) or 0)
        drum_type = str(cue.get("kind", cue.get("drum_type", "drum")))
        key_index = {"kick": 1, "snare": 9, "hihat": 17, "hi_hat": 17, "cymbal": 22, "tom": 13}.get(drum_type, 12)
        reactive_cues.append(
            {
                "performer": "floor_piano",
                "role": "drum_hook_key",
                "start_ms": start_ms,
                "end_ms": start_ms + 120,
                "kind": "drum_hook_key_press",
                "submodel": _key_name(key_index),
                "key_index": key_index,
                "velocity": float(hook.get("velocity", cue.get("velocity", 0.62)) or 0.62),
                "confidence": float(cue.get("confidence", 0.5) or 0.5),
                "source": "player_piano_hook",
                "drum_type": drum_type,
                "xlights": {"effect": "On", "timing_track": "drums", "target_submodel": _key_name(key_index)},
            }
        )

    for idx, mark in enumerate(sorted(set(int(value) for value in beat_ms))[:256]):
        if idx % 4 != 0:
            continue
        key_index = 6 + (idx // 4 % 12)
        reactive_cues.append(
            {
                "performer": "floor_piano",
                "role": "beat_step",
                "start_ms": mark,
                "end_ms": mark + 90,
                "kind": "beat_key_step",
                "submodel": _key_name(key_index),
                "key_index": key_index,
                "velocity": 0.34,
                "confidence": 0.34,
                "source": "beat_fallback",
                "xlights": {"effect": "On", "timing_track": "beat", "target_submodel": _key_name(key_index)},
            }
        )

    for mark in sorted(set(int(value) for value in phrase_hits)):
        reactive_cues.append(
            {
                "performer": "floor_piano",
                "role": "phrase_sweep",
                "start_ms": mark,
                "end_ms": mark + 420,
                "kind": "floor_piano_sweep",
                "submodel": "HX_FLOOR_PIANO_KEY_GROUP",
                "secondary_submodels": ["HX_FLOOR_PIANO_BASE_LEFT_EDGE", "HX_FLOOR_PIANO_BASE_RIGHT_EDGE"],
                "velocity": 0.68,
                "confidence": 0.56,
                "source": "phrase_hit",
                "xlights": {"effect": "Chase", "timing_track": "phrase", "target_submodel": "HX_FLOOR_PIANO_KEY_GROUP"},
            }
        )

    reactive_cues.sort(key=lambda cue: (int(cue["start_ms"]), str(cue["kind"]), str(cue["submodel"])))
    cue_targets = sorted({str(cue.get("submodel", "")) for cue in reactive_cues if cue.get("submodel")})
    payload.update(
        {
            "status": "reactive_working_stage_prop_slice",
            "reactive_cues": reactive_cues,
            "reactive_debug": {
                "schema": "helix.working_floor_piano.reactivity.v1",
                "cue_count": len(reactive_cues),
                "cue_targets": cue_targets,
                "uses_note_events": any(cue.get("source") == "note_events" for cue in reactive_cues),
                "uses_player_piano_hooks": any(cue.get("source") == "player_piano_hook" for cue in reactive_cues),
                "uses_beat_fallback": any(cue.get("source") == "beat_fallback" for cue in reactive_cues),
                "uses_phrase_hits": any(cue.get("source") == "phrase_hit" for cue in reactive_cues),
            },
            "validation": {
                **dict(payload["validation"]),
                "has_reactive_cues": bool(reactive_cues),
                "reactive_cues_target_existing_submodels": all(
                    str(cue.get("submodel", "")) in payload["available_submodels"] for cue in reactive_cues
                ),
            },
        }
    )
    return payload
