from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from core.sequence_context import SequenceContext, clamp01


LAYER_ROLE_PRIORITY = {
    "base": 1,
    "texture": 2,
    "motion": 3,
    "accent": 4,
    "focus": 5,
}


@dataclass(frozen=True)
class EffectCandidate:
    model: str
    effect: str
    start_ms: int
    end_ms: int
    layer: str = "motion"
    intensity: float = 0.6
    source: str = "effect"
    priority: int | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    def normalized_priority(self, context: SequenceContext | None = None) -> int:
        role = self.layer.lower()
        try:
            base = int(self.priority if self.priority is not None else LAYER_ROLE_PRIORITY.get(role, 2))
        except Exception:
            base = LAYER_ROLE_PRIORITY.get(role, 2)
        if context is not None:
            dominant = {item.lower() for item in context.dominant_elements}
            focus = str((context.band_state or {}).get("primary_focus", "")).lower()
            if self.source.lower() in dominant:
                base += 1
            if focus and focus in self.source.lower():
                base += 1
            emotion_type = str((context.emotion_state or {}).get("emotion_type", "")).lower()
            if emotion_type in {"aggressive", "energetic", "triumphant"} and role == "accent":
                base += 1
        return max(1, base)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LayeredEffect:
    model: str
    effect: str
    start_ms: int
    end_ms: int
    layer_name: str
    layer_role: str
    blend_mode: str
    mix: float
    priority: int
    intensity: float
    source: str
    parameters: dict[str, Any] = field(default_factory=dict)
    composited_sources: tuple[str, ...] = ()

    def overlaps(self, other: "LayeredEffect | EffectCandidate") -> bool:
        return self.model == other.model and self.start_ms < other.end_ms and int(other.start_ms) < self.end_ms

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["composited_sources"] = list(self.composited_sources)
        return data


@dataclass(frozen=True)
class LayeringPlan:
    layered_effects: list[LayeredEffect]
    layering_logs: list[dict[str, Any]]
    debug_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "layered_effects": [effect.to_dict() for effect in self.layered_effects],
            "layering_logs": self.layering_logs,
            "debug_summary": self.debug_summary,
        }


def _candidate_from(value: Any) -> EffectCandidate:
    if isinstance(value, EffectCandidate):
        return value
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if isinstance(value, Mapping):
        return EffectCandidate(
            model=str(value.get("model", "")),
            effect=str(value.get("effect", "On")),
            start_ms=int(value.get("start_ms", 0)),
            end_ms=max(int(value.get("start_ms", 0)) + 1, int(value.get("end_ms", 1))),
            layer=str(value.get("layer", value.get("layer_role", "motion"))),
            intensity=clamp01(float(value.get("intensity", 0.6))),
            source=str(value.get("source", "effect")),
            priority=value.get("priority"),
            parameters=dict(value.get("parameters", {}) or {}),
        )
    raise TypeError(f"Unsupported effect candidate: {value!r}")


def _style_layer_usage(context: SequenceContext | None) -> Mapping[str, Any]:
    if context is None:
        return {}
    return ((context.style_profile or {}).get("layer_usage") or {}) if context.style_profile else {}


def max_layers_for_context(context: SequenceContext | None, default: int = 3) -> int:
    usage = _style_layer_usage(context)
    raw = usage.get("max_layers", default)
    try:
        value = int(round(float(raw)))
    except Exception:
        value = default
    clutter = 0.0
    coherence = 1.0
    if context is not None:
        clutter = clamp01(float((context.scoring_feedback or {}).get("clutter_ratio", 0.0) or 0.0))
        coherence = clamp01(float((context.scoring_feedback or {}).get("visual_coherence", 1.0) or 1.0))
    if clutter >= 0.22 or coherence < 0.55:
        value -= 1
    if context is not None and context.energy_level >= 0.82 and clutter < 0.15:
        value += 1
    return max(1, min(5, value))


def _role_weight(role: str, context: SequenceContext | None) -> float:
    usage = _style_layer_usage(context)
    try:
        return clamp01(float(usage.get(role, 0.65)))
    except Exception:
        return 0.65


def _blend_mode(role: str, intensity: float, context: SequenceContext | None) -> str:
    style_name = str((context.style_profile or {}).get("name", "")).lower() if context is not None else ""
    role = role.lower()
    if role == "base":
        return "Normal"
    if role == "texture":
        return "Overlay" if style_name != "ambient" else "Screen"
    if role == "accent":
        return "Additive" if intensity >= 0.58 and style_name != "orchestral" else "Screen"
    if role == "focus":
        return "Screen"
    return "Screen" if intensity < 0.82 else "Additive"


def _layer_name(role: str, slot: int) -> str:
    return f"{role}_{slot:02d}"


def _make_layered(candidate: EffectCandidate, context: SequenceContext | None, slot: int) -> LayeredEffect:
    role = candidate.layer.lower()
    priority = candidate.normalized_priority(context)
    weighted_intensity = clamp01(candidate.intensity * (0.58 + (_role_weight(role, context) * 0.42)))
    return LayeredEffect(
        model=candidate.model,
        effect=candidate.effect,
        start_ms=max(0, candidate.start_ms),
        end_ms=max(candidate.start_ms + 1, candidate.end_ms),
        layer_name=_layer_name(role, slot),
        layer_role=role,
        blend_mode=_blend_mode(role, weighted_intensity, context),
        mix=round(0.35 + weighted_intensity * 0.65, 4),
        priority=priority,
        intensity=round(weighted_intensity, 4),
        source=candidate.source,
        parameters=dict(candidate.parameters),
    )


def _composite_into(base: LayeredEffect, candidate: EffectCandidate, context: SequenceContext | None) -> LayeredEffect:
    priority = max(base.priority, candidate.normalized_priority(context))
    merged_params = dict(base.parameters)
    merged_params.setdefault("composite_hints", []).append(
        {
            "effect": candidate.effect,
            "source": candidate.source,
            "layer": candidate.layer,
            "intensity": round(candidate.intensity, 4),
        }
    )
    sources = tuple(dict.fromkeys((*base.composited_sources, base.source, candidate.source)))
    intensity = clamp01(max(base.intensity, candidate.intensity * 0.82))
    return LayeredEffect(
        model=base.model,
        effect=base.effect,
        start_ms=min(base.start_ms, candidate.start_ms),
        end_ms=max(base.end_ms, candidate.end_ms),
        layer_name=base.layer_name,
        layer_role=base.layer_role,
        blend_mode=base.blend_mode,
        mix=round(max(base.mix, 0.35 + intensity * 0.55), 4),
        priority=priority,
        intensity=round(intensity, 4),
        source=base.source,
        parameters=merged_params,
        composited_sources=sources,
    )


def build_layering_plan(
    effects: Iterable[Any],
    *,
    context: SequenceContext | None = None,
    max_layers: int | None = None,
) -> LayeringPlan:
    candidates: list[EffectCandidate] = []
    for effect in effects:
        candidate = _candidate_from(effect)
        if candidate.model:
            candidates.append(candidate)
    candidates.sort(key=lambda item: (item.model.lower(), item.start_ms, -item.normalized_priority(context), item.effect))
    layer_cap = max_layers if max_layers is not None else max_layers_for_context(context)
    layered: list[LayeredEffect] = []
    logs: list[dict[str, Any]] = []

    for candidate in candidates:
        active = [effect for effect in layered if effect.overlaps(candidate)]
        if len(active) < layer_cap:
            slot = 1 + sum(1 for effect in active if effect.layer_role == candidate.layer.lower())
            placed = _make_layered(candidate, context, slot)
            layered.append(placed)
            logs.append({"action": "layered", "model": candidate.model, "effect": candidate.effect, "layer": placed.layer_name})
            continue

        target = min(active, key=lambda effect: (effect.priority, effect.intensity, effect.layer_name))
        candidate_priority = candidate.normalized_priority(context)
        if candidate_priority >= target.priority:
            replacement = _make_layered(candidate, context, int(target.layer_name.rsplit("_", 1)[-1]))
            replacement = _composite_into(replacement, EffectCandidate(
                model=target.model,
                effect=target.effect,
                start_ms=target.start_ms,
                end_ms=target.end_ms,
                layer=target.layer_role,
                intensity=target.intensity,
                source=target.source,
                priority=target.priority,
                parameters=target.parameters,
            ), context)
            idx = layered.index(target)
            layered[idx] = replacement
            logs.append(
                {
                    "action": "promoted_and_composited",
                    "model": candidate.model,
                    "effect": candidate.effect,
                    "replaced_layer": target.layer_name,
                    "carried_source": target.source,
                }
            )
        else:
            idx = layered.index(target)
            layered[idx] = _composite_into(target, candidate, context)
            logs.append(
                {
                    "action": "composited",
                    "model": candidate.model,
                    "effect": candidate.effect,
                    "into_layer": target.layer_name,
                    "reason": "layer_cap_reached",
                }
            )

    layered.sort(key=lambda item: (item.model.lower(), item.start_ms, item.layer_name))
    per_model: dict[str, int] = {}
    composited = 0
    for effect in layered:
        per_model[effect.model] = per_model.get(effect.model, 0) + 1
        if effect.composited_sources:
            composited += 1
    summary = {
        "candidate_count": len(candidates),
        "layered_count": len(layered),
        "max_layers_per_model": layer_cap,
        "composited_layer_count": composited,
        "layers_by_model": per_model,
    }
    plan = LayeringPlan(layered_effects=layered, layering_logs=logs, debug_summary=summary)
    if context is not None:
        context.update_scoring_feedback({"layered_effect_count": len(layered), "composited_layer_count": composited})
        context.add_debug("effect_layering_engine", "layering_plan_built", plan.to_dict())
    return plan
