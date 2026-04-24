from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from learning.memory import LearningMemory, append_debug, load_memory, save_memory


def _style_key(style: str | None) -> str:
    return (style or "unknown").strip().lower().replace(" ", "_") or "unknown"


def update_style_tendencies(
    memory: LearningMemory,
    *,
    style: str,
    pattern_ids: list[str],
    score: float,
) -> dict[str, Any]:
    key = _style_key(style)
    bucket = memory.style_tendencies.setdefault(
        key,
        {
            "count": 0,
            "average_score": 0.0,
            "preferred_patterns": {},
            "refinement": {"effect_density_bias": 0.0, "transition_speed_bias": 0.0},
        },
    )
    count = int(bucket.get("count", 0)) + 1
    old_avg = float(bucket.get("average_score", 0.0) or 0.0)
    avg = old_avg + ((float(score) - old_avg) / count)
    bucket["count"] = count
    bucket["average_score"] = round(avg, 4)
    preferred = bucket.setdefault("preferred_patterns", {})
    for pattern_id in pattern_ids[:16]:
        preferred[pattern_id] = int(preferred.get(pattern_id, 0)) + 1
    refinement = bucket.setdefault("refinement", {})
    if score >= avg:
        refinement["effect_density_bias"] = round(max(-0.15, min(0.15, float(refinement.get("effect_density_bias", 0.0)) + 0.006)), 4)
        refinement["transition_speed_bias"] = round(max(-0.15, min(0.15, float(refinement.get("transition_speed_bias", 0.0)) + 0.004)), 4)
    else:
        refinement["effect_density_bias"] = round(max(-0.15, min(0.15, float(refinement.get("effect_density_bias", 0.0)) - 0.004)), 4)
    return bucket


def update_style_learning_file(
    *,
    memory_path: Path,
    style: str,
    pattern_ids: list[str],
    score: float,
) -> dict[str, Any]:
    memory = load_memory(memory_path)
    updated = update_style_tendencies(memory, style=style, pattern_ids=pattern_ids, score=score)
    append_debug(memory, "style_learning_update", {"style": _style_key(style), "score": round(float(score), 4), "pattern_count": len(pattern_ids)})
    save_memory(memory_path, memory)
    return updated


def style_refinement(memory: LearningMemory | Mapping[str, Any], style: str) -> dict[str, Any]:
    tendencies = memory.style_tendencies if isinstance(memory, LearningMemory) else dict(memory.get("style_tendencies", {}) or {})
    bucket = tendencies.get(_style_key(style), {})
    refinement = dict(bucket.get("refinement", {}) or {})
    return {
        "style": _style_key(style),
        "sample_count": int(bucket.get("count", 0) or 0),
        "average_score": float(bucket.get("average_score", 0.0) or 0.0),
        "effect_density_bias": float(refinement.get("effect_density_bias", 0.0) or 0.0),
        "transition_speed_bias": float(refinement.get("transition_speed_bias", 0.0) or 0.0),
        "preferred_patterns": dict(sorted((bucket.get("preferred_patterns", {}) or {}).items(), key=lambda item: (-int(item[1]), item[0]))[:12]),
    }
