from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from core import vocal_timeline
from models.snowman_geometry import build_snowman_template, validate_mouth_inside_head
from models.working_band_member import WORKING_MEMBER_SCHEMA


FEMALE_SINGER_DEFAULT_CUES = [
    {
        "start_ms": 0,
        "end_ms": 100,
        "kind": "mouth_A_belt",
        "submodel": "mouth_A",
        "secondary_submodels": ["head", "mic_head"],
        "intensity": 0.96,
        "motion": "lead_female_vocal_open_belt",
        "xlights_effect_hint": "Faces effect mouth_A on phoneme timing track with strong lead-vocal brightness",
    },
    {
        "start_ms": 100,
        "end_ms": 220,
        "kind": "mouth_I_E_blend",
        "submodel": "mouth_I",
        "secondary_submodels": ["mouth_E", "head"],
        "intensity": 0.86,
        "motion": "lead_female_vocal_narrow_vowel",
        "xlights_effect_hint": "Faces effect mouth_I/E for bright vowel articulation",
    },
    {
        "start_ms": 220,
        "end_ms": 340,
        "kind": "mouth_O_round",
        "submodel": "mouth_O",
        "secondary_submodels": ["mouth_U", "head"],
        "intensity": 0.82,
        "motion": "lead_female_vocal_round_vowel",
        "xlights_effect_hint": "Faces effect mouth_O/U for round vowel articulation",
    },
    {
        "start_ms": 340,
        "end_ms": 560,
        "kind": "mic_sparkle_phrase_accent",
        "submodel": "mic_head",
        "secondary_submodels": ["mic_stand", "band_body_core", "mouth_all"],
        "intensity": 0.72,
        "motion": "female_lead_phrase_lift",
        "xlights_effect_hint": "Accent mic_head and mouth_all on phrase starts or high-confidence vocal peaks",
    },
]


def _required_female_singer_submodels() -> list[str]:
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


def _animation_frames() -> list[dict[str, Any]]:
    return [
        {
            "frame": index,
            "time_ms": int(cue["start_ms"]),
            "active_submodel": str(cue["submodel"]),
            "secondary_submodels": list(cue["secondary_submodels"]),
            "motion": str(cue["motion"]),
            "intensity": float(cue["intensity"]),
        }
        for index, cue in enumerate(FEMALE_SINGER_DEFAULT_CUES)
    ]


def build_working_female_singer(canvas_size: int = 64) -> dict[str, Any]:
    """Build a distinct female lead singer package using the singer geometry.

    The current geometry library has one singer snowman body. This wrapper keeps
    that proven geometry and gives the female singer her own performer role,
    cue set, export contract, and downstream face-definition identity.
    """
    model = build_snowman_template("singer", canvas_size)
    validation_issues = validate_mouth_inside_head(model)
    required_submodels = _required_female_singer_submodels()
    submodel_counts = {name: len(submodel.included_coordinates) for name, submodel in model.submodels.items()}
    missing_required = [name for name in required_submodels if name not in model.submodels]
    frames = _animation_frames()
    return {
        "schema": WORKING_MEMBER_SCHEMA,
        "role": "female_singer",
        "geometry_role": "singer",
        "status": "working_member_slice",
        "model_id": f"snowman_band_female_singer_{canvas_size}",
        "display_name": "Female Lead Singer Snowman",
        "canvas": asdict(model.canvas),
        "required_submodels": required_submodels,
        "missing_required_submodels": missing_required,
        "submodel_node_counts": submodel_counts,
        "mouth_shapes": sorted(model.mouth_regions),
        "animation_frames": frames,
        "default_cues": list(FEMALE_SINGER_DEFAULT_CUES),
        "validation": {
            "mouth_inside_head": not validation_issues,
            "issues": validation_issues,
            "has_required_submodels": not missing_required,
            "has_animation_frames": bool(frames),
        },
        "xlights_export_contract": {
            "target_model_type": "custom_model_with_submodels",
            "node_order": "row_major_top_left_1_based",
            "must_export_submodels": required_submodels,
            "face_definition": "female_singer_full",
            "first_sequence_smoke_test": "Apply phoneme cues to mouth_A/E/I/O/U/MBP and phrase sparkle accents to mic_head over one female lead lyric phrase.",
        },
    }


def _song_parts_from_raw(parts: Iterable[Any], vocal_peaks: Iterable[int]) -> list[vocal_timeline.SongPart]:
    return vocal_timeline.build_song_parts(parts, vocal_peaks_ms=vocal_peaks)


def build_reactive_female_singer_member(
    *,
    lyric_events: Iterable[Any] = (),
    vocal_peaks: Iterable[int] = (),
    parts: Iterable[Any] = (),
    canvas_size: int = 64,
) -> dict[str, Any]:
    """Build the female singer package with lyric/phoneme reactive cues."""
    payload = build_working_female_singer(canvas_size)
    vocal_peak_list = list(vocal_peaks)
    lyric_timeline = vocal_timeline.build_lyric_timeline(lyric_events, vocal_peaks_ms=vocal_peak_list)
    song_parts = _song_parts_from_raw(parts, vocal_peak_list)
    reactive_cues: list[dict[str, Any]] = []
    for event in lyric_timeline.phoneme_events:
        submodel = event.mouth_submodel
        reactive_cues.append(
            {
                "performer": "female_singer",
                "role": "female_lead_vocal",
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
                "expression": {
                    "brightness": round(min(1.0, 0.34 + event.confidence * 0.74), 3),
                    "lead_presence": 1.0,
                    "sparkle_accent": event.mouth_submodel in {"mouth_A", "mouth_I", "mouth_E"},
                },
                "xlights": {
                    "effect": "Faces",
                    "face_definition": "female_singer_full",
                    "timing_track": "phoneme",
                    "target_submodel": submodel,
                },
            }
        )
    for line in lyric_timeline.lines:
        if not line.words:
            continue
        start_ms = int(round(line.start_time * 1000.0))
        reactive_cues.append(
            {
                "performer": "female_singer",
                "role": "female_phrase_accent",
                "start_ms": start_ms,
                "end_ms": min(int(round(line.end_time * 1000.0)), start_ms + 320),
                "kind": "mic_sparkle_phrase_hit",
                "submodel": "mic_head",
                "secondary_submodels": ["mic_stand", "band_body_core", "mouth_all"],
                "lyric_text": line.text,
                "section": vocal_timeline.part_name_at(song_parts, line.start_time),
                "confidence": round(line.confidence, 3),
                "expression": {"brightness": round(min(1.0, 0.46 + line.confidence * 0.5), 3), "sparkle": True},
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
                "schema": "helix.working_female_singer.reactivity.v1",
                "timeline": dict(lyric_timeline.confidence_summary),
                "cue_count": len(reactive_cues),
                "cue_targets": cue_targets,
                "uses_lyrics": lyric_timeline.confidence_summary.get("source") == "lyrics",
                "uses_vocal_energy_fallback": lyric_timeline.confidence_summary.get("source") == "vocal_energy_fallback",
                "phoneme_count": len(lyric_timeline.phoneme_events),
                "word_count": len(lyric_timeline.words),
                "face_definition": "female_singer_full",
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
