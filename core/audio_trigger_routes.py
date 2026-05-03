from __future__ import annotations

from dataclasses import asdict, dataclass

from core import audio_reactive_effect_catalog as effect_catalog


@dataclass(frozen=True)
class AudioTriggerRoute:
    name: str
    feature: str
    threshold: float
    effect: str
    min_gap_ms: int
    priority: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


DEFAULT_ROUTES: tuple[AudioTriggerRoute, ...] = (
    AudioTriggerRoute("downbeat_flash_route", "downbeat", 1.0, "downbeat_flash", 900, 95),
    AudioTriggerRoute("drop_burst_route", "energy_smooth", 0.42, "drop_burst", 1200, 90),
    AudioTriggerRoute("bass_pulse_route", "low", 0.16, "bass_pulse", 450, 82),
    AudioTriggerRoute("build_ramp_route", "onset", 0.28, "build_ramp", 700, 76),
    AudioTriggerRoute("mid_sweep_route", "mid", 0.12, "mid_sweep", 650, 70),
    AudioTriggerRoute("treble_sparkle_route", "high", 0.08, "treble_sparkle", 350, 64),
    AudioTriggerRoute("energy_wave_route", "energy_smooth", 0.24, "energy_wave", 850, 58),
    AudioTriggerRoute("quiet_shimmer_route", "inverse_energy_smooth", 0.86, "quiet_shimmer", 1600, 35),
)


FLASH_LIKE_EFFECTS = {"downbeat_flash", "drop_burst"}
SAFE_DENSITY_EFFECT_ROTATION = ("energy_wave", "mid_sweep", "treble_sparkle", "build_ramp")


PROFILE_ROUTE_TUNING: dict[str, dict[str, tuple[float, float, int]]] = {
    "off": {
        "downbeat_flash": (1.0, 3.0, -20),
        "drop_burst": (1.0, 3.0, -20),
        "bass_pulse": (1.0, 3.0, -20),
        "build_ramp": (1.0, 3.0, -20),
        "mid_sweep": (1.0, 3.0, -20),
        "treble_sparkle": (1.0, 3.0, -20),
        "energy_wave": (1.0, 3.0, -20),
        "quiet_shimmer": (1.0, 3.0, -20),
    },
    "subtle": {
        "downbeat_flash": (1.14, 1.45, -8),
        "drop_burst": (1.22, 1.60, -10),
        "bass_pulse": (1.18, 1.45, -8),
        "build_ramp": (1.05, 1.20, -2),
        "mid_sweep": (1.00, 1.10, 2),
        "treble_sparkle": (0.88, 0.82, 8),
        "energy_wave": (1.10, 1.35, -4),
        "quiet_shimmer": (0.92, 0.75, 10),
    },
    "balanced": {},
    "showcase": {
        "downbeat_flash": (0.92, 0.78, 6),
        "drop_burst": (0.84, 0.62, 14),
        "bass_pulse": (0.82, 0.58, 10),
        "build_ramp": (0.82, 0.60, 12),
        "mid_sweep": (0.88, 0.70, 7),
        "treble_sparkle": (0.82, 0.55, 8),
        "energy_wave": (0.86, 0.66, 8),
        "quiet_shimmer": (1.05, 1.10, -4),
    },
    "max": {
        "downbeat_flash": (0.82, 0.58, 10),
        "drop_burst": (0.72, 0.45, 18),
        "bass_pulse": (0.72, 0.42, 14),
        "build_ramp": (0.74, 0.45, 16),
        "mid_sweep": (0.78, 0.55, 10),
        "treble_sparkle": (0.72, 0.42, 12),
        "energy_wave": (0.76, 0.50, 12),
        "quiet_shimmer": (1.10, 1.25, -8),
    },
}


PROFILE_FLASH_ACTION_LIMITS_PER_SECOND: dict[str, float] = {
    "off": 0.0,
    "subtle": 0.32,
    "balanced": 0.55,
    "showcase": 0.68,
    "max": 0.55,
}


def routes_for_profile(profile: str | None) -> tuple[AudioTriggerRoute, ...]:
    key = (profile or "balanced").strip().lower().replace("-", "_").replace(" ", "_")
    tuning = PROFILE_ROUTE_TUNING.get(key, PROFILE_ROUTE_TUNING["balanced"])
    if not tuning:
        return DEFAULT_ROUTES
    routes: list[AudioTriggerRoute] = []
    for route in DEFAULT_ROUTES:
        threshold_scale, gap_scale, priority_delta = tuning.get(route.effect, (1.0, 1.0, 0))
        routes.append(
            AudioTriggerRoute(
                route.name,
                route.feature,
                max(0.0, min(1.0, route.threshold * threshold_scale)),
                route.effect,
                max(120, int(round(route.min_gap_ms * gap_scale))),
                route.priority + priority_delta,
            )
        )
    return tuple(routes)


def routes_as_dicts(routes: tuple[AudioTriggerRoute, ...] = DEFAULT_ROUTES) -> list[dict[str, object]]:
    return [route.to_dict() for route in routes]


def build_audio_reactive_actions(
    beat_timeline: list[dict[str, object]],
    *,
    routes: tuple[AudioTriggerRoute, ...] = DEFAULT_ROUTES,
    max_actions: int = 192,
) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    last_hit_ms: dict[str, int] = {}
    active_conflicts_by_time: dict[int, set[str]] = {}

    for frame in beat_timeline:
        time_ms = _safe_int(frame.get("time_ms", 0))
        conflicts = active_conflicts_by_time.setdefault(time_ms, set())
        for route in sorted(routes, key=lambda item: item.priority, reverse=True):
            if not _route_matches(route, frame):
                continue
            previous = last_hit_ms.get(route.effect)
            if previous is not None and time_ms - previous < route.min_gap_ms:
                continue
            effect = effect_catalog.effect_by_name(route.effect)
            if effect is None:
                continue
            if conflicts.intersection(effect.conflicts):
                continue
            action = effect.to_dict()
            action.update(
                {
                    "time_ms": time_ms,
                    "route": route.name,
                    "effect": effect.name,
                    "feature_value": round(_feature_value(frame, route.feature), 4),
                    "reason": f"{route.feature}>={route.threshold:g}",
                }
            )
            actions.append(action)
            last_hit_ms[route.effect] = time_ms
            conflicts.update(effect.conflicts)
            if len(actions) >= max_actions:
                return actions
    return actions


def rebalance_flash_pressure(
    actions: list[dict[str, object]],
    *,
    profile: str | None,
    duration_s: float,
) -> list[dict[str, object]]:
    key = (profile or "balanced").strip().lower().replace("-", "_").replace(" ", "_")
    limit_per_second = PROFILE_FLASH_ACTION_LIMITS_PER_SECOND.get(key, PROFILE_FLASH_ACTION_LIMITS_PER_SECOND["balanced"])
    flash_budget = max(0, int(round(max(1.0, float(duration_s)) * limit_per_second)))
    if flash_budget <= 0:
        return [_to_safe_density_action(action, idx) for idx, action in enumerate(actions)]

    kept_flash = 0
    converted_index = 0
    rebalanced: list[dict[str, object]] = []
    for action in actions:
        effect_name = str(action.get("effect", "") or "")
        if effect_name not in FLASH_LIKE_EFFECTS:
            rebalanced.append(action)
            continue
        if kept_flash < flash_budget:
            kept_flash += 1
            rebalanced.append(action)
            continue
        rebalanced.append(_to_safe_density_action(action, converted_index))
        converted_index += 1
    return rebalanced


def _to_safe_density_action(action: dict[str, object], index: int) -> dict[str, object]:
    replacement_name = SAFE_DENSITY_EFFECT_ROTATION[index % len(SAFE_DENSITY_EFFECT_ROTATION)]
    replacement = effect_catalog.effect_by_name(replacement_name)
    if replacement is None:
        return action
    converted = replacement.to_dict()
    converted.update(
        {
            "time_ms": action.get("time_ms", 0),
            "route": f"{action.get('route', 'audio_reactive')}_safe_density",
            "effect": replacement.name,
            "feature_value": action.get("feature_value", 0.0),
            "reason": f"safe_density_rebalance:{action.get('effect', '')}",
            "original_effect": action.get("effect", ""),
        }
    )
    return converted


def build_audio_reactive_summary(
    actions: list[dict[str, object]],
    *,
    routes: tuple[AudioTriggerRoute, ...] = DEFAULT_ROUTES,
) -> dict[str, object]:
    return {
        "action_count": len(actions),
        "effect_counts": effect_catalog.summarize_effect_usage(actions),
        "routes": routes_as_dicts(routes),
        "catalog": effect_catalog.catalog_as_dicts(),
    }


def _route_matches(route: AudioTriggerRoute, frame: dict[str, object]) -> bool:
    return _feature_value(frame, route.feature) >= route.threshold


def _feature_value(frame: dict[str, object], feature: str) -> float:
    if feature == "downbeat":
        return 1.0 if bool(frame.get("downbeat", False)) else 0.0
    if feature.startswith("inverse_"):
        return 1.0 - _feature_value(frame, feature.removeprefix("inverse_"))
    try:
        return float(frame.get(feature, 0.0) or 0.0)
    except Exception:
        return 0.0


def _safe_int(value: object) -> int:
    try:
        return int(value)
    except Exception:
        return 0
