from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any


SIGNATURE_LANE = "lane_signature_backbone"
HOOK_LANE = "lane_hook_accents"
SPATIAL_LANE = "lane_spatial_motion"
STEM_LANE = "lane_stem_story"
CINEMATIC_LANE = "lane_cinematic_reveals"
AUXILIARY_LANE = "lane_auxiliary"

VARIANT_LANE_MAP: dict[str, str] = {
    "signature": SIGNATURE_LANE,
    "hook_focus": HOOK_LANE,
    "wide_stage": SPATIAL_LANE,
    "stem_story": STEM_LANE,
    "cinematic_arc": CINEMATIC_LANE,
}


@dataclass(frozen=True)
class VariantLaneAssignment:
    label: str
    lane: str
    description: str = ""
    quality_gate_passed: bool | None = None
    shortlist_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


def normalize_variant_label(label: str | None) -> str:
    return (label or "").strip().lower().replace("-", "_").replace(" ", "_")


def lane_for_variant(label: str | None) -> str:
    return VARIANT_LANE_MAP.get(normalize_variant_label(label), AUXILIARY_LANE)


def build_variant_lane_plan(entries: list[dict[str, Any]]) -> dict[str, Any]:
    assignments: list[VariantLaneAssignment] = []
    lanes: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for index, entry in enumerate(entries):
        label = normalize_variant_label(str(entry.get("label") or f"variant_{index + 1}"))
        assignment = VariantLaneAssignment(
            label=label,
            lane=lane_for_variant(label),
            description=str(entry.get("description") or ""),
            quality_gate_passed=(
                bool(entry["quality_gate_passed"]) if "quality_gate_passed" in entry else None
            ),
            shortlist_score=(
                float(entry["shortlist_score"]) if entry.get("shortlist_score") is not None else None
            ),
        )
        assignment_dict = assignment.to_dict()
        assignments.append(assignment)
        lanes[assignment.lane].append(assignment_dict)

    ordered_lanes = {
        lane: lanes.get(lane, [])
        for lane in [
            SIGNATURE_LANE,
            HOOK_LANE,
            SPATIAL_LANE,
            STEM_LANE,
            CINEMATIC_LANE,
            AUXILIARY_LANE,
        ]
        if lanes.get(lane)
    }

    return {
        "version": 1,
        "mode": "variant_lanes_plan",
        "composite_enabled": False,
        "lane_count": len(ordered_lanes),
        "assignment_count": len(assignments),
        "assignments": [assignment.to_dict() for assignment in assignments],
        "lanes": ordered_lanes,
    }
