from __future__ import annotations

from typing import Any


def generate_preview_data(*, layout_name: str, intents: list[dict[str, Any]], seconds: int = 30) -> dict[str, Any]:
    return {
        "layout": layout_name,
        "seconds": seconds,
        "intent_count": len(intents),
        "spatial_overlay": True,
        "prop_role_overlay": True,
        "clips": intents[: min(12, len(intents))],
    }
