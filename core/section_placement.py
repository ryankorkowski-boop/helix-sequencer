"""Conservative section caps inside the existing placement callback."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from core.section_composer import Section, SectionPlan


def effect_family(name: str) -> str:
    key = name.lower().replace(" ", "")
    if key in {"on", "ramp", "colorwash"}:
        return "base"
    if key in {"twinkle", "shimmer", "snowflakes", "sparkle"}:
        return "texture"
    if key in {"strobe", "shockwave", "fireworks", "lightning"}:
        return "accent"
    return "motion"


def cap_palette(palette: str | None, budget: float) -> str:
    parts = dict(p.split("=", 1) for p in (palette or "").split(",")
                 if "=" in p)
    if "active=true" in parts.get("C_VALUECURVE_Brightness", "").lower():
        raise ValueError("Section cap cannot bound an active brightness curve")
    previous = float(parts.get("C_SLIDER_Brightness", "100"))
    parts["C_SLIDER_Brightness"] = str(round(min(previous, budget * 100)))
    return ",".join(f"{key}={value}" for key, value in parts.items())


def expand_targets(
    models: Mapping[str, str], groups: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
    targets = {name: [parent or name] for name, parent in models.items()}

    def expand(name: str, seen: frozenset[str]) -> list[str]:
        if name in seen:
            raise ValueError(f"Cyclic section target group: {name}")
        if name not in targets:
            targets[name] = sorted({
                n for child in groups.get(name, ())
                for n in expand(child, seen | {name})})
            if not targets[name]:
                raise ValueError(f"Unknown/empty section target: {name}")
        return targets[name]

    for name in groups:
        expand(name, frozenset())
    return targets


def section_palette(original: str | None, section: Section, *,
                    rgb: bool) -> str:
    parts = dict(p.split("=", 1) for p in (original or "").split(",")
                 if "=" in p)
    if rgb:
        for i in range(1, 9):
            parts[f"C_CHECKBOX_Palette{i}"] = "0"
        for i, color in enumerate(section.palette, 1):
            parts[f"C_BUTTON_Palette{i}"] = color
            parts[f"C_CHECKBOX_Palette{i}"] = "1"
    return cap_palette(",".join(f"{k}={v}" for k, v in parts.items()),
                       section.energy_budget)


@dataclass(frozen=True)
class Placement:
    model: str
    start_ms: int
    end_ms: int
    section: Section


class SectionPlacementBudget:
    """Count expanded model unions in conservative 50-ms slots.

    Reservations occur only after successful XML placement. This is a ceiling,
    not a new effect selector. Existing Birdsong/energy_wave requests remain.
    """

    def __init__(self, plan: SectionPlan,
                 targets: Mapping[str, Sequence[str]]) -> None:
        self.plan = plan
        self.targets = {k: frozenset(v) for k, v in targets.items()}
        self.models = frozenset(n for v in self.targets.values() for n in v
                                if not self.protected(n))
        self.slots: dict[int, set[str]] = {}
        self.rejected = 0
        self.accepted = 0

    @staticmethod
    def protected(model: str) -> bool:
        # Protect all performer channels, including the locked drummer oracle.
        return any(s in model.lower() for s in ("drummer", "hx_snowman"))

    def exempt(self, model: str) -> bool:
        roots = self.targets.get(model, (model,))
        return any(self.protected(n) for n in roots)

    def propose(self, model: str, start: int, end: int,
                effect: str) -> Placement | None:
        section = self.plan.at(start)
        if (section is None
                or effect_family(effect) not in section.allowed_families):
            self.rejected += 1
            return None
        end = min(end, section.end_ms)
        for left, right in self.plan.intentional_restraint:
            if left <= start < right:
                self.rejected += 1
                return None
            if start < left < end:
                end = left
        roots = self.targets.get(model, frozenset((model,)))
        cap = math.ceil(len(self.models) * section.density_cap)
        if end - start < 50 or cap == 0 or any(
                len(self.slots.get(t, set()) | roots) > cap
                for t in range(start // 50, math.ceil(end / 50))):
            self.rejected += 1
            return None
        return Placement(model, start, end, section)

    def commit(self, placement: Placement) -> None:
        roots = self.targets.get(placement.model,
                                 frozenset((placement.model,)))
        for t in range(placement.start_ms // 50,
                       math.ceil(placement.end_ms / 50)):
            self.slots.setdefault(t, set()).update(roots)
        self.accepted += 1
