from __future__ import annotations

from typing import Any


def _placement_clips(placement_plan: dict[str, Any] | None, limit: int) -> list[dict[str, Any]]:
    if not placement_plan:
        return []
    clips: list[dict[str, Any]] = []
    visual_by_id = {
        str(intent.get("id", "")): intent
        for intent in list(placement_plan.get("visual_intents", []) or [])
        if isinstance(intent, dict)
    }
    for item in list(placement_plan.get("prop_effect_intents", []) or [])[:limit]:
        if not isinstance(item, dict):
            continue
        visual = visual_by_id.get(str(item.get("visual_intent_id", "")), {})
        clips.append(
            {
                "visual_intent_id": item.get("visual_intent_id", ""),
                "target_prop": item.get("target_prop", ""),
                "target_role": item.get("target_role", ""),
                "effect_family": item.get("effect_family", ""),
                "render_style": item.get("render_style", ""),
                "brightness_cap": item.get("brightness_cap", 0.0),
                "start_time": visual.get("start_time", 0.0),
                "end_time": visual.get("end_time", 0.0),
                "intent_type": visual.get("intent_type", ""),
            }
        )
    return clips


def generate_preview_data(
    *,
    layout_name: str,
    intents: list[dict[str, Any]],
    seconds: int = 30,
    placement_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    planner_report = dict((placement_plan or {}).get("planner_report", {}) or {})
    placement_clips = _placement_clips(placement_plan, min(18, max(1, seconds)))
    placement_count = int(planner_report.get("placement_count", len(placement_clips)) or 0)
    rejected_count = len(list(planner_report.get("rejected_intents", []) or []))
    capped_count = len(list(planner_report.get("capped_density_intents", []) or []))
    unique_targets = sorted({str(item.get("target_prop", "")) for item in placement_clips if item.get("target_prop")})
    effect_families = sorted({str(item.get("effect_family", "")) for item in placement_clips if item.get("effect_family")})
    return {
        "layout": layout_name,
        "seconds": seconds,
        "intent_count": len(intents),
        "spatial_overlay": True,
        "prop_role_overlay": True,
        "clips": intents[: min(12, len(intents))],
        "placement_overlay": bool(placement_plan),
        "placement_count": placement_count,
        "placement_rejected_intent_count": rejected_count,
        "placement_capped_intent_count": capped_count,
        "placement_unique_target_count": len(unique_targets),
        "placement_effect_family_count": len(effect_families),
        "placement_clips": placement_clips,
        "placement_warnings": list((placement_plan or {}).get("warnings", []) or []),
    }
