from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Legacy256Profile:
    name: str
    base_profile: str
    quality_gate_preset: str
    variants: int
    description: str
    engine_flags: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


LEGACY_256_PROFILES: dict[str, Legacy256Profile] = {
    "legacy_256_clean": Legacy256Profile(
        name="legacy_256_clean",
        base_profile="v9.2",
        quality_gate_preset="general",
        variants=2,
        description="Conservative AC-safe legacy output with low density and clear timing.",
        engine_flags=(
            "--single",
            "--no-prompt",
            "--no-save-settings",
            "--no-workspace-history",
            "--no-auto-timing-tracks",
            "--no-matrix-intelligence",
        ),
        notes=(
            "Prioritize clean on/fade/chase behavior.",
            "Avoid pixel-only assumptions and matrix-heavy logic.",
            "Use this as the first smoke profile for GP/LMS legacy 256 work.",
        ),
    ),
    "legacy_256_showcase": Legacy256Profile(
        name="legacy_256_showcase",
        base_profile="v9.2",
        quality_gate_preset="showcase",
        variants=3,
        description="Showcase-calibrated 256-channel output with stronger section contrast and controlled density.",
        engine_flags=(
            "--single",
            "--no-prompt",
            "--no-save-settings",
            "--no-workspace-history",
            "--no-auto-timing-tracks",
            "--no-matrix-intelligence",
        ),
        notes=(
            "Use the showcase gate to prefer cleaner winning variants.",
            "Keep density restrained enough for legacy channel inspection.",
            "Best first serious proving-ground profile.",
        ),
    ),
    "legacy_256_pro": Legacy256Profile(
        name="legacy_256_pro",
        base_profile="v9.2",
        quality_gate_preset="pro",
        variants=5,
        description="Strict professional-bar legacy 256 calibration run with the lowest tolerance for rejected effects.",
        engine_flags=(
            "--single",
            "--no-prompt",
            "--no-save-settings",
            "--no-workspace-history",
            "--no-auto-timing-tracks",
            "--no-matrix-intelligence",
        ),
        notes=(
            "Use after clean/showcase prove the layout and template path work.",
            "Strictest quality gate; failures are useful calibration evidence.",
            "Do not loosen this profile just to force a pass.",
        ),
    ),
}


def legacy_256_profile(name: str) -> Legacy256Profile:
    key = name.strip().lower().replace("-", "_")
    if key not in LEGACY_256_PROFILES:
        known = ", ".join(sorted(LEGACY_256_PROFILES))
        raise KeyError(f"Unknown legacy 256 profile {name!r}. Known profiles: {known}")
    return LEGACY_256_PROFILES[key]


def list_legacy_256_profiles() -> list[dict[str, Any]]:
    return [profile.to_dict() for profile in LEGACY_256_PROFILES.values()]
