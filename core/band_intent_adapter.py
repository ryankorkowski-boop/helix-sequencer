from __future__ import annotations

from dataclasses import dataclass

from core.choreography_intent import IntentLayerRole, MotionVocabulary
from core.intent_layer_expander import SequentialLayerEvent
from models.helixville4_performer_runtime import HELIXVILLE4_PERFORMERS


@dataclass(frozen=True)
class BandExecutionEvent:
    intent_id: str
    intent_source: str
    performer: str
    performer_state: str
    motion: MotionVocabulary
    layer_role: IntentLayerRole
    start: float
    duration: float
    intensity: float
    stage_region: str
    instrument_emphasis: str


class BandIntentAdapter:
    """Execution-only band choreography adapter.

    Converts canonical sequential events into performer execution states.
    This adapter intentionally does not author emotional choreography.
    """

    MOTION_TO_STATE = {
        MotionVocabulary.PULSE: "synchronized_bounce",
        MotionVocabulary.SWEEP: "cross_stage_motion",
        MotionVocabulary.ORBITAL: "rotating_focus",
        MotionVocabulary.BLOOM: "ensemble_expansion",
        MotionVocabulary.IMPACT: "accent_hit_pose",
        MotionVocabulary.CHASE: "staggered_activation",
        MotionVocabulary.HELIX_SPIRAL: "spiral_group_motion",
        MotionVocabulary.CASCADE: "descending_wave",
        MotionVocabulary.SHIMMER: "ambient_sway",
        MotionVocabulary.TEXTURE: "idle_texture",
        MotionVocabulary.BLACKOUT: "blackout_hold",
    }

    ROLE_TO_EMPHASIS = {
        IntentLayerRole.BASE: "ensemble_foundation",
        IntentLayerRole.SUSTAIN: "held_pose",
        IntentLayerRole.MOTION: "movement_focus",
        IntentLayerRole.EVENT: "timed_hit",
        IntentLayerRole.ACCENT: "lead_accent",
    }

    DEFAULT_PERFORMERS = tuple(performer.performer_id for performer in HELIXVILLE4_PERFORMERS)

    def __init__(self, performers: tuple[str, ...] | None = None):
        self.performers = performers or self.DEFAULT_PERFORMERS

    def adapt_event(
        self,
        event: SequentialLayerEvent,
    ) -> tuple[BandExecutionEvent, ...]:
        performer_state = self.MOTION_TO_STATE.get(event.motion, "idle_texture")

        events = []

        for performer in self.performers:
            events.append(
                BandExecutionEvent(
                    intent_id=event.intent_id,
                    intent_source=event.intent_source,
                    performer=performer,
                    performer_state=performer_state,
                    motion=event.motion,
                    layer_role=event.layer_role,
                    start=event.start,
                    duration=event.duration,
                    intensity=event.intensity,
                    stage_region=event.target_region,
                    instrument_emphasis=self._instrument_emphasis(
                        performer,
                        event.layer_role,
                    ),
                )
            )

        return tuple(events)

    def adapt_many(
        self,
        events: tuple[SequentialLayerEvent, ...],
    ) -> tuple[BandExecutionEvent, ...]:
        output = []

        for event in events:
            output.extend(self.adapt_event(event))

        return tuple(output)

    def _instrument_emphasis(
        self,
        performer: str,
        role: IntentLayerRole,
    ) -> str:
        if performer == "drummer":
            if role == IntentLayerRole.EVENT:
                return "percussion_hit_focus"
            return "rhythmic_foundation"

        if performer == "guitarist":
            if role == IntentLayerRole.MOTION:
                return "riff_motion_focus"
            return "harmonic_drive"

        if performer == "bassist":
            return "low_end_support"

        if performer == "singer":
            if role == IntentLayerRole.ACCENT:
                return "lead_vocal_focus"
            return "front_stage_presence"

        if performer == "female_singer":
            if role == IntentLayerRole.ACCENT:
                return "harmony_vocal_accent"
            return "harmony_call_response"

        return "ensemble_support"
