from __future__ import annotations

from dataclasses import dataclass

from core.choreography_intent import IntentLayerRole, MotionVocabulary
from core.intent_layer_expander import SequentialLayerEvent


@dataclass(frozen=True)
class FloorPianoExecutionEvent:
    intent_id: str
    intent_source: str
    start: float
    duration: float
    motion: MotionVocabulary
    layer_role: IntentLayerRole
    traversal_mode: str
    key_range: tuple[int, int]
    octave_span: tuple[int, int]
    chord_shape: str
    sustain: float
    velocity: float
    target_region: str


class FloorPianoIntentAdapter:
    """Converts canonical sequential events into floor piano execution events.

    This adapter is intentionally execution-only. It does not choose emotional
    tone, palette, contrast, escalation, dominance, or style identity. Those
    decisions belong to the canonical choreography layer.
    """

    MOTION_TO_TRAVERSAL = {
        MotionVocabulary.HELIX_SPIRAL: "spiral_chord_traversal",
        MotionVocabulary.SWEEP: "directional_key_sweep",
        MotionVocabulary.BLOOM: "outward_chord_bloom",
        MotionVocabulary.IMPACT: "cluster_accent_flash",
        MotionVocabulary.PULSE: "rhythmic_sustain_pulse",
        MotionVocabulary.ORBITAL: "rotating_chord_center",
        MotionVocabulary.CHASE: "sequential_key_step",
        MotionVocabulary.CASCADE: "descending_octave_cascade",
        MotionVocabulary.SHIMMER: "soft_key_texture",
        MotionVocabulary.TEXTURE: "ambient_key_wash",
        MotionVocabulary.BLACKOUT: "key_blackout",
    }

    ROLE_TO_SUSTAIN = {
        IntentLayerRole.BASE: 0.75,
        IntentLayerRole.SUSTAIN: 1.0,
        IntentLayerRole.MOTION: 0.55,
        IntentLayerRole.EVENT: 0.35,
        IntentLayerRole.ACCENT: 0.2,
    }

    def __init__(self, key_count: int = 88, lowest_octave: int = 0, highest_octave: int = 8):
        if key_count <= 0:
            raise ValueError("key_count must be positive")
        self.key_count = key_count
        self.lowest_octave = lowest_octave
        self.highest_octave = highest_octave

    def adapt_event(self, event: SequentialLayerEvent) -> FloorPianoExecutionEvent:
        traversal_mode = self.MOTION_TO_TRAVERSAL.get(event.motion, "ambient_key_wash")
        key_range = self._key_range_for_motion(event.motion)
        octave_span = self._octave_span_for_motion(event.motion)
        chord_shape = self._chord_shape_for_motion(event.motion)
        sustain = round(event.duration * self.ROLE_TO_SUSTAIN.get(event.layer_role, 0.5), 4)

        return FloorPianoExecutionEvent(
            intent_id=event.intent_id,
            intent_source=event.intent_source,
            start=event.start,
            duration=event.duration,
            motion=event.motion,
            layer_role=event.layer_role,
            traversal_mode=traversal_mode,
            key_range=key_range,
            octave_span=octave_span,
            chord_shape=chord_shape,
            sustain=sustain,
            velocity=event.intensity,
            target_region=event.target_region,
        )

    def adapt_many(self, events: tuple[SequentialLayerEvent, ...]) -> tuple[FloorPianoExecutionEvent, ...]:
        return tuple(self.adapt_event(event) for event in events)

    def _key_range_for_motion(self, motion: MotionVocabulary) -> tuple[int, int]:
        if motion in {MotionVocabulary.BLOOM, MotionVocabulary.ORBITAL, MotionVocabulary.HELIX_SPIRAL}:
            return (max(1, self.key_count // 4), min(self.key_count, self.key_count * 3 // 4))
        if motion in {MotionVocabulary.IMPACT, MotionVocabulary.PULSE}:
            center = max(1, self.key_count // 2)
            return (max(1, center - 6), min(self.key_count, center + 6))
        if motion == MotionVocabulary.BLACKOUT:
            return (1, self.key_count)
        return (1, self.key_count)

    def _octave_span_for_motion(self, motion: MotionVocabulary) -> tuple[int, int]:
        if motion in {MotionVocabulary.HELIX_SPIRAL, MotionVocabulary.CASCADE}:
            return (self.lowest_octave, self.highest_octave)
        if motion in {MotionVocabulary.BLOOM, MotionVocabulary.ORBITAL}:
            mid_low = max(self.lowest_octave, 2)
            mid_high = min(self.highest_octave, 6)
            return (mid_low, mid_high)
        if motion in {MotionVocabulary.IMPACT, MotionVocabulary.PULSE}:
            return (max(self.lowest_octave, 3), min(self.highest_octave, 5))
        return (self.lowest_octave, self.highest_octave)

    @staticmethod
    def _chord_shape_for_motion(motion: MotionVocabulary) -> str:
        if motion == MotionVocabulary.HELIX_SPIRAL:
            return "rotating_extended_chord"
        if motion == MotionVocabulary.BLOOM:
            return "center_out_triad_bloom"
        if motion == MotionVocabulary.ORBITAL:
            return "alternating_inversion_orbit"
        if motion == MotionVocabulary.IMPACT:
            return "dense_accent_cluster"
        if motion == MotionVocabulary.PULSE:
            return "repeated_power_chord"
        if motion == MotionVocabulary.CASCADE:
            return "octave_broken_chord"
        return "single_note_or_simple_interval"
