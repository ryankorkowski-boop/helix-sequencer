from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from helix_intent.placement_planner import PlacementCandidate


ROLE_BY_MODEL_TYPE: dict[str, str] = {
    "arch": "travel",
    "cane": "rhythm",
    "circle": "accent",
    "custom": "performer",
    "flood": "mood",
    "icicle": "texture",
    "image": "detail_surface",
    "line": "structure",
    "matrix": "detail_surface",
    "spinner": "motion",
    "sphere": "mood",
    "star": "accent",
    "tree": "hero",
    "window": "structure",
    "wreath": "accent",
}

FAMILY_BY_MODEL_TYPE: dict[str, str] = {
    "arch": "travel_props",
    "cane": "canes",
    "circle": "circles",
    "custom": "custom_props",
    "flood": "mood_washes",
    "icicle": "icicles",
    "image": "matrices",
    "line": "roofline",
    "matrix": "matrices",
    "spinner": "spinners",
    "sphere": "spheres",
    "star": "stars",
    "tree": "trees",
    "window": "windows",
    "wreath": "wreaths",
}

NAME_ROLE_HINTS: tuple[tuple[str, str, str], ...] = (
    ("snowman", "performer", "snowman_band"),
    ("cactus", "performer", "character"),
    ("tubeman", "performer", "character"),
    ("singer", "vocals", "snowman_band"),
    ("face", "vocals", "faces"),
    ("mouth", "vocals", "faces"),
    ("drum", "rhythm", "snowman_band"),
    ("bass", "rhythm", "snowman_band"),
    ("guitar", "rhythm", "snowman_band"),
    ("matrix", "detail_surface", "matrices"),
    ("mega", "hero", "trees"),
    ("tree", "hero", "trees"),
    ("roof", "structure", "roofline"),
    ("window", "structure", "windows"),
    ("arch", "travel", "travel_props"),
    ("flood", "mood", "mood_washes"),
)


def _norm(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _priority_for(role: str, family: str, prop_name: str) -> int:
    name = _norm(prop_name)
    if role in {"hero", "vocals", "performer"}:
        base = 10
    elif role in {"travel", "rhythm", "detail_surface"}:
        base = 25
    elif role in {"structure", "mood"}:
        base = 40
    else:
        base = 60
    if any(token in name for token in ("center", "main", "mega", "lead")):
        base -= 5
    if family in {"snowman_band", "character"}:
        base -= 3
    return max(1, base)


def role_family_for_model(name: str, model_type: str) -> tuple[str, str]:
    normalized_name = _norm(name)
    for token, role, family in NAME_ROLE_HINTS:
        if token in normalized_name:
            return role, family
    normalized_type = _norm(model_type)
    return (
        ROLE_BY_MODEL_TYPE.get(normalized_type, "support"),
        FAMILY_BY_MODEL_TYPE.get(normalized_type, normalized_type or "unknown"),
    )


def candidate_from_model(name: str, model_type: str) -> PlacementCandidate:
    role, family = role_family_for_model(name, model_type)
    return PlacementCandidate(
        prop_name=name,
        role=role,
        family=family,
        priority=_priority_for(role, family, name),
    )


def candidates_from_parsed_layout(parsed_layout: Any) -> list[PlacementCandidate]:
    models = getattr(parsed_layout, "models", {}) or {}
    candidates: list[PlacementCandidate] = []
    for name, model in models.items():
        if getattr(model, "is_submodel", False):
            continue
        candidates.append(candidate_from_model(str(name), str(getattr(model, "type", ""))))
    return sorted(candidates, key=lambda item: (item.priority, item.prop_name))


def candidates_from_layout_intelligence(layout_intelligence: Mapping[str, Any]) -> list[PlacementCandidate]:
    candidates: list[PlacementCandidate] = []
    for group_name, models in (layout_intelligence.get("performer_models") or {}).items():
        family = "character" if group_name == "cactus_tubeman" else _norm(group_name)
        role = "performer"
        for model_name in list(models or []):
            candidates.append(
                PlacementCandidate(
                    prop_name=str(model_name),
                    role=role,
                    family=family,
                    priority=_priority_for(role, family, str(model_name)),
                )
            )
    for lot in list(layout_intelligence.get("house_lots") or []) + list(layout_intelligence.get("special_lots") or []):
        if not isinstance(lot, Mapping):
            continue
        lot_id = str(lot.get("lot_id", ""))
        roles = list(lot.get("roles") or ["support"])
        families = list(lot.get("families") or ["unknown"])
        role = _norm(roles[0]) if roles else "support"
        family = _norm(families[0]) if families else "unknown"
        if lot_id:
            candidates.append(
                PlacementCandidate(
                    prop_name=lot_id,
                    role=role,
                    family=family,
                    priority=_priority_for(role, family, lot_id) + 20,
                )
            )
    return sorted(candidates, key=lambda item: (item.priority, item.prop_name))


def merge_candidates(*candidate_sets: Iterable[PlacementCandidate]) -> list[PlacementCandidate]:
    by_name: dict[str, PlacementCandidate] = {}
    for candidate_set in candidate_sets:
        for candidate in candidate_set:
            existing = by_name.get(candidate.prop_name)
            if existing is None or candidate.priority < existing.priority:
                by_name[candidate.prop_name] = candidate
    return sorted(by_name.values(), key=lambda item: (item.priority, item.prop_name))
