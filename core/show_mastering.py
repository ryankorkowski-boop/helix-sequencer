from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Sequence

from core.engine_coordinator import (
    AudioAnalysisContext,
    CoordinationResult,
    EngineEffectCandidate,
    LayoutProp,
    PlannedEffect,
    SectionWindow,
)


SECTION_DENSITY_PRESETS: dict[str, dict[str, float]] = {
    "intro": {"max_active_prop_ratio": 0.25, "energy_target": 0.25},
    "verse": {"max_active_prop_ratio": 0.45, "energy_target": 0.45},
    "pre_chorus": {"max_active_prop_ratio": 0.65, "energy_target": 0.65},
    "bridge": {"max_active_prop_ratio": 0.40, "energy_target": 0.40},
    "chorus": {"max_active_prop_ratio": 0.90, "energy_target": 0.90},
    "drop": {"max_active_prop_ratio": 1.00, "energy_target": 1.00},
    "climax": {"max_active_prop_ratio": 1.00, "energy_target": 1.00},
    "outro": {"max_active_prop_ratio": 0.25, "energy_target": 0.25},
}

_HIGH_IMPACT_SECTIONS = frozenset({"chorus", "drop", "climax"})
_QUIET_SECTIONS = frozenset({"intro", "outro", "bridge"})
_CHARACTER_TAGS = frozenset({"character", "snowman", "face", "singing_face", "vocal"})


@dataclass(frozen=True)
class SectionPalette:
    """Cohesive four-color palette with section-aware ordering."""

    primary: str
    secondary: str
    accent: str
    neutral: str

    def colors_for_section(self, section_name: str | None = None) -> tuple[str, str, str, str]:
        normalized = _normalize_section_name(section_name)
        if normalized in _HIGH_IMPACT_SECTIONS:
            return (self.primary, self.accent, self.secondary, self.neutral)
        if normalized in _QUIET_SECTIONS:
            return (self.neutral, self.primary, self.secondary, self.accent)
        return (self.primary, self.secondary, self.accent, self.neutral)


DEFAULT_PALETTES: dict[str, SectionPalette] = {
    "winter_aurora": SectionPalette(
        primary="#00D2FF",
        secondary="#3A7BD5",
        accent="#A8FF78",
        neutral="#E6F4FF",
    ),
    "classic_christmas": SectionPalette(
        primary="#D90429",
        secondary="#2B9348",
        accent="#FFD166",
        neutral="#FFF8E7",
    ),
    "electric_rock": SectionPalette(
        primary="#FF0055",
        secondary="#7B2CBF",
        accent="#00F5D4",
        neutral="#F8F9FA",
    ),
    "warm_gold": SectionPalette(
        primary="#FFB703",
        secondary="#FB8500",
        accent="#FFF3B0",
        neutral="#FDF0D5",
    ),
}


@dataclass(frozen=True)
class ShowMasteringConfig:
    """Configuration for pro vendor-grade show mastering."""

    palette_name: str = "winter_aurora"
    anticipation_breath_ms: int = 100
    default_fade_ms: int = 150
    motif_bonus: float = 0.15
    enforce_negative_space: bool = True
    lock_palette: bool = True
    bpm_sync_speed: bool = True


def _normalize_section_name(name: str | None) -> str:
    if not name:
        return ""
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def _effect_family(effect_type: str) -> str:
    cleaned = effect_type.strip().lower()
    if not cleaned:
        return ""
    for sep in ("_", "-"):
        if sep in cleaned:
            return cleaned.split(sep, 1)[0]
    return cleaned


def _resolve_section(effect: PlannedEffect, audio_ctx: AudioAnalysisContext) -> SectionWindow | None:
    if effect.section_name:
        target = _normalize_section_name(effect.section_name)
        for sec in audio_ctx.sections:
            if _normalize_section_name(sec.name) == target and sec.start_ms <= effect.start_ms < sec.end_ms:
                return sec
        for sec in audio_ctx.sections:
            if _normalize_section_name(sec.name) == target:
                return sec
    midpoint = (effect.start_ms + effect.end_ms) // 2
    return audio_ctx.section_for_ms(midpoint)


def _is_character_effect(effect: PlannedEffect, prop: LayoutProp | None) -> bool:
    if effect.params.get("preserve_colors"):
        return True
    if effect.engine_id == "snowman_band":
        return True
    if prop is not None:
        if prop.prop_type.strip().lower() in _CHARACTER_TAGS:
            return True
        if any(tag.strip().lower() in _CHARACTER_TAGS for tag in prop.tags):
            return True
    return False


class ProShowMaster:
    """Applies restraint, motif continuity, breath carving, palette locking, and transitions."""

    def __init__(self, config: ShowMasteringConfig | None = None) -> None:
        self.config = config or ShowMasteringConfig()

    def apply_motif_continuity(
        self,
        candidates: Sequence[EngineEffectCandidate],
        audio_ctx: AudioAnalysisContext,
    ) -> list[EngineEffectCandidate]:
        choruses = sorted(
            (s for s in audio_ctx.sections if "chorus" in _normalize_section_name(s.name)),
            key=lambda s: s.start_ms,
        )
        if len(choruses) < 2 or not candidates:
            return list(candidates)

        first_chorus = choruses[0]
        first_overlapping = [
            c
            for c in candidates
            if c.end_ms > first_chorus.start_ms and c.start_ms < first_chorus.end_ms
        ]
        if not first_overlapping:
            return list(candidates)

        hero_pool = [c for c in first_overlapping if c.role in ("focus", "accent")] or first_overlapping
        top_hero = max(
            hero_pool,
            key=lambda c: (c.score, 1 if c.role == "focus" else 0),
        )
        hero_family = _effect_family(top_hero.effect_type)
        if not hero_family:
            return list(candidates)

        later_choruses = choruses[1:]
        updated: list[EngineEffectCandidate] = []
        for candidate in candidates:
            in_later_chorus = any(
                candidate.end_ms > ch.start_ms and candidate.start_ms < ch.end_ms
                for ch in later_choruses
            )
            if in_later_chorus and _effect_family(candidate.effect_type) == hero_family:
                new_meta = dict(candidate.metadata)
                new_meta["motif_callback"] = True
                new_meta["motif_family"] = hero_family
                updated.append(
                    replace(
                        candidate,
                        score=round(candidate.score + self.config.motif_bonus, 6),
                        metadata=new_meta,
                    )
                )
            else:
                updated.append(candidate)
        return updated

    def enforce_section_negative_space(
        self,
        effects: Sequence[PlannedEffect],
        audio_ctx: AudioAnalysisContext,
        layout_props: Sequence[LayoutProp],
    ) -> list[PlannedEffect]:
        if not effects:
            return []

        prop_map = {p.prop_id: p for p in layout_props}
        total_props = len(prop_map) if prop_map else len({e.prop_id for e in effects})
        if total_props <= 0:
            return list(effects)

        grouped: dict[tuple[str, int], list[tuple[int, PlannedEffect, SectionWindow | None]]] = {}
        for idx, eff in enumerate(effects):
            sec = _resolve_section(eff, audio_ctx)
            key = (_normalize_section_name(sec.name), sec.start_ms) if sec is not None else ("", -1)
            grouped.setdefault(key, []).append((idx, eff, sec))

        kept_indices: set[int] = set()
        for _key, items in grouped.items():
            sec = items[0][2]
            max_ratio = getattr(sec, "max_active_prop_ratio", None) if sec is not None else None
            if max_ratio is None and sec is not None:
                preset = SECTION_DENSITY_PRESETS.get(_normalize_section_name(sec.name))
                max_ratio = preset["max_active_prop_ratio"] if preset else 1.0
            if max_ratio is None:
                max_ratio = 1.0

            if max_ratio <= 0.0:
                allowed_props = 0
            else:
                allowed_props = max(1, int(math.floor(total_props * max_ratio)))

            by_prop: dict[str, list[tuple[int, PlannedEffect]]] = {}
            for idx, eff, _ in items:
                by_prop.setdefault(eff.prop_id, []).append((idx, eff))

            def _prop_rank(prop_id: str) -> tuple[int, int, int, float]:
                prop_effects = [eff for _, eff in by_prop[prop_id]]
                prop = prop_map.get(prop_id)
                has_focus = 1 if any(e.role == "focus" for e in prop_effects) else 0
                has_hero_tag = (
                    1
                    if prop is not None
                    and any(t.strip().lower() in ("hero", "focus") for t in prop.tags)
                    else 0
                )
                max_priority = max(e.priority for e in prop_effects)
                max_score = max(e.score for e in prop_effects)
                return (has_focus, has_hero_tag, max_priority, max_score)

            ranked_props = sorted(by_prop.keys(), key=_prop_rank, reverse=True)
            allowed_prop_ids = set(ranked_props[:allowed_props])

            for idx, eff, _ in items:
                if eff.prop_id in allowed_prop_ids or eff.role == "focus":
                    kept_indices.add(idx)

        return [eff for idx, eff in enumerate(effects) if idx in kept_indices]

    def master_plan(
        self,
        result: CoordinationResult,
        audio_ctx: AudioAnalysisContext,
        layout_props: Sequence[LayoutProp],
    ) -> CoordinationResult:
        effects = list(result.planned_effects)
        if self.config.enforce_negative_space:
            effects = self.enforce_section_negative_space(effects, audio_ctx, layout_props)

        breath_ms = max(0, self.config.anticipation_breath_ms)
        if breath_ms > 0 and audio_ctx.sections:
            boundaries = [
                sec.start_ms
                for sec in audio_ctx.sections
                if _normalize_section_name(sec.name) in _HIGH_IMPACT_SECTIONS and sec.start_ms > 0
            ]
            if boundaries:
                carved: list[PlannedEffect] = []
                for eff in effects:
                    new_end = eff.end_ms
                    if eff.role in ("base", "texture"):
                        for boundary_ms in boundaries:
                            if eff.start_ms < boundary_ms and (boundary_ms - breath_ms) < new_end <= boundary_ms:
                                new_end = max(eff.start_ms, boundary_ms - breath_ms)
                    if new_end > eff.start_ms:
                        carved.append(replace(eff, end_ms=new_end) if new_end != eff.end_ms else eff)
                effects = carved

        prop_map = {p.prop_id: p for p in layout_props}
        palette = DEFAULT_PALETTES.get(self.config.palette_name, DEFAULT_PALETTES["winter_aurora"])
        bpm = audio_ctx.bpm if audio_ctx.bpm and audio_ctx.bpm > 0 else 120.0
        bpm_scale = round(max(0.25, min(4.0, bpm / 120.0)), 3)

        mastered: list[PlannedEffect] = []
        for eff in effects:
            params = dict(eff.params)
            prop = prop_map.get(eff.prop_id)

            if self.config.lock_palette and not _is_character_effect(eff, prop):
                colors = palette.colors_for_section(eff.section_name)
                params["palette_name"] = self.config.palette_name
                params["primary_color"] = colors[0]
                params["secondary_color"] = colors[1]
                params["accent_color"] = colors[2]
                params["neutral_color"] = colors[3]
                params["colors"] = [colors[0], colors[1], colors[2]]

            if self.config.bpm_sync_speed:
                params["bpm_speed_scale"] = bpm_scale

            if self.config.default_fade_ms > 0:
                duration_ms = max(0, eff.end_ms - eff.start_ms)
                fade_ms = min(self.config.default_fade_ms, duration_ms // 2)
                params.setdefault("fade_in_ms", fade_ms)
                params.setdefault("fade_out_ms", fade_ms)

            mastered.append(replace(eff, params=params))

        return CoordinationResult(
            planned_effects=tuple(mastered),
            report=result.report,
            errors=dict(result.errors),
        )
