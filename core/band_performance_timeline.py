from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from core.band_intent_adapter import BandExecutionEvent
from core.choreography_intent import IntentLayerRole, MotionVocabulary
from models.helixville4_performer_runtime import HELIXVILLE4_PERFORMERS, PerformerRuntimeSpec


@dataclass(frozen=True)
class BandPerformanceEvent:
    performer: str
    model_name: str
    state: str
    start: float
    duration: float
    intensity: float
    source_intent_id: str
    submodels: tuple[str, ...]
    instrument_emphasis: str
    motion: MotionVocabulary
    layer_role: IntentLayerRole

    @property
    def end(self) -> float:
        return round(self.start + self.duration, 6)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["end"] = self.end
        payload["motion"] = self.motion.value
        payload["layer_role"] = self.layer_role.value
        return payload


class BandPerformanceTimelineCompiler:
    """Compiles adapted band execution events into runtime performer state events.

    This is intentionally deterministic and non-authoring: it maps already-expanded
    choreography intent into the closest approved performer runtime states.
    """

    GENERIC_STATE_ALIASES = {
        "synchronized_bounce": "ready_idle",
        "cross_stage_motion": "sway_groove",
        "rotating_focus": "sway_groove",
        "ensemble_expansion": "big_vocal",
        "accent_hit_pose": "hit_end",
        "staggered_activation": "ready_idle",
        "spiral_group_motion": "sway_groove",
        "descending_wave": "ready_idle",
        "ambient_sway": "sway_groove",
        "idle_texture": "ready_idle",
        "blackout_hold": "ready_idle",
    }

    ROLE_FALLBACKS = {
        "drummer": {
            IntentLayerRole.EVENT: "snare_hit",
            IntentLayerRole.ACCENT: "downbeat_impact",
            IntentLayerRole.MOTION: "tom_fill",
            IntentLayerRole.SUSTAIN: "hi_hat_pulse",
            IntentLayerRole.BASE: "ready_idle",
        },
        "guitarist": {
            IntentLayerRole.EVENT: "strum_down",
            IntentLayerRole.ACCENT: "hit_end",
            IntentLayerRole.MOTION: "neck_slide",
            IntentLayerRole.SUSTAIN: "chord_groove",
            IntentLayerRole.BASE: "ready_idle",
        },
        "bassist": {
            IntentLayerRole.EVENT: "pluck_groove",
            IntentLayerRole.ACCENT: "hit_end",
            IntentLayerRole.MOTION: "neck_slide_up",
            IntentLayerRole.SUSTAIN: "groove_start",
            IntentLayerRole.BASE: "ready_idle",
        },
        "singer": {
            IntentLayerRole.EVENT: "sing_start",
            IntentLayerRole.ACCENT: "emote_high",
            IntentLayerRole.MOTION: "hand_raise",
            IntentLayerRole.SUSTAIN: "hit_hold",
            IntentLayerRole.BASE: "ready_idle",
        },
        "female_singer": {
            IntentLayerRole.EVENT: "sing_start",
            IntentLayerRole.ACCENT: "big_vocal",
            IntentLayerRole.MOTION: "point_out",
            IntentLayerRole.SUSTAIN: "hit_hold",
            IntentLayerRole.BASE: "ready_idle",
        },
    }

    def __init__(self, performers: Iterable[PerformerRuntimeSpec] = HELIXVILLE4_PERFORMERS):
        self.performers = {performer.performer_id: performer for performer in performers}

    def compile_event(self, event: BandExecutionEvent) -> BandPerformanceEvent:
        performer = self.performers[event.performer]
        state_name = self._resolve_state(event, performer)
        state = self._state_by_name(performer, state_name)

        return BandPerformanceEvent(
            performer=performer.performer_id,
            model_name=performer.model_name,
            state=state.name,
            start=event.start,
            duration=event.duration,
            intensity=round(event.intensity * state.intensity, 4),
            source_intent_id=event.intent_id,
            submodels=state.primary_submodels,
            instrument_emphasis=event.instrument_emphasis,
            motion=event.motion,
            layer_role=event.layer_role,
        )

    def compile_many(self, events: Iterable[BandExecutionEvent]) -> tuple[BandPerformanceEvent, ...]:
        compiled = [self.compile_event(event) for event in events]
        return tuple(sorted(compiled, key=lambda item: (item.start, item.performer, item.state)))

    def build_manifest(self, events: Iterable[BandExecutionEvent]) -> dict[str, Any]:
        timeline = self.compile_many(events)
        return {
            "schema": "helixville4.band_performance_timeline.v1",
            "event_count": len(timeline),
            "performers": sorted({event.performer for event in timeline}),
            "models": sorted({event.model_name for event in timeline}),
            "timeline": [event.to_dict() for event in timeline],
        }

    def _resolve_state(self, event: BandExecutionEvent, performer: PerformerRuntimeSpec) -> str:
        available = {state.name for state in performer.states}
        candidate = event.performer_state
        if candidate in available:
            return candidate

        alias = self.GENERIC_STATE_ALIASES.get(candidate)
        if alias in available:
            return alias

        fallback = self.ROLE_FALLBACKS.get(performer.performer_id, {}).get(event.layer_role)
        if fallback in available:
            return fallback

        return performer.states[0].name

    @staticmethod
    def _state_by_name(performer: PerformerRuntimeSpec, state_name: str):
        for state in performer.states:
            if state.name == state_name:
                return state
        raise KeyError(f"{performer.performer_id} does not define state {state_name!r}")
