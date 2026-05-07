from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from animation import drummer_motion
from effects import drum_effects
from mapping import drum_mapper
from models.snowman_geometry import build_snowman_template, validate_mouth_inside_head
from models.working_band_member import WORKING_MEMBER_SCHEMA


DRUMMER_DEFAULT_CUES = [
    {
        "start_ms": 0,
        "end_ms": 120,
        "kind": "kick_hit",
        "submodel": "kick",
        "secondary_submodels": ["drumkit_all", "body_bottom"],
        "intensity": 0.95,
        "motion": "foot_kick_pulse",
        "xlights_effect_hint": "Low-frequency glow on kick with floor-outward pulse",
    },
    {
        "start_ms": 120,
        "end_ms": 240,
        "kind": "snare_hit",
        "submodel": "snare",
        "secondary_submodels": ["left_stick", "drumkit_all"],
        "intensity": 0.86,
        "motion": "left_stick_snare_strike",
        "xlights_effect_hint": "Sharp flash on snare with left stick anticipation/rebound",
    },
    {
        "start_ms": 240,
        "end_ms": 340,
        "kind": "hihat_tick",
        "submodel": "hi_hat",
        "secondary_submodels": ["right_stick"],
        "intensity": 0.58,
        "motion": "right_stick_hat_tick",
        "xlights_effect_hint": "Rapid shimmer tick on hi_hat",
    },
    {
        "start_ms": 340,
        "end_ms": 620,
        "kind": "cymbal_wash",
        "submodel": "cymbal",
        "secondary_submodels": ["right_stick", "drumkit_all"],
        "intensity": 0.78,
        "motion": "right_stick_cymbal_crash",
        "xlights_effect_hint": "Wide bright wash on cymbal with long tail",
    },
]


def _required_drummer_submodels() -> list[str]:
    return [
        "head",
        "left_arm",
        "right_arm",
        "body_top",
        "body_bottom",
        "band_body_core",
        "kick",
        "snare",
        "tom",
        "cymbal",
        "hi_hat",
        "left_stick",
        "right_stick",
        "drumkit_all",
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
        for index, cue in enumerate(DRUMMER_DEFAULT_CUES)
    ]


def build_working_drummer(canvas_size: int = 64) -> dict[str, Any]:
    """Build the concrete snowman drummer performer package."""
    model = build_snowman_template("drummer", canvas_size)
    validation_issues = validate_mouth_inside_head(model)
    required_submodels = _required_drummer_submodels()
    submodel_counts = {name: len(submodel.included_coordinates) for name, submodel in model.submodels.items()}
    missing_required = [name for name in required_submodels if name not in model.submodels]
    frames = _animation_frames()
    return {
        "schema": WORKING_MEMBER_SCHEMA,
        "role": "drummer",
        "status": "working_member_slice",
        "model_id": model.id,
        "display_name": model.display_name,
        "canvas": asdict(model.canvas),
        "required_submodels": required_submodels,
        "missing_required_submodels": missing_required,
        "submodel_node_counts": submodel_counts,
        "mouth_shapes": sorted(model.mouth_regions),
        "animation_frames": frames,
        "default_cues": list(DRUMMER_DEFAULT_CUES),
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
            "first_sequence_smoke_test": "Apply kick/snare/hi_hat/cymbal cues with stick anticipation/rebound over one 620ms drum phrase.",
        },
    }


def _motion_submodels_for_hit(motion: dict[str, object]) -> list[str]:
    return [str(value) for value in list(motion.get("submodels", []) or [])]


def build_reactive_drummer_member(
    *,
    drum_event_streams: dict[str, list[Any]] | None = None,
    kicks: Iterable[int] = (),
    snares: Iterable[int] = (),
    hats: Iterable[int] = (),
    cymbals: Iterable[int] = (),
    canvas_size: int = 64,
) -> dict[str, Any]:
    """Build the drummer package with typed or legacy drum-timing reactive cues."""
    payload = build_working_drummer(canvas_size)
    resolved = drum_mapper.resolve_drum_streams(
        drum_event_streams,
        fallback_kicks=kicks,
        fallback_snares=snares,
        fallback_hats=hats,
        fallback_cymbals=cymbals,
    )
    events = list(resolved["events"])
    mapped_events = list(resolved["mapped_events"])
    motions = drummer_motion.build_drummer_motion(events)
    effect_cues = drum_effects.build_drum_effect_cues(events)
    motion_by_strike = {(str(motion.get("drum_type")), int(motion.get("strike_ms", 0))): motion for motion in motions}
    reactive_cues: list[dict[str, Any]] = []
    for index, mapped in enumerate(mapped_events):
        event = events[index]
        effect = effect_cues[index] if index < len(effect_cues) else {}
        nearest_motion = min(
            motions,
            key=lambda motion: abs(int(motion.get("strike_ms", 0)) - int(mapped["timestamp_ms"])),
        ) if motions else {}
        reactive_cues.append(
            {
                "performer": "drummer",
                "role": "drum_hit",
                "start_ms": int(effect.get("start_ms", mapped["timestamp_ms"])),
                "end_ms": int(effect.get("end_ms", int(mapped["timestamp_ms"]) + 140)),
                "kind": str(mapped["drum_type"]),
                "submodel": str(mapped["submodel"]),
                "composite_submodels": list(mapped.get("composite_submodels", [])),
                "velocity": mapped["velocity"],
                "confidence": mapped["confidence"],
                "frequency_band_info": mapped["frequency_band_info"],
                "cluster_id": mapped["cluster_id"],
                "source": mapped["source"],
                "motion": nearest_motion,
                "motion_submodels": _motion_submodels_for_hit(nearest_motion),
                "visual_effect": effect,
                "xlights": {
                    "effect": effect.get("effect", "drum_hit"),
                    "timing_track": "drums",
                    "target_submodel": str(mapped["submodel"]),
                    "layer": effect.get("layer", "accent"),
                },
            }
        )
    cue_targets = sorted({str(cue.get("submodel", "")) for cue in reactive_cues if cue.get("submodel")})
    payload.update(
        {
            "status": "reactive_working_member_slice",
            "reactive_cues": reactive_cues,
            "reactive_source_events": [event.to_dict() for event in events],
            "reactive_debug": {
                "schema": "helix.working_drummer.reactivity.v1",
                "fallback_mode": resolved["fallback_mode"],
                "counts": resolved["counts"],
                "cue_count": len(reactive_cues),
                "cue_targets": cue_targets,
                "mapped_events": mapped_events,
                "motion_events": motions,
                "effect_cues": effect_cues,
                "uses_typed_detection": resolved["fallback_mode"] == "typed_detection",
                "uses_legacy_marks": resolved["fallback_mode"] == "legacy_marks",
                "uses_drum_bus_distribution": resolved["fallback_mode"] == "drum_bus_distribution",
            },
            "validation": {
                **dict(payload["validation"]),
                "has_reactive_cues": bool(reactive_cues),
                "has_motion_events": bool(motions),
                "has_effect_cues": bool(effect_cues),
                "reactive_cues_target_existing_submodels": all(
                    str(cue.get("submodel", "")) in payload["submodel_node_counts"] for cue in reactive_cues
                ),
            },
        }
    )
    return payload
