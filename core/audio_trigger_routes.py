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


def build_audio_reactive_summary(actions: list[dict[str, object]]) -> dict[str, object]:
    return {
        "action_count": len(actions),
        "effect_counts": effect_catalog.summarize_effect_usage(actions),
        "routes": routes_as_dicts(),
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
