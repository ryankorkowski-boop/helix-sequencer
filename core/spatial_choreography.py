from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


PROP_FAMILIES = ("band", "floor_piano", "arches", "megatree", "roofline")

DEPTH_BY_FAMILY = {
    "band": "near",
    "floor_piano": "near",
    "arches": "mid",
    "megatree": "far",
    "roofline": "far",
}

FALLBACK_FAMILIES = {
    "band": ("floor_piano", "arches", "megatree", "roofline"),
    "floor_piano": ("arches", "band", "roofline", "megatree"),
    "arches": ("floor_piano", "roofline", "megatree", "band"),
    "megatree": ("roofline", "arches", "floor_piano", "band"),
    "roofline": ("megatree", "arches", "floor_piano", "band"),
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


def _scene_id(scene: Any, index: int) -> str:
    return str(_get(scene, "scene_id", f"scene_{index + 1:02d}") or f"scene_{index + 1:02d}")


def _label(scene: Any) -> str:
    return str(_get(scene, "section_label", _get(scene, "label", "section")) or "section").lower().replace("_", "-")


def _start_ms(scene: Any) -> int:
    return max(0, int(_get(scene, "start_ms", 0) or 0))


def _end_ms(scene: Any) -> int:
    start = _start_ms(scene)
    return max(start + 1, int(_get(scene, "end_ms", start + 1) or (start + 1)))


def _energy(scene: Any) -> float:
    return _clamp01(_safe_float(_get(scene, "energy", 0.5), 0.5))


@dataclass(frozen=True)
class MotionGrammarEntry:
    name: str
    trigger: str
    preferred_families: tuple[str, ...]
    timing_shape: str
    intensity_bias: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["preferred_families"] = list(self.preferred_families)
        return data


@dataclass(frozen=True)
class PropFamily:
    name: str
    targets: tuple[str, ...]
    depth_layer: str
    available: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["targets"] = list(self.targets)
        return data


@dataclass(frozen=True)
class DialogueCue:
    scene_id: str
    start_ms: int
    end_ms: int
    source_family: str
    target_family: str
    relationship: str
    motion: str
    intensity: float
    response_delay_ms: int
    depth_path: tuple[str, ...]
    palette_hint: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["depth_path"] = list(self.depth_path)
        return data


@dataclass(frozen=True)
class DepthStrategy:
    near: tuple[str, ...]
    mid: tuple[str, ...]
    far: tuple[str, ...]
    intensity_scale: dict[str, float]
    parallax_bias: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "near": list(self.near),
            "mid": list(self.mid),
            "far": list(self.far),
            "intensity_scale": dict(self.intensity_scale),
            "parallax_bias": dict(self.parallax_bias),
        }


@dataclass(frozen=True)
class SpatialChoreographyPlan:
    prop_families: tuple[PropFamily, ...]
    dialogue_cues: tuple[DialogueCue, ...]
    depth_strategy: DepthStrategy
    motion_grammar: tuple[MotionGrammarEntry, ...]
    fallback_logs: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "helix.spatial_choreography.v1",
            "prop_families": [family.to_dict() for family in self.prop_families],
            "dialogue_cues": [cue.to_dict() for cue in self.dialogue_cues],
            "depth_strategy": self.depth_strategy.to_dict(),
            "motion_grammar": [entry.to_dict() for entry in self.motion_grammar],
            "fallback_logs": [dict(item) for item in self.fallback_logs],
            "cue_count": len(self.dialogue_cues),
        }


MOTION_GRAMMAR = (
    MotionGrammarEntry("ripple", "beat_or_floor_piano_note", ("floor_piano", "arches"), "staggered_echo", 0.55),
    MotionGrammarEntry("bloom", "chorus_or_hook_arrival", ("megatree", "roofline"), "center_out_swell", 0.72),
    MotionGrammarEntry("sweep", "pre_chorus_or_buildup", ("arches", "roofline"), "directional_ramp", 0.62),
    MotionGrammarEntry("cascade", "drop_or_dense_percussion", ("megatree", "arches"), "top_down_release", 0.78),
    MotionGrammarEntry("impact", "kick_snare_or_drop_hit", ("band", "megatree"), "short_accent", 0.9),
    MotionGrammarEntry("shimmer", "quiet_window_or_outro", ("roofline", "arches"), "low_motion_texture", 0.38),
    MotionGrammarEntry("orbit", "bridge_or_instrumental_pivot", ("arches", "megatree"), "circular_call", 0.58),
    MotionGrammarEntry("strobe_accent", "micro_accent_only", ("band", "roofline"), "guarded_flash", 0.82),
)


def _family_from_text(name: str, semantic_type: str = "", tags: Sequence[str] = ()) -> str | None:
    text = f"{name} {semantic_type} {' '.join(tags)}".lower().replace("_", " ")
    if any(token in text for token in ("singer", "face", "snowman", "drum", "guitar", "bass", "band", "mouth")):
        return "band"
    if any(token in text for token in ("floor piano", "player piano", "keyboard", "piano", "keys", "note lane", "note")):
        return "floor_piano"
    if "arch" in text:
        return "arches"
    if "mega tree" in text or "megatree" in text or ("tree" in text and "roof" not in text):
        return "megatree"
    if any(token in text for token in ("roof", "roofline", "gutter", "eave", "outline")):
        return "roofline"
    return None


def _iter_layout_items(layout: Any | None) -> list[tuple[str, str, tuple[str, ...]]]:
    if layout is None:
        return []
    if hasattr(layout, "nodes"):
        return [
            (
                str(getattr(node, "name", "")),
                str(getattr(node, "type", "")),
                tuple(str(tag) for tag in getattr(node, "tags", ()) or ()),
            )
            for node in getattr(layout, "nodes", {}).values()
            if getattr(node, "kind", "model") == "model"
        ]
    if hasattr(layout, "models"):
        return [
            (
                str(getattr(model, "name", name)),
                str(getattr(model, "type", getattr(model, "display_as", ""))),
                (),
            )
            for name, model in getattr(layout, "models", {}).items()
            if not bool(getattr(model, "is_submodel", False))
        ]
    return []


def classify_prop_families(layout: Any | None = None) -> tuple[PropFamily, ...]:
    buckets: dict[str, list[str]] = {family: [] for family in PROP_FAMILIES}
    for name, semantic_type, tags in _iter_layout_items(layout):
        family = _family_from_text(name, semantic_type, tags)
        if family in buckets:
            buckets[family].append(name)
    return tuple(
        PropFamily(
            name=family,
            targets=tuple(sorted(dict.fromkeys(buckets[family]), key=str.lower)),
            depth_layer=DEPTH_BY_FAMILY[family],
            available=bool(buckets[family]),
        )
        for family in PROP_FAMILIES
    )


def _available_lookup(prop_families: Sequence[PropFamily]) -> dict[str, PropFamily]:
    return {family.name: family for family in prop_families}


def _resolve_family(
    requested: str,
    prop_families: Mapping[str, PropFamily],
    fallback_logs: list[dict[str, Any]],
    scene_id: str,
) -> str:
    family = prop_families.get(requested)
    if family is None or family.available:
        return requested
    for fallback in FALLBACK_FAMILIES.get(requested, ()):
        candidate = prop_families.get(fallback)
        if candidate is not None and candidate.available:
            fallback_logs.append(
                {
                    "scene_id": scene_id,
                    "requested_family": requested,
                    "fallback_family": fallback,
                    "reason": "requested_prop_family_unavailable",
                }
            )
            return fallback
    return requested


def _band_focus_for_scene(scene: Any, band_sync_payload: Mapping[str, Any] | None) -> str:
    start = _start_ms(scene)
    for item in (band_sync_payload or {}).get("performer_focus", []) or []:
        try:
            if int(item.get("start_ms", 0)) <= start < int(item.get("end_ms", 0)):
                return str(item.get("primary_focus", "environment") or "environment")
        except Exception:
            continue
    return "environment"


def _dialogue_recipe(label: str, focus: str, energy: float) -> tuple[str, str, str, str, str]:
    if label in {"intro", "outro"}:
        return ("roofline", "floor_piano", "ambient_callback", "shimmer", "bookend space")
    if label in {"pre-chorus", "buildup"}:
        return ("floor_piano", "arches", "rising_call_response", "sweep", "pre-payoff lift")
    if label == "drop":
        return ("band", "megatree", "impact_answer", "impact", "drop hit")
    if label in {"chorus", "post-chorus"}:
        return ("band", "roofline", "hook_call_response", "bloom", "hook payoff")
    if label in {"bridge", "breakdown"}:
        return ("arches", "band", "negative_space_reply", "orbit" if energy >= 0.42 else "shimmer", "contrast pivot")
    if focus in {"singer", "guitarist", "bassist", "drummer"}:
        return ("band", "floor_piano", "phrase_answer", "ripple", f"{focus} phrase")
    return ("floor_piano", "arches", "supporting_answer", "ripple", "groove phrase")


def _response_delay_ms(label: str, energy: float, duration_ms: int) -> int:
    if label in {"drop", "breakdown"}:
        raw = 90
    elif label in {"chorus", "post-chorus"}:
        raw = 180
    elif label in {"pre-chorus", "buildup"}:
        raw = 240
    else:
        raw = 320
    return max(60, min(max(80, duration_ms // 3), int(round(raw - energy * 70))))


def _palette_hint(scene: Any) -> str:
    palette = _get(scene, "palette", None)
    if isinstance(palette, Mapping):
        return str(palette.get("name", palette.get("temperature", "scene_palette")) or "scene_palette")
    return str(getattr(palette, "name", "") or getattr(palette, "temperature", "") or "scene_palette")


def _cue_for_scene(
    scene: Any,
    index: int,
    prop_lookup: Mapping[str, PropFamily],
    band_sync_payload: Mapping[str, Any] | None,
    fallback_logs: list[dict[str, Any]],
) -> DialogueCue:
    scene_id = _scene_id(scene, index)
    label = _label(scene)
    start = _start_ms(scene)
    end = _end_ms(scene)
    duration = end - start
    energy = _energy(scene)
    focus = _band_focus_for_scene(scene, band_sync_payload)
    source, target, relationship, motion, reason = _dialogue_recipe(label, focus, energy)
    source = _resolve_family(source, prop_lookup, fallback_logs, scene_id)
    target = _resolve_family(target, prop_lookup, fallback_logs, scene_id)
    if source == target:
        for candidate in FALLBACK_FAMILIES.get(target, ()):
            if candidate != source:
                target = _resolve_family(candidate, prop_lookup, fallback_logs, scene_id)
                break
    depth_path = tuple(dict.fromkeys((DEPTH_BY_FAMILY.get(source, "mid"), DEPTH_BY_FAMILY.get(target, "mid"))))
    return DialogueCue(
        scene_id=scene_id,
        start_ms=start,
        end_ms=end,
        source_family=source,
        target_family=target,
        relationship=relationship,
        motion=motion,
        intensity=round(_clamp01(0.34 + energy * 0.58), 4),
        response_delay_ms=_response_delay_ms(label, energy, duration),
        depth_path=depth_path,
        palette_hint=_palette_hint(scene),
        reason=reason,
    )


def _depth_strategy(prop_families: Sequence[PropFamily]) -> DepthStrategy:
    by_depth: dict[str, list[str]] = {"near": [], "mid": [], "far": []}
    for family in prop_families:
        if family.available:
            by_depth.setdefault(family.depth_layer, []).append(family.name)
    for family in PROP_FAMILIES:
        depth = DEPTH_BY_FAMILY[family]
        if family not in by_depth[depth]:
            by_depth[depth].append(family)
    return DepthStrategy(
        near=tuple(by_depth["near"]),
        mid=tuple(by_depth["mid"]),
        far=tuple(by_depth["far"]),
        intensity_scale={"near": 0.9, "mid": 1.0, "far": 0.82},
        parallax_bias={"near": 0.72, "mid": 0.45, "far": 0.22},
    )


def build_spatial_choreography_plan(
    scenes: Sequence[Any],
    *,
    layout: Any | None = None,
    band_sync_payload: Mapping[str, Any] | None = None,
) -> SpatialChoreographyPlan:
    prop_families = classify_prop_families(layout)
    prop_lookup = _available_lookup(prop_families)
    fallback_logs: list[dict[str, Any]] = []
    cues = tuple(
        _cue_for_scene(scene, idx, prop_lookup, band_sync_payload, fallback_logs)
        for idx, scene in enumerate(scenes)
    )
    return SpatialChoreographyPlan(
        prop_families=prop_families,
        dialogue_cues=cues,
        depth_strategy=_depth_strategy(prop_families),
        motion_grammar=MOTION_GRAMMAR,
        fallback_logs=tuple(fallback_logs),
    )
