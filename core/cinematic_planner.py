from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


DEPTH_INTENSITY_DEFAULTS = {"near": 0.9, "mid": 1.0, "far": 0.82}
HIERARCHY_ROLES = ("primary", "support", "motion", "background")


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


def _scene_id(scene: Any, index: int) -> str:
    return str(_get(scene, "scene_id", f"scene_{index + 1:02d}") or f"scene_{index + 1:02d}")


def _start_ms(obj: Any) -> int:
    return max(0, int(_get(obj, "start_ms", 0) or 0))


def _end_ms(obj: Any) -> int:
    start = _start_ms(obj)
    return max(start + 1, int(_get(obj, "end_ms", start + 1) or (start + 1)))


def _label(scene: Any) -> str:
    return str(_get(scene, "section_label", _get(scene, "label", "section")) or "section").lower().replace("_", "-")


def _energy(scene: Any) -> float:
    return _clamp01(_safe_float(_get(scene, "energy", 0.5), 0.5))


def _as_dict_list(value: Any, attr: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.get(attr, []) or [])
    return list(getattr(value, attr, []) or [])


def _palette_colors(item: Any) -> tuple[str, ...]:
    colors = _get(item, "colors", ())
    return tuple(str(color) for color in (colors or ()) if str(color).strip())


@dataclass(frozen=True)
class CinematicCue:
    cue_id: str
    scene_id: str
    start_ms: int
    end_ms: int
    cue_type: str
    hierarchy_role: str
    prop_family: str
    depth_layer: str
    motion: str
    palette: tuple[str, ...]
    intensity: float
    brightness_modulation: float
    decay_curve: str
    source: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["palette"] = list(self.palette)
        return data


@dataclass(frozen=True)
class CinematicTransitionCue:
    transition_id: str
    start_ms: int
    end_ms: int
    from_scene_id: str
    to_scene_id: str
    transition_type: str
    palette_shift: str
    intensity: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CinematicPlan:
    cues: tuple[CinematicCue, ...]
    transitions: tuple[CinematicTransitionCue, ...]
    debug_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "helix.cinematic_planner.v1",
            "cue_count": len(self.cues),
            "transition_count": len(self.transitions),
            "cues": [cue.to_dict() for cue in self.cues],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "debug_summary": dict(self.debug_summary),
        }


def _scene_lookup(scene_plan: Any) -> tuple[list[Any], list[Any]]:
    scenes = _as_dict_list(scene_plan, "scenes")
    transitions = _as_dict_list(scene_plan, "transitions")
    return scenes, transitions


def _by_scene(items: Sequence[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in items:
        scene_id = str(_get(item, "scene_id", "") or "")
        if scene_id and scene_id not in out:
            out[scene_id] = item
    return out


def _family_depth_map(spatial_choreography: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    for family in _as_dict_list(spatial_choreography, "prop_families"):
        name = str(_get(family, "name", "") or "")
        if name:
            out[name] = str(_get(family, "depth_layer", "mid") or "mid")
    return out


def _depth_scales(spatial_choreography: Any) -> dict[str, float]:
    depth_strategy = _get(spatial_choreography, "depth_strategy", {}) or {}
    raw = _get(depth_strategy, "intensity_scale", {}) or {}
    return {**DEPTH_INTENSITY_DEFAULTS, **{str(key): _safe_float(value, 1.0) for key, value in dict(raw).items()}}


def _complexity_ceiling(signature_style: Any) -> int:
    profile = _get(signature_style, "show_profile", {}) or {}
    try:
        return max(1, min(5, int(_get(profile, "complexity_ceiling", 3) or 3)))
    except Exception:
        return 3


def _motion_bias(signature_style: Any) -> float:
    profile = _get(signature_style, "show_profile", {}) or {}
    return _clamp01(_safe_float(_get(profile, "motion_intensity_bias", 0.65), 0.65))


def _section_palette_by_scene(signature_style: Any) -> dict[str, Any]:
    return _by_scene(_as_dict_list(signature_style, "section_palettes"))


def _dynamics_by_scene(signature_style: Any) -> dict[str, Any]:
    return _by_scene(_as_dict_list(signature_style, "section_dynamics"))


def _dialogue_by_scene(spatial_choreography: Any) -> dict[str, Any]:
    return _by_scene(_as_dict_list(spatial_choreography, "dialogue_cues"))


def _scene_palette(scene: Any, palette_item: Any | None) -> tuple[str, ...]:
    if palette_item is not None:
        colors = _palette_colors(palette_item)
        if colors:
            return colors
    palette = _get(scene, "palette", {}) or {}
    colors = [
        str(_get(palette, "primary", "") or ""),
        str(_get(palette, "secondary", "") or ""),
        str(_get(palette, "accent", "") or ""),
    ]
    return tuple(color for color in colors if color)


def _cue_window(scene: Any) -> tuple[int, int]:
    start = _start_ms(scene)
    end = max(start + 1, _end_ms(scene))
    return start, end


def _role_specs(scene: Any, dialogue: Any | None) -> list[tuple[str, str, str, str]]:
    target = str(_get(dialogue, "target_family", "environment") or "environment") if dialogue is not None else "environment"
    source = str(_get(dialogue, "source_family", target) or target) if dialogue is not None else target
    motion = str(_get(dialogue, "motion", _get(scene, "motion_layer", "slow_drift")) or "slow_drift") if dialogue is not None else str(_get(scene, "motion_layer", "slow_drift") or "slow_drift")
    return [
        ("primary", target, motion, str(_get(scene, "primary_focal_element", "focal") or "focal")),
        ("support", source, "support_hold", str(_get(scene, "supporting_layer", "support") or "support")),
        ("motion", target, motion, str(_get(scene, "motion_layer", motion) or motion)),
        ("background", "environment", "ambient_hold", str(_get(scene, "background_ambience", "ambience") or "ambience")),
    ]


def _cue_intensity(
    *,
    scene: Any,
    role: str,
    dialogue: Any | None,
    dynamics: Any | None,
    depth_layer: str,
    depth_scales: Mapping[str, float],
    motion_bias: float,
) -> float:
    energy = _energy(scene)
    role_factor = {
        "primary": 1.0,
        "support": 0.62,
        "motion": 0.78,
        "background": 0.34,
    }.get(role, 0.6)
    dialogue_intensity = _safe_float(_get(dialogue, "intensity", energy), energy) if dialogue is not None else energy
    brightness = _safe_float(_get(dynamics, "brightness_modulation", 0.0), 0.0) if dynamics is not None else 0.0
    depth_scale = _safe_float(depth_scales.get(depth_layer, 1.0), 1.0)
    raw = (0.18 + (energy * 0.36) + (dialogue_intensity * 0.28) + (motion_bias * 0.18)) * role_factor * depth_scale
    return round(_clamp01(raw + brightness), 4)


def _build_scene_cues(
    scene: Any,
    index: int,
    *,
    dialogue: Any | None,
    palette_item: Any | None,
    dynamics: Any | None,
    family_depth: Mapping[str, str],
    depth_scales: Mapping[str, float],
    complexity_ceiling: int,
    motion_bias: float,
) -> list[CinematicCue]:
    scene_id = _scene_id(scene, index)
    start, end = _cue_window(scene)
    palette = _scene_palette(scene, palette_item)
    brightness = _safe_float(_get(dynamics, "brightness_modulation", 0.0), 0.0) if dynamics is not None else 0.0
    decay = str(_get(dynamics, "decay_curve", "musical_ease_in_out") or "musical_ease_in_out") if dynamics is not None else "musical_ease_in_out"
    cues: list[CinematicCue] = []
    for role, family, motion, reason in _role_specs(scene, dialogue)[:complexity_ceiling]:
        depth = family_depth.get(family, "mid" if family != "environment" else "far")
        cues.append(
            CinematicCue(
                cue_id=f"{scene_id}_{role}",
                scene_id=scene_id,
                start_ms=start,
                end_ms=end,
                cue_type=f"{_label(scene)}_{role}",
                hierarchy_role=role,
                prop_family=family,
                depth_layer=depth,
                motion=motion,
                palette=palette,
                intensity=_cue_intensity(
                    scene=scene,
                    role=role,
                    dialogue=dialogue,
                    dynamics=dynamics,
                    depth_layer=depth,
                    depth_scales=depth_scales,
                    motion_bias=motion_bias,
                ),
                brightness_modulation=round(_clamp01(brightness), 4),
                decay_curve=decay,
                source="scene_spatial_signature_merge",
                reason=reason,
            )
        )
    return cues


def _build_transition_cues(transitions: Sequence[Any]) -> tuple[CinematicTransitionCue, ...]:
    out: list[CinematicTransitionCue] = []
    for idx, transition in enumerate(transitions):
        delta = abs(_safe_float(_get(transition, "energy_delta", 0.0), 0.0))
        out.append(
            CinematicTransitionCue(
                transition_id=f"transition_{idx + 1:02d}",
                start_ms=_start_ms(transition),
                end_ms=_end_ms(transition),
                from_scene_id=str(_get(transition, "from_scene_id", "") or ""),
                to_scene_id=str(_get(transition, "to_scene_id", "") or ""),
                transition_type=str(_get(transition, "transition_type", "dissolve") or "dissolve"),
                palette_shift=str(_get(transition, "palette_shift", "scene_palette_shift") or "scene_palette_shift"),
                intensity=round(_clamp01(0.35 + delta * 0.8), 4),
            )
        )
    return tuple(out)


def build_cinematic_plan(
    scene_plan: Any,
    *,
    spatial_choreography: Any | None = None,
    signature_style: Any | None = None,
) -> CinematicPlan:
    scenes, transitions = _scene_lookup(scene_plan)
    dialogue = _dialogue_by_scene(spatial_choreography)
    palettes = _section_palette_by_scene(signature_style)
    dynamics = _dynamics_by_scene(signature_style)
    family_depth = _family_depth_map(spatial_choreography)
    depth_scales = _depth_scales(spatial_choreography)
    complexity_ceiling = _complexity_ceiling(signature_style)
    motion_bias = _motion_bias(signature_style)

    cues: list[CinematicCue] = []
    for idx, scene in enumerate(scenes):
        scene_id = _scene_id(scene, idx)
        cues.extend(
            _build_scene_cues(
                scene,
                idx,
                dialogue=dialogue.get(scene_id),
                palette_item=palettes.get(scene_id),
                dynamics=dynamics.get(scene_id),
                family_depth=family_depth,
                depth_scales=depth_scales,
                complexity_ceiling=complexity_ceiling,
                motion_bias=motion_bias,
            )
        )

    role_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for cue in cues:
        role_counts[cue.hierarchy_role] = role_counts.get(cue.hierarchy_role, 0) + 1
        family_counts[cue.prop_family] = family_counts.get(cue.prop_family, 0) + 1
    return CinematicPlan(
        cues=tuple(cues),
        transitions=_build_transition_cues(transitions),
        debug_summary={
            "scene_count": len(scenes),
            "complexity_ceiling": complexity_ceiling,
            "role_counts": role_counts,
            "prop_family_counts": family_counts,
        },
    )
