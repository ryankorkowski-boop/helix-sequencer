from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineName:
    slug: str
    public_name: str
    internal_name: str


ENGINE_NAMES: dict[str, EngineName] = {
    "helix_flow": EngineName("helix_flow", "Helix Flow Engine", "Helix Flow Engine"),
    "hardkor": EngineName("hardkor", "Helix Impact Engine", "Hardkor Engine"),
    "chrono": EngineName("chrono", "Helix Time Engine", "Chrono Engine"),
}


def public_engine_name(slug: str) -> str:
    return ENGINE_NAMES[slug].public_name


def internal_engine_name(slug: str) -> str:
    return ENGINE_NAMES[slug].internal_name
