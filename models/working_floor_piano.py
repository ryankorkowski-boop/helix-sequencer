from __future__ import annotations

from typing import Any, Iterable, Mapping

from models.helixia_props import build_floor_piano_structure, prop_definition_to_dict

FLOOR_PIANO_SCHEMA = "helix.working_floor_piano.v1"
FLOOR_PIANO_KEY_COUNT = 24
MIN_NOTE = 36.0
MAX_NOTE = 84.0


def _key_name(index: int) -> str:
    return f"HX_FLOOR_PIANO_KEY_{max(1, min(FLOOR_PIANO_KEY_COUNT, int(index))):02d}"


def _key_index_for_pitch(pitch_midi: float | None) -> int:
    if pitch_midi is None:
        return 12
    note = max(MIN_NOTE, min(MAX_NOTE, float(pitch_midi)))
    normalized = (note - MIN_NOTE) / (MAX_NOTE - MIN_NOTE)
    return max(1, min(FLOOR_PIANO_KEY_COUNT, int(normalized * (FLOOR_PIANO_KEY_COUNT - 1)) + 1))


def _event_start_ms(event: Any) -> int:
    return max(0, int(getattr(event, "start_ms", 0) or 0))


def _event_end_ms(event: Any, fallback_ms: int = 180) -> int:
    start_ms = _event_start_ms(event)
    return max(start_ms + 50, int(getattr(event, "end_ms", start_ms + fallback_ms) or (start_ms + fallback_ms)))


def _extract_notes(event: Any) -> list[tuple[float, float]]:
    notes: list[tuple[float, float]] = []
    for raw_note in list(getattr(event, "notes", []) or []):
        try:
            if isinstance(raw_note, (list, tuple)) and raw_note:
                pitch = float(raw_note[0])
                velocity = float(raw_note[1]) if len(raw_note) > 1 else 0.62
            else:
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


def _default_cues() -> list[dict[str, Any]]:
    return [
        {"start_ms": 0, "end_ms": 140, "kind": "bass_kick_key", "submodel": "HX_FLOOR_PIANO_KEY_01", "secondary_submodels": ["HX_FLOOR_PIANO_BASE_FRAME", "HX_FLOOR_PIANO_KEY_GROUP"], "intensity": 0.95, "motion": "floor_piano_low_key_step"},
        {"start_ms": 140, "end_ms": 280, "kind": "mid_chord_step", "submodel": "HX_FLOOR_PIANO_KEY_12", "secondary_submodels": ["HX_FLOOR_PIANO_KEY_10", "HX_FLOOR_PIANO_KEY_14"], "intensity": 0.78, "motion": "floor_piano_chord_step"},
        {"start_ms": 280, "end_ms": 420, "kind": "high_melody_key", "submodel": "HX_FLOOR_PIANO_KEY_21", "secondary_submodels": ["HX_FLOOR_PIANO_KEY_20", "HX_FLOOR_PIANO_KEY_22"], "intensity": 0.72, "motion": "floor_piano_high_key_step"},
        {"start_ms": 420, "end_ms": 620, "kind": "keyboard_sweep", "submodel": "HX_FLOOR_PIANO_KEY_GROUP", "secondary_submodels": ["HX_FLOOR_PIANO_BASE_LEFT_EDGE", "HX_FLOOR_PIANO_BASE_RIGHT_EDGE"], "intensity": 0.66, "motion": "floor_piano_left_to_right_sweep"},
    ]


FLOOR_PIANO_DEFAULT_CUES = _default_cues()


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
        {"frame": index, "time_ms": int(cue["start_ms"]), "active_submodel": str(cue["submodel"]), "secondary_submodels": list(cue["secondary_submodels"]), "motion": str(cue["motion"]), "intensity": float(cue["intensity"])}
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
        "validation": {"has_required_submodels": not missing_required, "has_animation_frames": bool(animation_frames), "has_24_keys": all(_key_name(index) in available_submodels for index in range(1, FLOOR_PIANO_KEY_COUNT + 1))},
        "xlights_export_contract": {"target_model_type": "stage_prop_with_key_submodels", "node_order": "left_to_right_low_to_high", "must_export_submodels": required_submodels},
    }


def _add_reactive_cue(reactive_cues: list[dict[str, Any]], *, start_ms: int, end_ms: int, kind: str, submodel: str, key_index: int | None, source: str, velocity: float = 0.62, confidence: float = 0.5, role: str = "note_key", **extra: Any) -> None:
    cue = {"performer": "floor_piano", "role": role, "start_ms": start_ms, "end_ms": end_ms, "kind": kind, "submodel": submodel, "velocity": round(float(velocity), 3), "confidence": round(float(confidence), 3), "source": source, "xlights": {"effect": "On", "target_submodel": submodel}}
    if key_index is not None:
        cue["key_index"] = key_index
    cue.update(extra)
    reactive_cues.append(cue)


def build_reactive_floor_piano(*, note_events: Iterable[Any] = (), beat_ms: Iterable[int] = (), drum_cues: Iterable[Mapping[str, Any]] = (), phrase_hits: Iterable[int] = ()) -> dict[str, Any]:
    payload = build_working_floor_piano()
    reactive_cues: list[dict[str, Any]] = []

    for event in sorted(list(note_events), key=_event_start_ms):
        start_ms = _event_start_ms(event)
        end_ms = _event_end_ms(event)
        for idx, (pitch, velocity) in enumerate(_extract_notes(event)[:6]):
            key_index = _key_index_for_pitch(pitch)
            _add_reactive_cue(reactive_cues, start_ms=start_ms + idx * 12, end_ms=min(end_ms, start_ms + idx * 12 + 220), kind="note_key_press", submodel=_key_name(key_index), key_index=key_index, source="note_events", velocity=velocity, confidence=0.78, pitch_midi=round(pitch, 2))

    for cue in drum_cues:
        hook = dict(cue.get("visual_effect", {}).get("player_piano_hook", {}) or cue.get("player_piano_hook", {}) or {})
        if not hook.get("enabled"):
            continue
        start_ms = int(cue.get("start_ms", 0) or 0)
        drum_type = str(cue.get("kind", cue.get("drum_type", "drum")))
        key_index = {"kick": 1, "snare": 9, "hihat": 17, "hi_hat": 17, "cymbal": 22, "tom": 13}.get(drum_type, 12)
        _add_reactive_cue(reactive_cues, start_ms=start_ms, end_ms=start_ms + 120, kind="drum_hook_key_press", submodel=_key_name(key_index), key_index=key_index, source="player_piano_hook", velocity=float(hook.get("velocity", cue.get("velocity", 0.62)) or 0.62), confidence=float(cue.get("confidence", 0.5) or 0.5), role="drum_hook_key", drum_type=drum_type)

    for idx, mark in enumerate(sorted(set(int(value) for value in beat_ms))[:256]):
        if idx % 4 == 0:
            key_index = 6 + (idx // 4 % 12)
            _add_reactive_cue(reactive_cues, start_ms=mark, end_ms=mark + 90, kind="beat_key_step", submodel=_key_name(key_index), key_index=key_index, source="beat_fallback", velocity=0.34, confidence=0.34, role="beat_step")

    for mark in sorted(set(int(value) for value in phrase_hits)):
        _add_reactive_cue(reactive_cues, start_ms=mark, end_ms=mark + 420, kind="floor_piano_sweep", submodel="HX_FLOOR_PIANO_KEY_GROUP", key_index=None, source="phrase_hit", velocity=0.68, confidence=0.56, role="phrase_sweep", secondary_submodels=["HX_FLOOR_PIANO_BASE_LEFT_EDGE", "HX_FLOOR_PIANO_BASE_RIGHT_EDGE"])

    reactive_cues.sort(key=lambda cue: (int(cue["start_ms"]), str(cue["kind"]), str(cue["submodel"])))
    payload.update({
        "status": "reactive_working_stage_prop_slice",
        "reactive_cues": reactive_cues,
        "reactive_debug": {"schema": "helix.working_floor_piano.reactivity.v1", "cue_count": len(reactive_cues), "cue_targets": sorted({str(cue.get("submodel", "")) for cue in reactive_cues if cue.get("submodel")}), "uses_note_events": any(cue.get("source") == "note_events" for cue in reactive_cues), "uses_player_piano_hooks": any(cue.get("source") == "player_piano_hook" for cue in reactive_cues), "uses_beat_fallback": any(cue.get("source") == "beat_fallback" for cue in reactive_cues), "uses_phrase_hits": any(cue.get("source") == "phrase_hit" for cue in reactive_cues)},
        "validation": {**dict(payload["validation"]), "has_reactive_cues": bool(reactive_cues), "reactive_cues_target_existing_submodels": all(str(cue.get("submodel", "")) in payload["available_submodels"] for cue in reactive_cues)},
    })
    return payload
