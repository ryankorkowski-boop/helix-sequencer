from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.choreography_intent import (
    ChoreographyIntent,
    IntentLayerRole,
    MotionVocabulary,
)


@dataclass(frozen=True)
class SequentialLayerEvent:
    intent_id: str
    intent_source: str
    start: float
    duration: float
    layer_role: IntentLayerRole
    motion: MotionVocabulary
    spatial_mode: str
    intensity: float
    target_region: str


class IntentLayerExpander:
    """Execution-only expansion layer.

    Converts canonical choreography intent into deterministic sequential
    execution events. This layer intentionally does NOT decide:

    - emotional tone
    - palette philosophy
    - contrast strategy
    - escalation behavior
    - dominance strategy

    Those decisions belong to StyleEngineV2.
    """

    MOTION_TO_SPATIAL_MODE = {
        MotionVocabulary.CHASE: "linear_traversal",
        MotionVocabulary.SWEEP: "sweep_arc",
        MotionVocabulary.ORBITAL: "orbital_rotation",
        MotionVocabulary.HELIX_SPIRAL: "helix_spiral",
        MotionVocabulary.BLOOM: "radial_bloom",
        MotionVocabulary.CASCADE: "cascade_drop",
        MotionVocabulary.PULSE: "pulse_expand",
        MotionVocabulary.IMPACT: "impact_flash",
        MotionVocabulary.SHIMMER: "texture_shimmer",
        MotionVocabulary.TEXTURE: "static_texture",
        MotionVocabulary.BLACKOUT: "blackout",
    }

    def expand_intent(
        self,
        intent: ChoreographyIntent,
    ) -> tuple[SequentialLayerEvent, ...]:
        events: list[SequentialLayerEvent] = []

        for role in intent.layer_roles:
            for motion in intent.motion_vocabulary:
                spatial_mode = self.MOTION_TO_SPATIAL_MODE.get(
                    motion,
                    "static_texture",
                )

                role_intensity = self._role_intensity_multiplier(role)

                events.append(
                    SequentialLayerEvent(
                        intent_id=intent.intent_id,
                        intent_source=intent.source,
                        start=intent.start,
                        duration=intent.duration,
                        layer_role=role,
                        motion=motion,
                        spatial_mode=spatial_mode,
                        intensity=round(intent.intensity * role_intensity, 4),
                        target_region=intent.focal_region,
                    )
                )

        return tuple(events)

    def expand_many(
        self,
        intents: Iterable[ChoreographyIntent],
    ) -> tuple[SequentialLayerEvent, ...]:
        output: list[SequentialLayerEvent] = []

        for intent in intents:
            output.extend(self.expand_intent(intent))

        return tuple(sorted(output, key=lambda event: (event.start, event.intent_id)))

    @staticmethod
    def _role_intensity_multiplier(role: IntentLayerRole) -> float:
        if role == IntentLayerRole.ACCENT:
            return 1.0
        if role == IntentLayerRole.MOTION:
            return 0.85
        if role == IntentLayerRole.EVENT:
            return 0.92
        if role == IntentLayerRole.SUSTAIN:
            return 0.65
        return 0.75
