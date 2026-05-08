from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from helix_intent.visual_intent import PropEffectIntent, VisualIntent


ROLE_ALIASES: dict[str, set[str]] = {
    "center": {"hero", "matrix", "detail_surface", "performer", "vocal_prop", "whole_house"},
    "upper": {"hero", "tree", "matrix", "accent"},
    "hero_prop": {"hero", "tree", "matrix"},
    "whole_house": {"structure", "roofline", "outline", "whole_house"},
    "background": {"structure", "roofline", "window", "mood", "texture"},
    "matrix": {"matrix", "detail_surface"},
    "roofline": {"structure", "roofline", "outline"},
    "middle": {"matrix", "performer", "mood", "rhythm"},
    "arches": {"travel", "arch", "travel_props"},
    "vocal_prop": {"vocals", "face", "performer", "snowman_band"},
}

EFFECT_BY_INTENT: dict[str, str] = {
    "bloom": "energy_wave",
    "color_wash": "soft_wash",
    "transition": "directional_sweep",
    "trail": "melody_trail",
}

EFFECT_BY_ROLE: dict[str, str] = {
    "hero": "energy_wave",
    "tree": "energy_wave",
    "matrix": "matrix_pulse",
    "detail_surface": "matrix_pulse",
    "travel": "directional_sweep",
    "arch": "directional_sweep",
    "travel_props": "directional_sweep",
    "structure": "outline_pulse",
    "roofline": "outline_pulse",
    "outline": "outline_pulse",
    "window": "outline_pulse",
    "vocals": "lyric_pulse",
    "face": "lyric_pulse",
    "performer": "character_hit",
    "snowman_band": "character_hit",
    "rhythm": "beat_pulse",
    "mood": "soft_wash",
    "texture": "soft_wash",
    "accent": "sparkle_accent",
}

BRIGHTNESS_CAP_BY_DENSITY: dict[str, float] = {
    "sparse": 0.38,
    "medium": 0.62,
    "full": 0.82,
}

MAX_TARGETS_BY_DENSITY: dict[str, int] = {
    "sparse": 2,
    "medium": 4,
    "full": 7,
}


@dataclass(frozen=True)
class PlacementCandidate:
    prop_name: str
    role: str
    family: str = ""
    priority: int = 50


@dataclass(frozen=True)
class PlacementPlanReport:
    intent_count: int
    placement_count: int
    rejected_intents: list[str]
    capped_density_intents: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "intent_count": self.intent_count,
            "placement_count": self.placement_count,
            "rejected_intents": list(self.rejected_intents),
            "capped_density_intents": list(self.capped_density_intents),
        }


def _norm(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _expanded_roles(role: str) -> set[str]:
    normalized = _norm(role)
    return {normalized, *ROLE_ALIASES.get(normalized, set())}


def _candidate_from_mapping(item: Mapping[str, object]) -> PlacementCandidate:
    return PlacementCandidate(
        prop_name=str(item.get("prop_name") or item.get("name") or item.get("model") or ""),
        role=_norm(item.get("role") or item.get("target_role") or item.get("visual_role") or "support"),
        family=_norm(item.get("family") or item.get("model_family") or ""),
        priority=int(item.get("priority", 50) or 50),
    )


def normalize_candidates(items: Iterable[PlacementCandidate | Mapping[str, object]]) -> list[PlacementCandidate]:
    candidates: list[PlacementCandidate] = []
    for item in items:
        candidate = item if isinstance(item, PlacementCandidate) else _candidate_from_mapping(item)
        if candidate.prop_name:
            candidates.append(candidate)
    return candidates


def _candidate_matches(candidate: PlacementCandidate, target_role: str) -> bool:
    wanted = _expanded_roles(target_role)
    return candidate.role in wanted or candidate.family in wanted


def _effect_family(intent: VisualIntent, candidate: PlacementCandidate) -> str:
    return EFFECT_BY_ROLE.get(candidate.role) or EFFECT_BY_ROLE.get(candidate.family) or EFFECT_BY_INTENT.get(intent.intent_type, "support_pulse")


def _render_style(intent: VisualIntent, candidate: PlacementCandidate) -> str:
    if intent.render_style_hint and intent.render_style_hint != "per_preview":
        return intent.render_style_hint
    if candidate.role in {"hero", "matrix", "detail_surface"}:
        return "per_preview"
    if candidate.role in {"structure", "roofline", "window"}:
        return "per_model"
    return intent.render_style_hint or "per_model"


def _curve_type(intent: VisualIntent) -> str:
    if intent.curve_strategy:
        return intent.curve_strategy
    if intent.intent_type == "bloom":
        return "attack_decay"
    if intent.intent_type == "transition":
        return "crossfade"
    return "section_envelope"


def plan_prop_effect_intents(
    visual_intents: Iterable[VisualIntent],
    candidates: Iterable[PlacementCandidate | Mapping[str, object]],
) -> tuple[list[PropEffectIntent], PlacementPlanReport]:
    """Map visual intents to deterministic per-prop effect intents.

    This is a source-agnostic bridge between high-level visual planning and the
    heavier xLights effect engine. It does not place XML effects directly. It
    chooses target props, effect families, render styles, curves, and brightness
    caps so the next layer can render inspectable placements.
    """
    normalized_candidates = normalize_candidates(candidates)
    placements: list[PropEffectIntent] = []
    rejected: list[str] = []
    capped: list[str] = []
    intent_count = 0

    for intent in visual_intents:
        intent_count += 1
        density = _norm(intent.density_level) or "medium"
        max_targets = MAX_TARGETS_BY_DENSITY.get(density, MAX_TARGETS_BY_DENSITY["medium"])
        brightness_cap = BRIGHTNESS_CAP_BY_DENSITY.get(density, BRIGHTNESS_CAP_BY_DENSITY["medium"])

        matched: dict[str, PlacementCandidate] = {}
        for target_role in intent.target_roles:
            for candidate in normalized_candidates:
                if _candidate_matches(candidate, target_role):
                    previous = matched.get(candidate.prop_name)
                    if previous is None or candidate.priority < previous.priority:
                        matched[candidate.prop_name] = candidate

        ordered = sorted(matched.values(), key=lambda item: (item.priority, item.prop_name))
        if not ordered:
            rejected.append(intent.id)
            continue
        if len(ordered) > max_targets:
            capped.append(intent.id)
            ordered = ordered[:max_targets]

        for candidate in ordered:
            confidence = min(1.0, max(0.0, float(intent.confidence) * (1.0 if candidate.priority <= 50 else 0.9)))
            placements.append(
                PropEffectIntent(
                    visual_intent_id=intent.id,
                    target_prop=candidate.prop_name,
                    target_role=candidate.role,
                    effect_family=_effect_family(intent, candidate),
                    render_style=_render_style(intent, candidate),
                    curve_type=_curve_type(intent),
                    brightness_cap=brightness_cap,
                    confidence=round(confidence, 4),
                )
            )

    return placements, PlacementPlanReport(
        intent_count=intent_count,
        placement_count=len(placements),
        rejected_intents=rejected,
        capped_density_intents=capped,
    )
