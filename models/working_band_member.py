from __future__ import annotations

from dataclasses import asdict
from typing import Any

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


def build_working_bassist(canvas_size: int = 64) -> dict[str, Any]:
    """Build the first concrete snowman band member artifact.

    This is intentionally narrow: it turns the bassist from a static placeholder
    template into a usable performer package with geometry, submodels, mouth
    shapes, validation, animation frames, and xLights-oriented sequencing hints.
    """
    model = build_snowman_template("bassist", canvas_size)
    validation_issues = validate_mouth_inside_head(model)
    submodel_counts = {name: len(submodel.included_coordinates) for name, submodel in model.submodels.items()}
    required_submodels = [
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
    missing_required = [name for name in required_submodels if name not in model.submodels]
    animation_frames = [
        {
            "frame": index,
            "time_ms": cue["start_ms"],
            "active_submodel": cue["submodel"],
            "secondary_submodels": cue["secondary_submodels"],
            "motion": cue["motion"],
            "intensity": cue["intensity"],
        }
        for index, cue in enumerate(BASSIST_DEFAULT_CUES)
    ]
    return {
        "schema": WORKING_MEMBER_SCHEMA,
        "role": "bassist",
        "status": "working_member_slice",
        "model_id": model.id,
        "display_name": model.display_name,
        "canvas": asdict(model.canvas),
        "required_submodels": required_submodels,
        "missing_required_submodels": missing_required,
        "submodel_node_counts": submodel_counts,
        "mouth_shapes": sorted(model.mouth_regions),
        "animation_frames": animation_frames,
        "default_cues": list(BASSIST_DEFAULT_CUES),
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
            "first_sequence_smoke_test": "Apply the four default cues to pluck_zone, band_body_core, neck_zone, and bass_body over one 560ms bass phrase.",
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_working_bassist(), indent=2))
