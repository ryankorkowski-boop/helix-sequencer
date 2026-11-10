from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.choreography_intent import (
    ChoreographyIntent,
    ContrastStrategy,
    DominanceStrategy,
    MotionVocabulary,
    PaletteFamily,
)
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class OrchestrationPersonality:
    name: str
    pacing_style: str
    density_bias: float
    restraint_bias: float
    motion_signature: tuple[MotionVocabulary, ...]
    palette_bias: PaletteFamily
    dominance_strategy: DominanceStrategy
    contrast_strategy: ContrastStrategy
    cinematic_focus: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pacing_style": self.pacing_style,
            "density_bias": self.density_bias,
            "restraint_bias": self.restraint_bias,
            "motion_signature": [motion.value for motion in self.motion_signature],
            "palette_bias": self.palette_bias.value,
            "dominance_strategy": self.dominance_strategy.value,
            "contrast_strategy": self.contrast_strategy.value,
            "cinematic_focus": self.cinematic_focus,
        }


class StyleGovernedOrchestrationPersonalities:
    """Applies distinct directorial personalities to Helix orchestration."""

    PERSONALITIES = {
        "cinematic_helix": OrchestrationPersonality(
            name="Cinematic Helix",
            pacing_style="slow_build_massive_payoff",
            density_bias=0.82,
            restraint_bias=0.72,
            motion_signature=(
                MotionVocabulary.ORBITAL,
                MotionVocabulary.BLOOM,
                MotionVocabulary.HELIX_SPIRAL,
            ),
            palette_bias=PaletteFamily.SPATIAL_HELIX,
            dominance_strategy=DominanceStrategy.SINGLE_HERO,
            contrast_strategy=ContrastStrategy.DARK_PRE_DROP,
            cinematic_focus="emotional_storytelling",
        ),
        "aggressive_concert": OrchestrationPersonality(
            name="Aggressive Concert",
            pacing_style="constant_forward_pressure",
            density_bias=0.95,
            restraint_bias=0.18,
            motion_signature=(
                MotionVocabulary.IMPACT,
                MotionVocabulary.SWEEP,
                MotionVocabulary.CHASE,
            ),
            palette_bias=PaletteFamily.ENERGETIC_CONTRAST,
            dominance_strategy=DominanceStrategy.DISTRIBUTED,
            contrast_strategy=ContrastStrategy.ESCALATING_CHORUS,
            cinematic_focus="audience_hype",
        ),
        "elegant_orchestral": OrchestrationPersonality(
            name="Elegant Orchestral",
            pacing_style="measured_crescendo",
            density_bias=0.58,
            restraint_bias=0.88,
            motion_signature=(
                MotionVocabulary.TEXTURE,
                MotionVocabulary.BLOOM,
                MotionVocabulary.SWEEP,
            ),
            palette_bias=PaletteFamily.WARM_CLASSIC,
            dominance_strategy=DominanceStrategy.BACKGROUND_ONLY,
            contrast_strategy=ContrastStrategy.SPARSE_VERSE,
            cinematic_focus="compositional_balance",
        ),
        "experimental_spatial": OrchestrationPersonality(
            name="Experimental Spatial",
            pacing_style="unpredictable_spatial_tension",
            density_bias=0.76,
            restraint_bias=0.52,
            motion_signature=(
                MotionVocabulary.ORBITAL,
                MotionVocabulary.CASCADE,
                MotionVocabulary.HELIX_SPIRAL,
            ),
            palette_bias=PaletteFamily.SPATIAL_HELIX,
            dominance_strategy=DominanceStrategy.ORBITAL,
            contrast_strategy=ContrastStrategy.DARK_PRE_DROP,
            cinematic_focus="dimensional_motion",
        ),
        "minimalist_emotional": OrchestrationPersonality(
            name="Minimalist Emotional",
            pacing_style="silence_then_release",
            density_bias=0.38,
            restraint_bias=0.96,
            motion_signature=(
                MotionVocabulary.PULSE,
                MotionVocabulary.TEXTURE,
            ),
            palette_bias=PaletteFamily.SOFT_EMOTIONAL,
            dominance_strategy=DominanceStrategy.SINGLE_HERO,
            contrast_strategy=ContrastStrategy.SPARSE_VERSE,
            cinematic_focus="negative_space",
        ),
    }

    def __init__(self, personality: str = "cinematic_helix"):
        self.personality = self.PERSONALITIES[personality]

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()

        for intent in graph:
            output.add_intent(self._apply_personality(intent))

        return output

    def _apply_personality(self, intent: ChoreographyIntent) -> ChoreographyIntent:
        vocabulary = list(intent.motion_vocabulary)

        for motion in self.personality.motion_signature:
            if motion not in vocabulary:
                vocabulary.append(motion)

        density = max(
            0.05,
            min(1.0, intent.density_budget * self.personality.density_bias),
        )

        restraint_modifier = 1.0 - self.personality.restraint_bias * 0.2

        return intent.__class__(
            **{
                **intent.__dict__,
                "motion_vocabulary": tuple(dict.fromkeys(vocabulary)),
                "palette_family": self.personality.palette_bias,
                "dominance_strategy": self.personality.dominance_strategy,
                "contrast_strategy": self.personality.contrast_strategy,
                "density_budget": round(density, 4),
                "intensity": round(min(1.0, intent.intensity * restraint_modifier + 0.08), 4),
                "metadata": {
                    **dict(intent.metadata),
                    "orchestration_personality": self.personality.to_dict(),
                },
            }
        )
