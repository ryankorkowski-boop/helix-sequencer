from __future__ import annotations

from typing import Any


def grade_preview(preview_data: dict[str, Any]) -> dict[str, Any]:
    intent_count = int(preview_data.get("intent_count", 0) or 0)
    musicality = min(1.0, 0.45 + intent_count * 0.03)
    readability = 0.82 if preview_data.get("prop_role_overlay") else 0.66
    spatial = 0.8 if preview_data.get("spatial_overlay") else 0.6
    brightness = 0.76
    total = round((musicality + readability + spatial + brightness) / 4.0, 4)
    return {
        "Musicality": round(musicality, 4),
        "Readability": round(readability, 4),
        "Spatial coherence": round(spatial, 4),
        "Brightness control": round(brightness, 4),
        "preview_grade": total,
        "vendor_quality_feel": "promising" if total >= 0.72 else "early",
    }
