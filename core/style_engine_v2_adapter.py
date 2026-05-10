from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.choreography_intent import (
    ChoreographyIntent,
    ChoreographyTarget,
    ContrastStrategy,
    DominanceStrategy,
    IntentLayerRole,
    MotionVocabulary,
    PaletteFamily,
)


DEFAULT_MOTION_MAP: dict[str, tuple[MotionVocabulary, ...]] = {
    "beat_pulse": (MotionVocabulary.PULSE,),
    "tight_chase": (MotionVocabulary.CHASE,),
    "cinematic_sweep": (MotionVocabulary.SWEEP,),
    "helix_spiral_sweep": (
        MotionVocabulary.ORBITAL,
        MotionVocabulary.HELIX_SPIRAL,
    ),
    "gold_white_sparkle": (MotionVocabulary.SHIMMER,),
    "trailer_hit_burst": (
        MotionVocabulary.IMPACT,
        MotionVocabulary.BLOOM,
    ),
    "party_strobe_burst": (
        MotionVocabulary.IMPACT,
        MotionVocabulary.PULSE,
    ),
    "depth_orbit_texture": (
        MotionVocabulary.ORBITAL,
        MotionVocabulary.TEXTURE,
    ),
    "blackout": (MotionVocabulary.BLACKOUT,),
}


STYLE_PALETTE_MAP: dict[str, PaletteFamily] = {
    "BeatDrive": PaletteFamily.PARTY_NEON,
    "ClassicChristmas": PaletteFamily.CLASSIC_CHRISTMAS,
    "CinematicSweep": PaletteFamily.CINEMATIC_BLUE_GOLD,
    "PartyMode": PaletteFamily.PARTY_NEON,
    "SpatialHelix": PaletteFamily.SPATIAL_HELIX,
}


STYLE_DOMINANCE_MAP: dict[str, DominanceStrategy] = {
    "BeatDrive": DominanceStrategy.DISTRIBUTED,
    "ClassicChristmas": DominanceStrategy.SINGLE_HERO,
    "CinematicSweep": DominanceStrategy.SINGLE_HERO,
    "PartyMode": DominanceStrategy.DISTRIBUTED,
    "SpatialHelix": DominanceStrategy.ORBITAL,
}


STYLE_CONTRAST_MAP: dict[str, ContrastStrategy] = {
    "BeatDrive": ContrastStrategy.ESCALATING_CHORUS,
    "ClassicChristmas": ContrastStrategy.WARM_COOL_ALTERNATION,
    "CinematicSweep": ContrastStrategy.DARK_PRE_DROP,
    "PartyMode": ContrastStrategy.DENSE_SPARSE_ALTERNATION,
    "SpatialHelix": ContrastStrategy.DARK_PRE_DROP,
}


SECTION_ENERGY_MAP: dict[str, float] = {
    "intro": 0.25,
    "verse": 0.45,
    "bridge": 0.65,
    "chorus": 0.82,
    "finale": 1.0,
}


EVENT_INTENSITY_MAP: dict[str, float] = {
    "silence": 0.05,
    "texture": 0.22,
    "beat": 0.55,
    "build": 0.75,
    "hit": 0.92,
    "drop": 1.0,
}


TARGET_ROLE_MAP: dict[str, tuple[ChoreographyTarget, ...]] = {
    "whole_house": (ChoreographyTarget.ALL,),
    "band": (ChoreographyTarget.PERFORMER,),
    "matrix": (ChoreographyTarget.MATRIX,),
    "megatree": (ChoreographyTarget.CENTERPIECE,),
    "sequential": (ChoreographyTarget.SEQUENTIAL,),
}


class StyleDecisionAdapter:
    """Bridge existing StyleDecision structures into canonical intent.

    This layer preserves the existing Style Engine contract while promoting
    decisions into the canonical orchestration ontology.
    """

    @staticmethod
    def to_choreography_intent(decision: Mapping[str, Any]) -> ChoreographyIntent:
        style = str(decision.get("style", "unknown"))
        section = str(decision.get("section", "unknown"))
        event_type = str(decision.get("event_type", decision.get("event", "texture")))
        effect = str(decision.get("effect", "texture"))
        target = str(decision.get("targets", "whole_house"))

        energy = SECTION_ENERGY_MAP.get(section, 0.5)
        intensity = EVENT_INTENSITY_MAP.get(event_type, 0.5)

        if event_type in {"drop", "hit"}:
            escalation_phase = 3
        elif event_type == "build":
            escalation_phase = 2
        elif event_type == "beat":
            escalation_phase = 1
        else:
            escalation_phase = 0

        return ChoreographyIntent(
            start=float(decision.get("start", 0.0)),
            duration=float(decision.get("duration", 1.0)),
            section=section,
            event_type=event_type,
            style=style,
            emotional_energy=energy,
            intensity=intensity,
            focal_region=str(decision.get("focal_region", "center_stage")),
            support_regions=tuple(decision.get("support_regions", ())),
            target_families=TARGET_ROLE_MAP.get(
                target,
                (ChoreographyTarget.ALL,),
            ),
            dominant_prop=decision.get("dominant_prop"),
            dominance_strategy=STYLE_DOMINANCE_MAP.get(
                style,
                DominanceStrategy.DISTRIBUTED,
            ),
            motion_vocabulary=DEFAULT_MOTION_MAP.get(
                effect,
                (MotionVocabulary.TEXTURE,),
            ),
            contrast_strategy=STYLE_CONTRAST_MAP.get(
                style,
                ContrastStrategy.NONE,
            ),
            escalation_phase=escalation_phase,
            palette_family=STYLE_PALETTE_MAP.get(
                style,
                PaletteFamily.DEFAULT,
            ),
            density_budget=float(decision.get("density_budget", 0.5)),
            layer_roles=(
                IntentLayerRole.BASE,
                IntentLayerRole.MOTION,
            ),
            source="style_engine_v1_adapter",
            metadata={
                "original_effect": effect,
                "original_target": target,
                "adapter": "StyleDecisionAdapter",
            },
        )
