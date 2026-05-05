from __future__ import annotations

from typing import Any


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


def grade_preview(preview_data: dict[str, Any]) -> dict[str, Any]:
    intent_count = int(preview_data.get("intent_count", 0) or 0)
    placement_count = int(preview_data.get("placement_count", 0) or 0)
    rejected_count = int(preview_data.get("placement_rejected_intent_count", 0) or 0)
    capped_count = int(preview_data.get("placement_capped_intent_count", 0) or 0)
    unique_targets = int(preview_data.get("placement_unique_target_count", 0) or 0)
    effect_family_count = int(preview_data.get("placement_effect_family_count", 0) or 0)

    musicality = min(1.0, 0.45 + intent_count * 0.03)
    readability = 0.82 if preview_data.get("prop_role_overlay") else 0.66
    spatial = 0.8 if preview_data.get("spatial_overlay") else 0.6
    brightness = 0.76

    overlay_bonus = 0.0
    if preview_data.get("placement_overlay"):
        placement_coverage = _clamp(0.35 + min(0.45, placement_count * 0.045) + min(0.2, unique_targets * 0.025))
        effect_variety = _clamp(0.45 + min(0.35, effect_family_count * 0.07))
        rejection_penalty = min(0.35, rejected_count * 0.08)
        cap_penalty = min(0.16, capped_count * 0.03)
        readability = _clamp((readability * 0.62) + (placement_coverage * 0.38) - rejection_penalty)
        spatial = _clamp((spatial * 0.7) + (placement_coverage * 0.3) - cap_penalty)
        musicality = _clamp((musicality * 0.72) + (effect_variety * 0.28) - rejection_penalty)
        brightness = _clamp(brightness - cap_penalty + min(0.08, placement_count * 0.004))
        if rejected_count == 0 and capped_count == 0 and placement_count > 0:
            overlay_bonus = min(0.06, 0.025 + placement_count * 0.005)

    total = round(_clamp(((musicality + readability + spatial + brightness) / 4.0) + overlay_bonus), 4)
    return {
        "Musicality": round(musicality, 4),
        "Readability": round(readability, 4),
        "Spatial coherence": round(spatial, 4),
        "Brightness control": round(brightness, 4),
        "preview_grade": total,
        "placement_overlay": bool(preview_data.get("placement_overlay")),
        "placement_count": placement_count,
        "placement_rejected_intent_count": rejected_count,
        "placement_capped_intent_count": capped_count,
        "vendor_quality_feel": "promising" if total >= 0.72 else "early",
    }
