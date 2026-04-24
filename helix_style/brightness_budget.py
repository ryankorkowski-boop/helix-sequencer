from __future__ import annotations


def brightness_budget(section_name: str, *, hero_priority: float = 0.8) -> dict[str, float]:
    if section_name == "verse":
        return {"max_total_brightness": 0.42, "max_white_use": 0.18, "hero_priority": hero_priority}
    if section_name in {"chorus", "final_chorus"}:
        return {"max_total_brightness": 0.82, "max_white_use": 0.34, "hero_priority": min(1.0, hero_priority + 0.12)}
    return {"max_total_brightness": 0.58, "max_white_use": 0.22, "hero_priority": hero_priority}
