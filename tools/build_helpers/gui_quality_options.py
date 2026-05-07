"""GUI-safe quality option contract for Helix output improvements.

Slice 10 starts as a small contract/normalizer only. It does not modify GUI files,
render effects, write XSQ content, or change current output by default. The goal is
to give GUI code a stable, validated shape for quality-related controls before any
launcher wiring is attempted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


QUALITY_PRESETS = {"general", "showcase", "vendor"}
STYLE_PRESETS = {
    "general",
    "classic_christmas",
    "edm",
    "rock",
    "ballad",
    "comedy",
    "spooky",
    "patriotic",
}


class GuiQualityOptionsError(ValueError):
    """Raised when GUI quality options cannot be normalized safely."""


@dataclass(frozen=True)
class GuiQualityOptions:
    """Validated GUI-facing output-quality options."""

    quality_preset: str = "showcase"
    style_preset: str = "general"
    enable_prop_roles: bool = True
    enable_density_restraint: bool = True
    enable_section_identity: bool = True
    enable_palette_discipline: bool = True
    enable_motif_memory: bool = True
    enable_manual_locks: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        if self.quality_preset not in QUALITY_PRESETS:
            raise GuiQualityOptionsError(f"Unsupported quality preset: {self.quality_preset}")
        if self.style_preset not in STYLE_PRESETS:
            raise GuiQualityOptionsError(f"Unsupported style preset: {self.style_preset}")
        if not self.report_only and self.enable_manual_locks:
            # Slice 10 does not permit GUI enforcement yet. Manual locks must be
            # reported before they can control generation.
            raise GuiQualityOptionsError("manual locks are report-only in Slice 10")

    def as_dict(self) -> dict[str, object]:
        return {
            "quality_preset": self.quality_preset,
            "style_preset": self.style_preset,
            "enable_prop_roles": self.enable_prop_roles,
            "enable_density_restraint": self.enable_density_restraint,
            "enable_section_identity": self.enable_section_identity,
            "enable_palette_discipline": self.enable_palette_discipline,
            "enable_motif_memory": self.enable_motif_memory,
            "enable_manual_locks": self.enable_manual_locks,
            "report_only": self.report_only,
        }

    def enabled_report_modules(self) -> tuple[str, ...]:
        modules: list[str] = []
        if self.enable_prop_roles:
            modules.append("prop_roles")
        if self.enable_density_restraint:
            modules.append("density_restraint")
        if self.enable_section_identity:
            modules.append("section_identity")
        if self.enable_palette_discipline:
            modules.append("palette_discipline")
        if self.enable_motif_memory:
            modules.append("motif_memory")
        if self.enable_manual_locks:
            modules.append("manual_locks")
        return tuple(modules)

    def cli_args(self) -> tuple[str, ...]:
        """Return future-safe CLI-style options for wrapper/launcher wiring.

        These are not guaranteed to be accepted by the current active engine yet.
        GUI code should only pass arguments that the active command actually
        supports. This method exists to document the intended mapping.
        """

        args = ["--quality-gate-preset", self.quality_preset]
        args.extend(["--helix-style-preset", self.style_preset])
        if self.report_only:
            args.append("--quality-report-only")
        for module in self.enabled_report_modules():
            args.extend(["--enable-quality-report-module", module])
        return tuple(args)


def normalize_gui_quality_options(raw: Mapping[str, object] | None = None) -> GuiQualityOptions:
    """Normalize GUI quality options with safe defaults."""

    data = dict(raw or {})
    return GuiQualityOptions(
        quality_preset=str(data.get("quality_preset", "showcase")),
        style_preset=str(data.get("style_preset", "general")),
        enable_prop_roles=bool(data.get("enable_prop_roles", True)),
        enable_density_restraint=bool(data.get("enable_density_restraint", True)),
        enable_section_identity=bool(data.get("enable_section_identity", True)),
        enable_palette_discipline=bool(data.get("enable_palette_discipline", True)),
        enable_motif_memory=bool(data.get("enable_motif_memory", True)),
        enable_manual_locks=bool(data.get("enable_manual_locks", True)),
        report_only=bool(data.get("report_only", True)),
    )
