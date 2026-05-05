"""Instrument-aware realism mapping for routed stem events.

This layer upgrades raw StemRoute actions into richer effect rows for xLights-facing
output. It keeps instrument/model/submodel routing intact while assigning effects,
palettes, motion profiles, and decay behavior that better match real performance.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.stem_routing import StemRoute


@dataclass(frozen=True)
class RealismEffectProfile:
    effect: str
    palette: tuple[str, ...]
    motion: str | None
    duration_scale: float = 1.0
    intensity_scale: float = 1.0
    decay: str | None = None


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def profile_for_route(route: StemRoute) -> RealismEffectProfile:
    stem = route.stem.lower().replace(" ", "_")
    event = route.event_type.lower().replace(" ", "_")
    submodel = route.target_submodel.lower().replace(" ", "_")
    action = route.action.lower().replace(" ", "_")

    if stem in {"guitar", "electric_guitar", "acoustic_guitar"}:
        if "strings" in submodel:
            return RealismEffectProfile("string_ripple", ("white", "cyan"), "string_directional", 0.9, 1.0, "short")
        if "left_hand" in submodel:
            return RealismEffectProfile("fret_slide", ("blue", "white"), "neck_follow", 1.0, 0.72, "medium")
        if "right_hand" in submodel:
            return RealismEffectProfile("pick_flicker", ("white",), "pick_motion", 0.55, 0.92, "short")
        if "arms" in submodel:
            return RealismEffectProfile("arm_motion", ("warm_white",), "strum_arc", 1.15, 0.62, "medium")

    if stem in {"bass", "bass_guitar"}:
        if "strings" in submodel:
            return RealismEffectProfile("bass_string_pulse", ("deep_blue", "white"), "low_string_throb", 1.25, 1.0, "medium")
        if "left_hand" in submodel:
            return RealismEffectProfile("bass_fret_shift", ("blue",), "neck_follow", 1.0, 0.66, "medium")
        if "right_hand" in submodel:
            return RealismEffectProfile("bass_pluck", ("white", "blue"), "finger_pluck", 0.8, 0.88, "short")
        if "arms" in submodel:
            return RealismEffectProfile("bass_groove_motion", ("blue",), "groove_sway", 1.3, 0.58, "medium")

    if stem in {"drums", "percussion"}:
        if event == "kick" or submodel == "kick":
            return RealismEffectProfile("kick_thump", ("red", "white"), "center_pop", 0.35, 1.0, "short")
        if event == "snare" or submodel == "snare":
            return RealismEffectProfile("snare_crack", ("white",), "snap_flash", 0.25, 1.0, "instant")
        if event in {"hi_hat", "hihat"} or submodel == "hi_hat":
            return RealismEffectProfile("hat_tick", ("silver", "white"), "tight_tick", 0.18, 0.72, "instant")
        if event in {"cymbal", "crash", "ride"} or submodel == "cymbal":
            return RealismEffectProfile("cymbal_decay", ("gold", "white"), "radial_shimmer", 2.1, 0.92, "long")
        if event in {"tom", "toms"} or submodel == "tom":
            return RealismEffectProfile("tom_roll", ("orange", "white"), "left_right_fill", 0.65, 0.9, "medium")
        if submodel == "arms":
            return RealismEffectProfile("stick_motion", ("warm_white",), "stick_arc", 0.55, 0.75, "short")
        return RealismEffectProfile("percussion_hit", ("white",), "percussion_pop", 0.4, 0.8, "short")

    if stem in {"lead_vocals", "lead_vocal"}:
        return RealismEffectProfile("lead_face_phoneme" if route.lyric else "lead_vocal_presence", ("white", "gold"), "mouth_shape", 1.0, 1.0, "phrase")

    if stem in {"female_vocals", "female_vocal"}:
        return RealismEffectProfile("female_face_phoneme" if route.lyric else "female_vocal_presence", ("pink", "white"), "mouth_shape", 1.0, 1.0, "phrase")

    if stem in {"backup_vocals", "backup_vocal", "harmony", "choir"}:
        return RealismEffectProfile("backup_face_phoneme" if route.lyric else "backup_vocal_presence", ("purple", "white"), "harmony_mouth_shape", 1.0, 0.78, "phrase")

    return RealismEffectProfile(route.action, ("white",), route.target_submodel, 1.0, 1.0, None)


def route_to_realism_effect_row(route: StemRoute) -> dict:
    profile = profile_for_route(route)
    duration = max(0.001, route.duration * profile.duration_scale)
    intensity = _clamp(route.intensity * profile.intensity_scale)
    return {
        "model": route.target_model,
        "start": route.start,
        "duration": round(duration, 4),
        "effect": profile.effect,
        "palette": list(profile.palette),
        "intensity": round(intensity, 3),
        "motion": profile.motion or route.target_submodel,
        "intent": route.event_type,
        "stem": route.stem,
        "submodel": route.target_submodel,
        "action": route.action,
        "decay": profile.decay,
        "lyric": route.lyric,
    }


def routes_to_realism_effect_rows(routes) -> list[dict]:
    return [route_to_realism_effect_row(route) for route in routes]
