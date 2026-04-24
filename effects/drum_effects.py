from __future__ import annotations

from typing import Iterable

from audio.drum_classification import DrumEvent


DEFAULT_DRUM_EFFECTS = {
    "kick": {"effect": "low_frequency_glow", "duration_ms": 220, "spatial": "ground_spread", "layer": "accent"},
    "snare": {"effect": "sharp_white_flash", "duration_ms": 120, "spatial": "lateral_flash", "layer": "accent"},
    "tom": {"effect": "mid_bounce_pulse", "duration_ms": 180, "spatial": "body_bounce", "layer": "motion"},
    "hihat": {"effect": "rapid_shimmer_tick", "duration_ms": 80, "spatial": "spark_particles", "layer": "accent"},
    "cymbal": {"effect": "wide_bright_wash", "duration_ms": 360, "spatial": "wide_wash_tail", "layer": "motion"},
    "drum_bus": {"effect": "drum_bus_pulse", "duration_ms": 150, "spatial": "fallback_impulse", "layer": "motion"},
}


def build_drum_effect_cues(events: Iterable[DrumEvent], *, spatial_enabled: bool = True, piano_hooks: bool = True) -> list[dict[str, object]]:
    cues: list[dict[str, object]] = []
    for event in sorted(events, key=lambda item: item.timestamp_ms):
        defaults = DEFAULT_DRUM_EFFECTS.get(event.drum_type, DEFAULT_DRUM_EFFECTS["drum_bus"])
        duration = int(defaults["duration_ms"] * (0.72 + event.velocity * 0.56))
        cues.append(
            {
                "start_ms": event.timestamp_ms,
                "end_ms": event.timestamp_ms + max(50, duration),
                "drum_type": event.drum_type,
                "effect": defaults["effect"],
                "layer": defaults["layer"],
                "intensity": round(event.velocity, 3),
                "confidence": event.confidence,
                "submodel": "hi_hat" if event.drum_type == "hihat" else event.drum_type,
                "spatial_impulse": {
                    "enabled": bool(spatial_enabled),
                    "mode": defaults["spatial"],
                    "propagate_to": ["trees", "arches", "matrices"],
                    "strength": round(event.velocity * event.confidence, 3),
                },
                "player_piano_hook": {
                    "enabled": bool(piano_hooks),
                    "trigger": "floor_piano_percussive_note" if event.drum_type in {"kick", "snare"} else "grid_tick",
                    "velocity": round(event.velocity, 3),
                },
                "effect_scoring_hint": "allow_layering_with_shaders_and_spatial_engine",
            }
        )
    return cues
