from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


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


def _label(section: Any) -> str:
    return str(getattr(section, "label", "") or "section").strip().lower()


def _energy(section: Any, energy_curve: Any | None = None) -> float:
    if energy_curve is not None:
        try:
            return _clamp01(
                float(
                    energy_curve.energy_between(
                        int(getattr(section, "start_ms", 0) or 0),
                        int(getattr(section, "end_ms", 0) or 0),
                    )
                )
            )
        except Exception:
            pass
    return _clamp01(_safe_float(getattr(section, "energy", 0.5), 0.5))


def _section_bounds(section: Any) -> tuple[int, int]:
    start = max(0, int(getattr(section, "start_ms", 0) or 0))
    end = max(start + 1, int(getattr(section, "end_ms", start + 1) or (start + 1)))
    return start, end


@dataclass(frozen=True)
class PaletteState:
    name: str
    temperature: str
    brightness: str
    primary: str
    secondary: str
    accent: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class Scene:
    scene_id: str
    section_label: str
    start_ms: int
    end_ms: int
    energy: float
    scene_mode: str
    palette: PaletteState
    primary_focal_element: str
    supporting_layer: str
    motion_layer: str
    background_ambience: str
    density: str
    brightness: str
    motion: str
    temperature: str
    motif_keys: tuple[str, ...] = ()
    crossfade_in_ms: int = 0
    crossfade_out_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["palette"] = self.palette.to_dict()
        data["motif_keys"] = list(self.motif_keys)
        return data


@dataclass(frozen=True)
class SceneTransition:
    start_ms: int
    end_ms: int
    from_scene_id: str
    to_scene_id: str
    transition_type: str
    crossfade_ms: int
    palette_shift: str
    energy_delta: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScenePlan:
    scenes: tuple[Scene, ...]
    transitions: tuple[SceneTransition, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "helix.scene_engine.v1",
            "scene_count": len(self.scenes),
            "transition_count": len(self.transitions),
            "scenes": [scene.to_dict() for scene in self.scenes],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "palette_evolution": [
                {
                    "scene_id": scene.scene_id,
                    "start_ms": scene.start_ms,
                    "palette": scene.palette.to_dict(),
                }
                for scene in self.scenes
            ],
        }


def _decision_map(contrast_plan: Any | None) -> dict[tuple[int, int], Any]:
    if contrast_plan is None:
        return {}
    decisions = getattr(contrast_plan, "decisions", None)
    if decisions is None and isinstance(contrast_plan, Mapping):
        decisions = contrast_plan.get("decisions", [])
    out: dict[tuple[int, int], Any] = {}
    for decision in decisions or []:
        start = int(getattr(decision, "start_ms", 0) if not isinstance(decision, Mapping) else decision.get("start_ms", 0))
        end = int(getattr(decision, "end_ms", start + 1) if not isinstance(decision, Mapping) else decision.get("end_ms", start + 1))
        out[(start, end)] = decision
    return out


def _decision_value(decision: Any | None, key: str, default: str) -> str:
    if decision is None:
        return default
    if isinstance(decision, Mapping):
        return str(decision.get(key, default) or default)
    return str(getattr(decision, key, default) or default)


def _fallback_density(label: str, energy: float) -> str:
    if label in {"intro", "outro", "breakdown"} or energy < 0.34:
        return "sparse"
    if label in {"chorus", "drop"} and energy >= 0.68:
        return "dense"
    return "medium"


def _fallback_brightness(label: str, energy: float) -> str:
    if label == "breakdown" or energy < 0.36:
        return "dark"
    if label in {"chorus", "drop"} and energy >= 0.66:
        return "bright"
    return "balanced"


def _fallback_motion(label: str, energy: float) -> str:
    if label in {"buildup", "drop"} or energy >= 0.78:
        return "active"
    if label in {"intro", "outro", "breakdown"}:
        return "still"
    return "gentle"


def _palette_for(label: str, temperature: str, brightness: str, index: int) -> PaletteState:
    if brightness == "dark":
        if temperature == "warm":
            return PaletteState("ember_shadow", temperature, brightness, "#3a0906", "#9d2a19", "#ffc857")
        return PaletteState("midnight_ice", temperature, brightness, "#07111f", "#1f5f8b", "#d7f7ff")
    if brightness == "bright":
        if temperature == "warm":
            return PaletteState("golden_impact", temperature, brightness, "#ffcf4a", "#ff4f5e", "#fff8dc")
        return PaletteState("electric_frost", temperature, brightness, "#2bd9ff", "#5a6cff", "#ffffff")
    if label in {"bridge", "breakdown"}:
        return PaletteState("moonlit_teal", "cool", brightness, "#0f6f78", "#6be7c8", "#f7f3d6")
    if temperature == "warm" or index % 2 == 0:
        return PaletteState("lantern_mix", "warm", brightness, "#ff8a3d", "#2e9f82", "#ffe7a6")
    return PaletteState("aurora_mix", "cool", brightness, "#4db6ff", "#7f52ff", "#b8ffd9")


def _scene_mode(label: str, energy: float, density: str) -> str:
    if label in {"intro", "outro"}:
        return "bookend"
    if label == "buildup" or (energy >= 0.55 and density != "dense" and label == "pre-chorus"):
        return "rising_tension"
    if label == "drop":
        return "impact_release"
    if label == "chorus":
        return "wide_payoff"
    if label in {"breakdown", "bridge"}:
        return "negative_space" if energy < 0.46 else "thematic_pivot"
    return "narrative_phrase"


def _primary_focal(label: str, energy: float) -> str:
    if label in {"drop", "breakdown"}:
        return "percussion_impact"
    if label in {"chorus", "post-chorus"}:
        return "hook_signature"
    if label in {"buildup", "pre-chorus"}:
        return "rising_motion"
    if label in {"intro", "outro"}:
        return "environment"
    if energy >= 0.68:
        return "melodic_lead"
    return "vocal_or_phrase_lead"


def _supporting_layer(label: str, density: str) -> str:
    if density == "sparse":
        return "single_color_support"
    if label in {"chorus", "drop", "post-chorus"}:
        return "bass_and_harmony_support"
    if label in {"bridge", "breakdown"}:
        return "textural_counterline"
    return "rhythmic_color_support"


def _motion_layer(motion: str, label: str) -> str:
    if motion == "active":
        return "cascade" if label in {"drop", "chorus"} else "sweep"
    if motion == "still":
        return "held_glow"
    return "slow_drift"


def _background_ambience(brightness: str, density: str) -> str:
    if brightness == "dark":
        return "low_black_floor"
    if density == "dense":
        return "restrained_wash"
    return "soft_air"


def _motif_keys_for_section(section: Any, motif_report: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not motif_report:
        return ()
    start, end = _section_bounds(section)
    keys: list[str] = []
    for hook in motif_report.get("hooks", []) or []:
        if not isinstance(hook, Mapping):
            continue
        fingerprint = hook.get("fingerprint", {}) if isinstance(hook.get("fingerprint", {}), Mapping) else {}
        key = str(fingerprint.get("key", "") or "")
        if not key:
            continue
        for occurrence in hook.get("occurrences", []) or []:
            if not isinstance(occurrence, Mapping):
                continue
            occ_start = int(occurrence.get("start_ms", 0) or 0)
            occ_end = int(occurrence.get("end_ms", occ_start + 1) or (occ_start + 1))
            if occ_start < end and start < occ_end:
                keys.append(key)
                break
    return tuple(dict.fromkeys(keys))


def _crossfade_ms(previous: Scene, current: Scene, max_crossfade_ms: int) -> int:
    duration_limit = max(120, min(previous.end_ms - previous.start_ms, current.end_ms - current.start_ms) // 4)
    delta = abs(current.energy - previous.energy)
    raw = int(round(180 + delta * 620))
    if previous.scene_mode == "rising_tension" or current.scene_mode in {"wide_payoff", "impact_release"}:
        raw += 120
    return max(120, min(int(max_crossfade_ms), duration_limit, raw))


def _transition_type(previous: Scene, current: Scene) -> str:
    delta = current.energy - previous.energy
    if current.section_label == "drop" and delta >= 0.18:
        return "blackout_impact"
    if previous.scene_mode == "rising_tension" or current.scene_mode == "rising_tension":
        return "swell_crossfade"
    if previous.temperature != current.temperature or previous.density != current.density:
        return "contrast_cut"
    return "dissolve"


def _build_transitions(scenes: Sequence[Scene], max_crossfade_ms: int) -> tuple[SceneTransition, ...]:
    transitions: list[SceneTransition] = []
    for previous, current in zip(scenes, scenes[1:]):
        fade = _crossfade_ms(previous, current, max_crossfade_ms)
        boundary = current.start_ms
        transition_type = _transition_type(previous, current)
        transitions.append(
            SceneTransition(
                start_ms=max(previous.start_ms, boundary - fade),
                end_ms=min(current.end_ms, boundary + fade),
                from_scene_id=previous.scene_id,
                to_scene_id=current.scene_id,
                transition_type=transition_type,
                crossfade_ms=fade,
                palette_shift=f"{previous.palette.name}_to_{current.palette.name}",
                energy_delta=round(current.energy - previous.energy, 4),
            )
        )
    return tuple(transitions)


def build_scene_plan(
    sections: Sequence[Any],
    *,
    energy_curve: Any | None = None,
    contrast_plan: Any | None = None,
    motif_report: Mapping[str, Any] | None = None,
    max_crossfade_ms: int = 1200,
) -> ScenePlan:
    decisions = _decision_map(contrast_plan)
    scenes: list[Scene] = []
    for idx, section in enumerate(sections):
        start, end = _section_bounds(section)
        label = _label(section)
        energy = _energy(section, energy_curve)
        decision = decisions.get((start, end))
        density = _decision_value(decision, "density", _fallback_density(label, energy))
        brightness = _decision_value(decision, "brightness", _fallback_brightness(label, energy))
        motion = _decision_value(decision, "motion", _fallback_motion(label, energy))
        temperature = _decision_value(decision, "temperature", "warm" if idx % 2 == 0 else "cool")
        palette = _palette_for(label, temperature, brightness, idx)
        mode = _scene_mode(label, energy, density)
        scenes.append(
            Scene(
                scene_id=f"scene_{idx + 1:02d}_{label.replace('-', '_')}",
                section_label=label,
                start_ms=start,
                end_ms=end,
                energy=round(energy, 4),
                scene_mode=mode,
                palette=palette,
                primary_focal_element=_primary_focal(label, energy),
                supporting_layer=_supporting_layer(label, density),
                motion_layer=_motion_layer(motion, label),
                background_ambience=_background_ambience(brightness, density),
                density=density,
                brightness=brightness,
                motion=motion,
                temperature=temperature,
                motif_keys=_motif_keys_for_section(section, motif_report),
                metadata={
                    "source": "section_energy_contrast_motif_rules",
                    "section_index": idx,
                    "duration_ms": end - start,
                },
            )
        )
    transitions = _build_transitions(scenes, max_crossfade_ms=max_crossfade_ms)
    fade_in_by_scene = {transition.to_scene_id: transition.crossfade_ms for transition in transitions}
    fade_out_by_scene = {transition.from_scene_id: transition.crossfade_ms for transition in transitions}
    scenes = [
        Scene(
            **{
                **scene.to_dict(),
                "palette": scene.palette,
                "motif_keys": scene.motif_keys,
                "crossfade_in_ms": fade_in_by_scene.get(scene.scene_id, 0),
                "crossfade_out_ms": fade_out_by_scene.get(scene.scene_id, 0),
            }
        )
        for scene in scenes
    ]
    return ScenePlan(scenes=tuple(scenes), transitions=transitions)
