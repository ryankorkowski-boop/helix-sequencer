from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from core import effect_layering_engine
from core.sequence_context import SequenceContext


ROLE_TO_LAYER = {
    "primary": "focus",
    "support": "support",
    "motion": "motion",
    "background": "base",
}

ROLE_PRIORITY = {
    "primary": 5,
    "motion": 3,
    "support": 2,
    "background": 1,
}

MOTION_TO_EFFECT = {
    "ambient_hold": "On",
    "bloom": "On",
    "cascade": "Spirals",
    "impact": "On",
    "orbit": "Wave",
    "ripple": "Wave",
    "shimmer": "Twinkle",
    "slow_drift": "Wave",
    "strobe_accent": "Strobe",
    "support_hold": "On",
    "sweep": "Wave",
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    if out != out:
        return default
    return out


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_list(obj: Any, key: str) -> list[Any]:
    if obj is None:
        return []
    if isinstance(obj, Mapping):
        return list(obj.get(key, []) or [])
    return list(getattr(obj, key, []) or [])


@dataclass(frozen=True)
class CinematicLayeringBridge:
    candidates: tuple[effect_layering_engine.EffectCandidate, ...]
    layering_plan: effect_layering_engine.LayeringPlan
    skipped_cues: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "helix.cinematic_adapter.v1",
            "candidate_count": len(self.candidates),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "layering_plan": self.layering_plan.to_dict(),
            "skipped_cues": [dict(item) for item in self.skipped_cues],
        }


def _prop_target_map(prop_families: Sequence[Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for family in prop_families:
        name = str(_get(family, "name", "") or "")
        targets = [str(item) for item in (_get(family, "targets", []) or []) if str(item).strip()]
        if name:
            out[name] = targets
    return out


def _target_for_cue(cue: Any, targets_by_family: Mapping[str, Sequence[str]]) -> str:
    family = str(_get(cue, "prop_family", "") or "")
    targets = list(targets_by_family.get(family, ()) or ())
    if targets:
        cue_id = str(_get(cue, "cue_id", "") or "")
        digest = hashlib.sha256(cue_id.encode("utf-8", errors="ignore")).hexdigest()
        slot = int(digest[:8], 16) % len(targets)
        return targets[slot]
    return ""


def _effect_for_cue(cue: Any) -> str:
    motion = str(_get(cue, "motion", "") or "").lower()
    return MOTION_TO_EFFECT.get(motion, "On")


def _candidate_for_cue(cue: Any, model: str) -> effect_layering_engine.EffectCandidate:
    role = str(_get(cue, "hierarchy_role", "motion") or "motion").lower()
    layer = ROLE_TO_LAYER.get(role, "motion")
    palette = [str(item) for item in (_get(cue, "palette", []) or []) if str(item).strip()]
    return effect_layering_engine.EffectCandidate(
        model=model,
        effect=_effect_for_cue(cue),
        start_ms=int(_get(cue, "start_ms", 0) or 0),
        end_ms=max(int(_get(cue, "start_ms", 0) or 0) + 1, int(_get(cue, "end_ms", 1) or 1)),
        layer=layer,
        intensity=round(_clamp01(_safe_float(_get(cue, "intensity", 0.6), 0.6)), 4),
        source="cinematic_planner",
        priority=ROLE_PRIORITY.get(role, 2),
        parameters={
            "cue_id": str(_get(cue, "cue_id", "") or ""),
            "scene_id": str(_get(cue, "scene_id", "") or ""),
            "cue_type": str(_get(cue, "cue_type", "") or ""),
            "prop_family": str(_get(cue, "prop_family", "") or ""),
            "depth_layer": str(_get(cue, "depth_layer", "") or ""),
            "motion": str(_get(cue, "motion", "") or ""),
            "palette": palette,
            "brightness_modulation": round(_clamp01(_safe_float(_get(cue, "brightness_modulation", 0.0), 0.0)), 4),
            "decay_curve": str(_get(cue, "decay_curve", "") or ""),
            "reason": str(_get(cue, "reason", "") or ""),
        },
    )


def cinematic_cues_to_effect_candidates(
    cinematic_plan: Any,
    *,
    prop_families: Sequence[Any] = (),
) -> tuple[tuple[effect_layering_engine.EffectCandidate, ...], tuple[dict[str, Any], ...]]:
    targets_by_family = _prop_target_map(prop_families)
    candidates: list[effect_layering_engine.EffectCandidate] = []
    skipped: list[dict[str, Any]] = []
    for cue in _as_list(cinematic_plan, "cues"):
        model = _target_for_cue(cue, targets_by_family)
        if not model:
            skipped.append(
                {
                    "cue_id": str(_get(cue, "cue_id", "") or ""),
                    "prop_family": str(_get(cue, "prop_family", "") or ""),
                    "reason": "no_target_model_for_prop_family",
                }
            )
            continue
        candidates.append(_candidate_for_cue(cue, model))
    return tuple(candidates), tuple(skipped)


def build_cinematic_layering_bridge(
    cinematic_plan: Any,
    *,
    prop_families: Sequence[Any] = (),
    context: SequenceContext | None = None,
    max_layers: int | None = None,
) -> CinematicLayeringBridge:
    candidates, skipped = cinematic_cues_to_effect_candidates(cinematic_plan, prop_families=prop_families)
    layering_plan = effect_layering_engine.build_layering_plan(candidates, context=context, max_layers=max_layers)
    return CinematicLayeringBridge(candidates=candidates, layering_plan=layering_plan, skipped_cues=skipped)
