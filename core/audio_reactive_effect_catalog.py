from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class AudioReactiveEffect:
    name: str
    family: str
    trigger_feature: str
    threshold: float
    target_hint: str
    motion_hint: str
    color_hint: str
    density: float
    priority: int
    conflicts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        out = asdict(self)
        out["conflicts"] = list(self.conflicts)
        return out


EFFECT_CATALOG: tuple[AudioReactiveEffect, ...] = (
    AudioReactiveEffect("downbeat_flash", "accent", "downbeat", 1.0, "whole_house", "instant", "white_gold", 0.42, 95, ("full_intensity",)),
    AudioReactiveEffect("bass_pulse", "bass", "low", 0.16, "large_props", "expand", "warm_red", 0.52, 82, ("full_intensity",)),
    AudioReactiveEffect("mid_sweep", "motion", "mid", 0.12, "arches_lines", "left_right", "blue_green", 0.48, 70, ("large_motion",)),
    AudioReactiveEffect("treble_sparkle", "texture", "high", 0.08, "stars_snowflakes", "twinkle", "cool_white", 0.58, 64, ("dense_texture",)),
    AudioReactiveEffect("energy_wave", "motion", "energy_smooth", 0.24, "all_models", "wave", "rainbow", 0.62, 58, ("large_motion",)),
    AudioReactiveEffect("build_ramp", "build", "onset", 0.28, "sequential_groups", "rise", "cyan_magenta", 0.55, 76, ("large_motion",)),
    AudioReactiveEffect("drop_burst", "accent", "energy_smooth", 0.42, "whole_house", "burst", "white_blue", 0.7, 90, ("full_intensity", "dense_texture")),
    AudioReactiveEffect("quiet_shimmer", "texture", "inverse_energy_smooth", 0.86, "small_props", "slow_shimmer", "soft_pastel", 0.24, 35, ()),
)


def catalog_as_dicts() -> list[dict[str, object]]:
    return [effect.to_dict() for effect in EFFECT_CATALOG]


def effect_by_name(name: str) -> AudioReactiveEffect | None:
    for effect in EFFECT_CATALOG:
        if effect.name == name:
            return effect
    return None


def choose_effects_for_frame(frame: dict[str, object], *, is_downbeat: bool = False, max_effects: int = 3) -> list[dict[str, object]]:
    chosen: list[AudioReactiveEffect] = []
    blocked: set[str] = set()
    for effect in sorted(EFFECT_CATALOG, key=lambda item: item.priority, reverse=True):
        if blocked.intersection(effect.conflicts):
            continue
        if _effect_matches(effect, frame, is_downbeat=is_downbeat):
            chosen.append(effect)
            blocked.update(effect.conflicts)
        if len(chosen) >= max_effects:
            break
    return [effect.to_dict() for effect in chosen]


def summarize_effect_usage(actions: Iterable[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for action in actions:
        name = str(action.get("effect", ""))
        if not name:
            continue
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def _effect_matches(effect: AudioReactiveEffect, frame: dict[str, object], *, is_downbeat: bool) -> bool:
    if effect.trigger_feature == "downbeat":
        return is_downbeat
    value = _frame_value(frame, effect.trigger_feature)
    return value >= effect.threshold


def _frame_value(frame: dict[str, object], key: str) -> float:
    if key.startswith("inverse_"):
        return 1.0 - _frame_value(frame, key.removeprefix("inverse_"))
    try:
        return float(frame.get(key, 0.0) or 0.0)
    except Exception:
        return 0.0
