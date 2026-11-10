from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

from animation import string_motion
from audio import instrument_detection
from core import vocal_timeline
from models.snowman_geometry import build_snowman_template, validate_mouth_inside_head


WORKING_MEMBER_SCHEMA = "helix.working_band_member.v1"


BASSIST_DEFAULT_CUES = [
    {
        "start_ms": 0,
        "end_ms": 140,
        "kind": "pluck",
        "submodel": "pluck_zone",
        "secondary_submodels": ["bass_body", "right_arm"],
        "intensity": 0.90,
        "motion": "right_arm_pluck_in",
        "xlights_effect_hint": "On/Color Wash pulse on pluck_zone with short decay",
    },
    {
        "start_ms": 140,
        "end_ms": 280,
        "kind": "body_bob",
        "submodel": "band_body_core",
        "secondary_submodels": ["head", "body_top", "body_bottom"],
        "intensity": 0.48,
        "motion": "downbeat_body_bob",
        "xlights_effect_hint": "Dim shimmer or value curve on body core",
    },
    {
        "start_ms": 280,
        "end_ms": 420,
        "kind": "neck_hand",
        "submodel": "neck_zone",
        "secondary_submodels": ["bass_neck", "left_arm"],
        "intensity": 0.72,
        "motion": "left_arm_neck_shift",
        "xlights_effect_hint": "Short chase along neck_zone toward bass_scroll",
    },
    {
        "start_ms": 420,
        "end_ms": 560,
        "kind": "pluck_release",
        "submodel": "bass_body",
        "secondary_submodels": ["pluck_zone", "instrument_all"],
        "intensity": 0.55,
        "motion": "string_decay",
        "xlights_effect_hint": "Fade down instrument_all, leave bass_body warm sustain",
    },
]


GUITARIST_DEFAULT_CUES = [
    {
        "start_ms": 0,
        "end_ms": 120,
        "kind": "strum_down",
        "submodel": "strum_zone",
        "secondary_submodels": ["guitar_body", "right_arm"],
        "intensity": 0.88,
        "motion": "right_arm_downstroke",
        "xlights_effect_hint": "Fast pulse on strum_zone with sweep into guitar_body",
    },
    {
        "start_ms": 120,
        "end_ms": 260,
        "kind": "fret_change",
        "submodel": "fret_zone",
        "secondary_submodels": ["guitar_neck", "left_arm"],
        "intensity": 0.68,
        "motion": "left_arm_fret_shift",
        "xlights_effect_hint": "Short chase along fret_zone/guitar_neck",
    },
    {
        "start_ms": 260,
        "end_ms": 420,
        "kind": "guitar_sustain",
        "submodel": "guitar_body",
        "secondary_submodels": ["instrument_all", "band_body_core"],
        "intensity": 0.54,
        "motion": "body_sway_sustain",
        "xlights_effect_hint": "Sustain shimmer on guitar_body and low body sway",
    },
    {
        "start_ms": 420,
        "end_ms": 560,
        "kind": "strum_up",
        "submodel": "strum_zone",
        "secondary_submodels": ["guitar_neck", "instrument_all"],
        "intensity": 0.76,
        "motion": "right_arm_upstroke",
        "xlights_effect_hint": "Reverse sweep through strum_zone into guitar_neck",
    },
]


SINGER_DEFAULT_CUES = [
    {
        "start_ms": 0,
        "end_ms": 120,
        "kind": "mouth_open_A",
        "submodel": "mouth_A",
        "secondary_submodels": ["head", "mic_head"],
        "intensity": 0.92,
        "motion": "lead_vocal_open",
        "xlights_effect_hint": "Faces effect mouth_A on phoneme timing track",
    },
    {
        "start_ms": 120,
        "end_ms": 240,
        "kind": "mouth_E",
        "submodel": "mouth_E",
        "secondary_submodels": ["head", "mic_stand"],
        "intensity": 0.82,
        "motion": "lead_vocal_narrow",
        "xlights_effect_hint": "Faces effect mouth_E on phoneme timing track",
    },
    {
        "start_ms": 240,
        "end_ms": 360,
        "kind": "mouth_MBP",
        "submodel": "mouth_MBP",
        "secondary_submodels": ["head", "mouth_all"],
        "intensity": 0.78,
        "motion": "closed_lip_consonant",
        "xlights_effect_hint": "Faces effect mouth_MBP for M/B/P consonants",
    },
    {
        "start_ms": 360,
        "end_ms": 560,
        "kind": "mic_accent",
        "submodel": "mic_head",
        "secondary_submodels": ["mic_stand", "band_body_core"],
        "intensity": 0.64,
        "motion": "mic_hit_body_sway",
        "xlights_effect_hint": "Accent mic_head and body core on phrase hit",
    },
]


def _required_bassist_submodels() -> list[str]:
    return [
        "head",
        "left_arm",
        "right_arm",
        "body_top",
        "body_bottom",
        "band_body_core",
        "bass_body",
        "bass_neck",
        "bass_scroll",
        "pluck_zone",
        "neck_zone",
        "instrument_all",
        "mouth_all",
    ]


def _required_guitarist_submodels() -> list[str]:
    return [
        "head",
        "left_arm",
        "right_arm",
        "body_top",
        "body_bottom",
        "band_body_core",
        "guitar_body",
        "guitar_neck",
        "guitar_headstock",
        "strum_zone",
        "fret_zone",
        "instrument_all",
        "mouth_all",
    ]


def _required_singer_submodels() -> list[str]:
    return [
        "head",
        "left_arm",
        "right_arm",
        "body_top",
        "body_bottom",
        "band_body_core",
        "mic_stand",
        "mic_head",
        "instrument_all",
        "mouth_A",
        "mouth_E",
        "mouth_I",
        "mouth_O",
        "mouth_U",
        "mouth_MBP",
        "mouth_all",
    ]


def _default_animation_frames(cues: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "frame": index,
            "time_ms": int(cue["start_ms"]),
            "active_submodel": str(cue["submodel"]),
            "secondary_submodels": list(cue["secondary_submodels"]),
            "motion": str(cue["motion"]),
            "intensity": float(cue["intensity"]),
        }
        for index, cue in enumerate(cues)
    ]


def _build_working_member(
    *,
    role: str,
    required_submodels: list[str],
    default_cues: list[dict[str, Any]],
    smoke_test: str,
    canvas_size: int,
) -> dict[str, Any]:
    model = build_snowman_template(role, canvas_size)
    validation_issues = validate_mouth_inside_head(model)
    submodel_counts = {name: len(submodel.included_coordinates) for name, submodel in model.submodels.items()}
    missing_required = [name for name in required_submodels if name not in model.submodels]
    animation_frames = _default_animation_frames(default_cues)
    return {
        "schema": WORKING_MEMBER_SCHEMA,
        "role": role,
        "status": "working_member_slice",
        "model_id": model.id,
        "display_name": model.display_name,
        "canvas": asdict(model.canvas),
        "required_submodels": required_submodels,
        "missing_required_submodels": missing_required,
        "submodel_node_counts": submodel_counts,
        "mouth_shapes": sorted(model.mouth_regions),
        "animation_frames": animation_frames,
        "default_cues": list(default_cues),
        "validation": {
            "mouth_inside_head": not validation_issues,
            "issues": validation_issues,
            "has_required_submodels": not missing_required,
            "has_animation_frames": bool(animation_frames),
        },
        "xlights_export_contract": {
            "target_model_type": "custom_model_with_submodels",
            "node_order": "row_major_top_left_1_based",
            "must_export_submodels": required_submodels,
            "first_sequence_smoke_test": smoke_test,
        },
    }


def build_working_bassist(canvas_size: int = 64) -> dict[str, Any]:
    """Build the concrete snowman bassist performer package."""
    return _build_working_member(
        role="bassist",
        required_submodels=_required_bassist_submodels(),
        default_cues=BASSIST_DEFAULT_CUES,
        smoke_test="Apply the four default cues to pluck_zone, band_body_core, neck_zone, and bass_body over one 560ms bass phrase.",
        canvas_size=canvas_size,
    )


def build_working_guitarist(canvas_size: int = 64) -> dict[str, Any]:
    """Build the concrete snowman guitarist performer package."""
    return _build_working_member(
        role="guitarist",
        required_submodels=_required_guitarist_submodels(),
        default_cues=GUITARIST_DEFAULT_CUES,
        smoke_test="Apply the four default cues to strum_zone, fret_zone, guitar_body, and instrument_all over one 560ms guitar phrase.",
        canvas_size=canvas_size,
    )


def build_working_singer(canvas_size: int = 64) -> dict[str, Any]:
    """Build the concrete lead singer snowman performer package."""
    return _build_working_member(
        role="singer",
        required_submodels=_required_singer_submodels(),
        default_cues=SINGER_DEFAULT_CUES,
        smoke_test="Apply phoneme cues to mouth_A/E/I/O/U/MBP and phrase accents to mic_head over one lyric phrase.",
        canvas_size=canvas_size,
    )


def build_reactive_bassist_member(
    *,
    bass_peaks: Iterable[int] = (),
    note_events: Iterable[Any] = (),
    beat_ms: Iterable[int] = (),
    parts: Iterable[Any] = (),
    band_sync_payload: Mapping[str, Any] | None = None,
    canvas_size: int = 64,
) -> dict[str, Any]:
    """Build the bassist package with real audio/stem-timing reactive cues."""
    payload = build_working_bassist(canvas_size)
    note_event_list = list(note_events)
    bass_events, detection_debug = instrument_detection.derive_bass_events(
        bass_peaks,
        note_event_list,
        beat_ms=beat_ms,
    )
    reactive_cues = string_motion.build_bass_motion_cues(
        bass_events,
        parts=parts,
        band_sync_payload=band_sync_payload,
    )
    cue_targets = sorted({str(cue.get("submodel", "")) for cue in reactive_cues if cue.get("submodel")})
    payload.update(
        {
            "status": "reactive_working_member_slice",
            "reactive_cues": reactive_cues,
            "reactive_source_events": [event.to_dict() for event in bass_events],
            "reactive_debug": {
                "schema": "helix.working_bassist.reactivity.v1",
                "detection": dict(detection_debug),
                "cue_count": len(reactive_cues),
                "cue_targets": cue_targets,
                "uses_bass_peaks": "bass_peak_events" in detection_debug.get("sources", []),
                "uses_low_note_sustains": "low_note_duration" in detection_debug.get("sources", []),
                "uses_beat_fallback": detection_debug.get("fallback_mode") == "beat",
                "band_sync_applied": bool(band_sync_payload),
            },
            "validation": {
                **dict(payload["validation"]),
                "has_reactive_cues": bool(reactive_cues),
                "reactive_cues_target_existing_submodels": all(
                    str(cue.get("submodel", "")) in payload["submodel_node_counts"] for cue in reactive_cues
                ),
            },
        }
    )
    return payload


def build_reactive_guitarist_member(
    *,
    note_events: Iterable[Any] = (),
    onset_ms: Iterable[int] = (),
    beat_ms: Iterable[int] = (),
    parts: Iterable[Any] = (),
    band_sync_payload: Mapping[str, Any] | None = None,
    canvas_size: int = 64,
) -> dict[str, Any]:
    """Build the guitarist package with real audio/stem-timing reactive cues."""
    payload = build_working_guitarist(canvas_size)
    guitar_events, detection_debug = instrument_detection.derive_guitar_events(
        list(note_events),
        onset_ms=onset_ms,
        beat_ms=beat_ms,
    )
    reactive_cues = string_motion.build_guitar_motion_cues(
        guitar_events,
        parts=parts,
        band_sync_payload=band_sync_payload,
    )
    cue_targets = sorted({str(cue.get("submodel", "")) for cue in reactive_cues if cue.get("submodel")})
    event_types = sorted({str(event.event_type) for event in guitar_events})
    payload.update(
        {
            "status": "reactive_working_member_slice",
            "reactive_cues": reactive_cues,
            "reactive_source_events": [event.to_dict() for event in guitar_events],
            "reactive_debug": {
                "schema": "helix.working_guitarist.reactivity.v1",
                "detection": dict(detection_debug),
                "event_types": event_types,
                "cue_count": len(reactive_cues),
                "cue_targets": cue_targets,
                "uses_note_events": detection_debug.get("fallback_mode") == "note_events",
                "uses_rhythm_fallback": detection_debug.get("fallback_mode") == "rhythm_energy",
                "band_sync_applied": bool(band_sync_payload),
            },
            "validation": {
                **dict(payload["validation"]),
                "has_reactive_cues": bool(reactive_cues),
                "reactive_cues_target_existing_submodels": all(
                    str(cue.get("submodel", "")) in payload["submodel_node_counts"] for cue in reactive_cues
                ),
            },
        }
    )
    return payload


def _song_parts_from_raw(parts: Iterable[Any], vocal_peaks: Iterable[int]) -> list[vocal_timeline.SongPart]:
    return vocal_timeline.build_song_parts(parts, vocal_peaks_ms=vocal_peaks)


def build_reactive_singer_member(
    *,
    lyric_events: Iterable[Any] = (),
    vocal_peaks: Iterable[int] = (),
    parts: Iterable[Any] = (),
    canvas_size: int = 64,
) -> dict[str, Any]:
    """Build the singer package with lyric/phoneme timing reactive cues.

    Lyric events drive word and phoneme timing. If lyrics are unavailable,
    vocal peaks create a low-confidence energy fallback so the singer still
    animates instead of silently doing nothing.
    """
    payload = build_working_singer(canvas_size)
    vocal_peak_list = list(vocal_peaks)
    lyric_timeline = vocal_timeline.build_lyric_timeline(lyric_events, vocal_peaks_ms=vocal_peak_list)
    song_parts = _song_parts_from_raw(parts, vocal_peak_list)
    reactive_cues: list[dict[str, Any]] = []
    for event in lyric_timeline.phoneme_events:
        submodel = event.mouth_submodel
        reactive_cues.append(
            {
                "performer": "lead_singer",
                "role": "lead_vocal",
                "start_ms": event.start_ms,
                "end_ms": event.end_ms,
                "kind": "phoneme_face",
                "phoneme": event.phoneme,
                "mouth_shape": event.mouth_shape,
                "submodel": submodel,
                "mouth_submodel": submodel,
                "word_text": event.word_text,
                "section": vocal_timeline.part_name_at(song_parts, event.start_time),
                "confidence": round(event.confidence, 3),
                "xlights": {
                    "effect": "Faces",
                    "face_definition": "lead_singer_full",
                    "timing_track": "phoneme",
                    "target_submodel": submodel,
                },
            }
        )
    for line in lyric_timeline.lines:
        if not line.words:
            continue
        reactive_cues.append(
            {
                "performer": "lead_singer",
                "role": "phrase_accent",
                "start_ms": int(round(line.start_time * 1000.0)),
                "end_ms": min(int(round(line.end_time * 1000.0)), int(round(line.start_time * 1000.0)) + 280),
                "kind": "mic_phrase_hit",
                "submodel": "mic_head",
                "secondary_submodels": ["mic_stand", "band_body_core"],
                "lyric_text": line.text,
                "section": vocal_timeline.part_name_at(song_parts, line.start_time),
                "confidence": round(line.confidence, 3),
                "xlights": {"effect": "On", "timing_track": "word", "target_submodel": "mic_head"},
            }
        )
    cue_targets = sorted({str(cue.get("submodel", "")) for cue in reactive_cues if cue.get("submodel")})
    payload.update(
        {
            "status": "reactive_working_member_slice",
            "reactive_cues": reactive_cues,
            "reactive_source_events": {
                "lyric_lines": [vocal_timeline.as_plain_dict(line) for line in lyric_timeline.lines],
                "words": [vocal_timeline.as_plain_dict(word) for word in lyric_timeline.words],
                "phonemes": [vocal_timeline.as_plain_dict(event) for event in lyric_timeline.phoneme_events],
            },
            "reactive_debug": {
                "schema": "helix.working_singer.reactivity.v1",
                "timeline": dict(lyric_timeline.confidence_summary),
                "cue_count": len(reactive_cues),
                "cue_targets": cue_targets,
                "uses_lyrics": lyric_timeline.confidence_summary.get("source") == "lyrics",
                "uses_vocal_energy_fallback": lyric_timeline.confidence_summary.get("source") == "vocal_energy_fallback",
                "phoneme_count": len(lyric_timeline.phoneme_events),
                "word_count": len(lyric_timeline.words),
            },
            "validation": {
                **dict(payload["validation"]),
                "has_reactive_cues": bool(reactive_cues),
                "has_phoneme_cues": any(cue.get("kind") == "phoneme_face" for cue in reactive_cues),
                "reactive_cues_target_existing_submodels": all(
                    str(cue.get("submodel", "")) in payload["submodel_node_counts"] for cue in reactive_cues
                ),
            },
        }
    )
    return payload


if __name__ == "__main__":
    import json

    print(json.dumps(build_working_bassist(), indent=2))
