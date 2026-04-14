from __future__ import annotations

from dataclasses import dataclass

from core import effect_engine


@dataclass(frozen=True)
class EngineProfile:
    profile_id: str
    version: str
    title: str
    description: str
    legacy: bool = False


ACTIVE_PROFILE_ID = "master"

_ACTIVE_PROFILE = EngineProfile(
    profile_id=ACTIVE_PROFILE_ID,
    version=effect_engine.ACTIVE_STYLE_VERSION,
    title="Master Sequencer",
    description="Stable active sequencing profile backed by the current Helix Prime tuning.",
)

_PROFILE_ALIASES = {
    "default": ACTIVE_PROFILE_ID,
    "stable": ACTIVE_PROFILE_ID,
    "latest": ACTIVE_PROFILE_ID,
    effect_engine.ACTIVE_STYLE_VERSION.lower(): ACTIVE_PROFILE_ID,
}


def available_profiles() -> list[EngineProfile]:
    return [_ACTIVE_PROFILE]


def active_profile() -> EngineProfile:
    return _ACTIVE_PROFILE


def resolve_profile(profile_id: str | None) -> EngineProfile:
    if profile_id is None:
        return _ACTIVE_PROFILE

    key = profile_id.strip().lower()
    if not key:
        return _ACTIVE_PROFILE
    if key == _ACTIVE_PROFILE.profile_id:
        return _ACTIVE_PROFILE
    alias = _PROFILE_ALIASES.get(key)
    if alias == ACTIVE_PROFILE_ID:
        return _ACTIVE_PROFILE
    if key in effect_engine.VARIANTS:
        style = effect_engine.VARIANTS[key]
        return EngineProfile(
            profile_id=style.version,
            version=style.version,
            title=style.title,
            description="Legacy compatibility profile.",
            legacy=True,
        )
    raise KeyError(f"Unknown engine profile: {profile_id}")
