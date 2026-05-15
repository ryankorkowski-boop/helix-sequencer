from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from math import cos, sin
from typing import Any, Iterable, Sequence

from core.birdsong_generative import (
    BIRDSONG_MOTIFS,
    DEFAULT_EFFECTS,
    BehaviorEngine,
    EffectCandidate,
    EffectScoringEngine,
    EnergyWave,
    FeatureState,
    Phrase,
    PhraseEngine,
    RenderEvent,
    SpatialMap,
    SpatialModel,
    clamp,
    distance,
)


INTENTS = ("BUILD", "RELEASE", "GROOVE", "BREAK", "FINALE")
LAYERS = ("AMBIENT", "RHYTHMIC", "ACCENT")


@dataclass(frozen=True)
class IntentSnapshot:
    time_s: float
    intent: str
    energy_smooth: float
    onset: float
    reason: str


class IntentEngine:
    """High-level choreography intent layer above PhraseEngine.

    This remains deterministic and conservative: intent changes only when clear
    energy/onset evidence exists, which keeps the sequence from feeling random.
    """

    def __init__(self, default_intent: str = "GROOVE") -> None:
        if default_intent not in INTENTS:
            raise ValueError(f"Unknown intent: {default_intent}")
        self.current_intent = default_intent
        self.history: deque[IntentSnapshot] = deque(maxlen=128)

    def update(self, time_s: float, feature_state: FeatureState) -> str:
        previous = self.current_intent
        reason = "steady"

        energy = feature_state.energy_smooth
        onset = feature_state.onset
        trend = feature_state.trend("energy_smooth", 24)

        if energy >= 0.92 and onset >= 0.70:
            self.current_intent = "FINALE"
            reason = "very_high_energy_with_transient"
        elif trend >= 0.18 or energy >= 0.78:
            self.current_intent = "BUILD"
            reason = "rising_or_high_energy"
        elif onset >= 0.90 and previous in {"BUILD", "FINALE"}:
            self.current_intent = "RELEASE"
            reason = "strong_onset_after_build"
        elif energy <= 0.28 and onset <= 0.45:
            self.current_intent = "BREAK"
            reason = "low_energy_sparse"
        else:
            self.current_intent = "GROOVE"
            reason = "stable_mid_energy"

        self.history.append(
            IntentSnapshot(
                time_s=float(time_s),
                intent=self.current_intent,
                energy_smooth=float(energy),
                onset=float(onset),
                reason=reason,
            )
        )
        return self.current_intent


class IntentAwarePhraseEngine(PhraseEngine):
    """Phrase engine conditioned by cognitive intent."""

    INTENT_MOTIFS = {
        "BUILD": ("wave_sweep", "spiral"),
        "RELEASE": ("pulse_cascade", "sparkle_field"),
        "GROOVE": ("orbit", "wave_sweep"),
        "BREAK": ("sparkle_field",),
        "FINALE": ("spiral", "pulse_cascade", "wave_sweep"),
    }

    def update_with_intent(self, time_s: float, feature_state: FeatureState, intent: str) -> Phrase:
        phrase = super().update(time_s, feature_state)
        allowed = self.INTENT_MOTIFS.get(intent, BIRDSONG_MOTIFS)
        if phrase.motif in allowed:
            return phrase
        replacement = allowed[self._motif_index % len(allowed)]
        self.current_phrase = Phrase(
            start_time=phrase.start_time,
            duration=phrase.duration,
            motif=replacement,
            direction=phrase.direction,
        )
        return self.current_phrase


@dataclass(frozen=True)
class EnergySource:
    position: tuple[float, float, float]
    amplitude: float
    radius: float
    start_time: float
    decay: float = 0.88
    frequency: float = 1.0

    def influence(self, position: tuple[float, float, float], time_s: float) -> float:
        age = max(0.0, float(time_s) - self.start_time)
        dist = distance(self.position, position)
        spatial = max(0.0, 1.0 - (dist / max(0.001, self.radius)))
        temporal = self.decay ** (age * 4.0)
        oscillation = 0.75 + (0.25 * cos(age * self.frequency))
        return clamp(self.amplitude * spatial * temporal * oscillation)


class EnergyField:
    """Continuous overlapping field replacing direct one-shot triggering."""

    def __init__(self) -> None:
        self.sources: list[EnergySource] = []

    def add_source(self, source: EnergySource) -> None:
        self.sources.append(source)

    def prune(self, time_s: float) -> None:
        self.sources = [src for src in self.sources if src.influence(src.position, time_s) >= 0.03]

    def sample(self, position: tuple[float, float, float], time_s: float) -> float:
        return clamp(sum(src.influence(position, time_s) for src in self.sources))

    def spawn_from_state(self, time_s: float, feature_state: FeatureState, spatial_map: SpatialMap) -> None:
        if feature_state.onset < 0.50 and feature_state.energy_smooth < 0.65:
            return
        anchor = spatial_map.feature_anchor(feature_state)
        radius = 0.45 + (feature_state.energy_smooth * 0.55)
        frequency = 1.0 + (feature_state.centroid * 2.0)
        self.add_source(
            EnergySource(
                position=anchor,
                amplitude=max(feature_state.onset, feature_state.energy_smooth),
                radius=radius,
                start_time=float(time_s),
                decay=0.90,
                frequency=frequency,
            )
        )


@dataclass(frozen=True)
class MotifInstance:
    base_name: str
    speed: float
    spread: float
    curvature: float
    intent: str


class MotifEvolutionEngine:
    """Deterministic motif mutation with a no-repetition ceiling.

    It mutates parameters, not the motif list. Base motifs remain capped at five.
    """

    def __init__(self) -> None:
        self.history: deque[str] = deque(maxlen=16)

    def evolve(self, motif_name: str, intent: str, feature_state: FeatureState) -> MotifInstance:
        recent_count = sum(1 for item in self.history if item == motif_name)
        energy = feature_state.energy_smooth
        centroid = feature_state.centroid
        speed = 0.85 + (energy * 0.55) - (recent_count * 0.03)
        spread = 0.45 + (feature_state.high * 0.30) + (feature_state.mid * 0.15)
        curvature = 0.10 + (centroid * 0.35)
        if intent == "BREAK":
            speed *= 0.65
            spread *= 0.70
        elif intent == "FINALE":
            speed *= 1.20
            spread *= 1.15
        self.history.append(motif_name)
        return MotifInstance(
            base_name=motif_name,
            speed=round(max(0.25, speed), 4),
            spread=round(clamp(spread, 0.15, 1.0), 4),
            curvature=round(clamp(curvature, 0.0, 0.75), 4),
            intent=intent,
        )


@dataclass(frozen=True)
class FlowVector:
    dx: float
    dy: float
    dz: float


class SpatialFlowField:
    """Curved spatial flow used by waves and layer sampling."""

    def sample(self, position: tuple[float, float, float], motif: MotifInstance) -> FlowVector:
        x, y, z = position
        if motif.base_name == "spiral":
            return FlowVector(dx=-y * motif.curvature + 0.18, dy=x * motif.curvature, dz=0.22 * motif.speed)
        if motif.base_name == "orbit":
            return FlowVector(dx=-y * 0.25, dy=x * 0.25, dz=0.03)
        if motif.base_name == "sparkle_field":
            return FlowVector(dx=0.05 * sin(x + z), dy=0.02, dz=0.18 * motif.spread)
        if motif.base_name == "pulse_cascade":
            return FlowVector(dx=0.26 * motif.speed, dy=0.0, dz=-0.04)
        return FlowVector(dx=0.34 * motif.speed, dy=0.05 * motif.curvature, dz=0.04)


@dataclass(frozen=True)
class LayerContext:
    layer: str
    band_energy: float
    intensity_scale: float
    preferred_spatial_role: str


class MultiLayerRenderer:
    """Produces ambient, rhythmic, and accent contexts from feature bands."""

    def contexts(self, feature_state: FeatureState, intent: str) -> tuple[LayerContext, LayerContext, LayerContext]:
        ambient_scale = 0.45 if intent != "BREAK" else 0.28
        rhythmic_scale = 0.70 if intent not in {"BREAK"} else 0.38
        accent_scale = 1.00 if intent in {"BUILD", "RELEASE", "FINALE"} else 0.72
        return (
            LayerContext("AMBIENT", feature_state.low, ambient_scale, "ground"),
            LayerContext("RHYTHMIC", feature_state.mid, rhythmic_scale, "horizontal"),
            LayerContext("ACCENT", max(feature_state.high, feature_state.onset), accent_scale, "vertical"),
        )


class ChoreographyMemory:
    def __init__(self) -> None:
        self.effects: deque[str] = deque(maxlen=48)
        self.regions: deque[str] = deque(maxlen=48)
        self.motifs: deque[str] = deque(maxlen=24)
        self.intensity_trend: deque[float] = deque(maxlen=64)

    def remember(self, *, effect: str, region: str, motif: str, intensity: float) -> None:
        self.effects.append(effect)
        self.regions.append(region)
        self.motifs.append(motif)
        self.intensity_trend.append(float(intensity))

    def effect_penalty(self, effect: str) -> float:
        return 0.60 if effect in self.effects else 1.0

    def region_penalty(self, region: str) -> float:
        return 0.72 if region in self.regions else 1.0


class MemoryAwareEffectScoringEngine(EffectScoringEngine):
    def __init__(self, memory: ChoreographyMemory) -> None:
        super().__init__()
        self.memory = memory

    def score(self, effect: EffectCandidate, model: SpatialModel, wave: EnergyWave, preferred: set[str]) -> float:
        base = super().score(effect, model, wave, preferred)
        return base * self.memory.effect_penalty(effect.name) * self.memory.region_penalty(model.category)


@dataclass(frozen=True)
class CognitiveRenderEvent(RenderEvent):
    intent: str = "GROOVE"
    layer: str = "RHYTHMIC"
    field_value: float = 0.0


class CognitiveBehaviorEngine:
    """Intent + field + memory orchestrator.

    This does not replace the legacy engine. It is an isolated v2 path for A-/A
    quality experiments.
    """

    def __init__(self, spatial_map: SpatialMap) -> None:
        self.spatial_map = spatial_map
        self.energy_field = EnergyField()
        self.memory = ChoreographyMemory()
        self.scorer = MemoryAwareEffectScoringEngine(self.memory)
        self.flow = SpatialFlowField()
        self.layer_renderer = MultiLayerRenderer()
        self._last_time_s: float | None = None

    def update(
        self,
        time_s: float,
        feature_state: FeatureState,
        phrase: Phrase,
        intent: str,
        motif: MotifInstance,
    ) -> list[CognitiveRenderEvent]:
        self.energy_field.spawn_from_state(time_s, feature_state, self.spatial_map)
        self.energy_field.prune(time_s)
        contexts = self.layer_renderer.contexts(feature_state, intent)
        events: list[CognitiveRenderEvent] = []

        for model in self.spatial_map.models:
            position = (model.x, model.y, model.z)
            field_value = self.energy_field.sample(position, time_s)
            if field_value < 0.08:
                continue
            flow = self.flow.sample(position, motif)
            synthetic_wave = EnergyWave(
                position=position,
                velocity=(flow.dx, flow.dy, flow.dz),
                energy=field_value,
                radius=0.28 + motif.spread * 0.25,
            )
            for layer in contexts:
                if layer.band_energy * layer.intensity_scale < 0.05:
                    continue
                effect = self.scorer.select(model, synthetic_wave, phrase, DEFAULT_EFFECTS)
                intensity = clamp(field_value * layer.band_energy * layer.intensity_scale)
                start_ms = int(round(time_s * 1000.0))
                duration_ms = int(round(120 + (260 * intensity)))
                event = CognitiveRenderEvent(
                    model=model.name,
                    start_ms=start_ms,
                    end_ms=start_ms + duration_ms,
                    effect=effect.name,
                    motif=motif.base_name,
                    intensity=intensity,
                    intent=intent,
                    layer=layer.layer,
                    field_value=round(field_value, 4),
                )
                events.append(event)
                self.memory.remember(effect=effect.name, region=model.category, motif=motif.base_name, intensity=intensity)
        return events


@dataclass(frozen=True)
class BirdsongQualityScore:
    musicality: float
    spatial_coherence: float
    layering: float
    novelty: float
    emotion: float

    @property
    def overall(self) -> float:
        return round(
            (self.musicality * 0.30)
            + (self.spatial_coherence * 0.25)
            + (self.layering * 0.20)
            + (self.novelty * 0.15)
            + (self.emotion * 0.10),
            4,
        )

    @property
    def weakest_category(self) -> str:
        values = {
            "musicality": self.musicality,
            "spatial_coherence": self.spatial_coherence,
            "layering": self.layering,
            "novelty": self.novelty,
            "emotion": self.emotion,
        }
        return min(values, key=values.get)


def score_birdsong_events(events: Sequence[CognitiveRenderEvent]) -> BirdsongQualityScore:
    if not events:
        return BirdsongQualityScore(0.0, 0.0, 0.0, 0.0, 0.0)
    motifs = {event.motif for event in events}
    models = {event.model for event in events}
    layers = {event.layer for event in events}
    effects = {event.effect for event in events}
    ordered = sorted(events, key=lambda event: (event.start_ms, event.model, event.layer))
    continuity_hits = sum(1 for a, b in zip(ordered, ordered[1:]) if abs(b.start_ms - a.start_ms) <= 450)
    continuity = continuity_hits / max(1, len(ordered) - 1)
    musicality = clamp(0.55 + continuity * 0.45)
    spatial_coherence = clamp(0.45 + min(0.35, len(models) / 20.0) + min(0.20, len(motifs) / 25.0))
    layering = clamp(len(layers) / 3.0)
    novelty = clamp(0.50 + min(0.30, len(effects) / 20.0) + min(0.20, len(motifs) / 10.0))
    avg_intensity = sum(event.intensity for event in events) / len(events)
    emotion = clamp(0.45 + avg_intensity * 0.55)
    return BirdsongQualityScore(
        musicality=round(musicality, 4),
        spatial_coherence=round(spatial_coherence, 4),
        layering=round(layering, 4),
        novelty=round(novelty, 4),
        emotion=round(emotion, 4),
    )


@dataclass
class CognitiveBirdsongPipeline:
    spatial_map: SpatialMap
    feature_state: FeatureState = field(default_factory=FeatureState)
    intent_engine: IntentEngine = field(default_factory=IntentEngine)
    phrase_engine: IntentAwarePhraseEngine = field(default_factory=IntentAwarePhraseEngine)
    motif_engine: MotifEvolutionEngine = field(default_factory=MotifEvolutionEngine)
    behavior_engine: CognitiveBehaviorEngine | None = None

    def __post_init__(self) -> None:
        if self.behavior_engine is None:
            self.behavior_engine = CognitiveBehaviorEngine(self.spatial_map)

    def update(self, features: Any, time_s: float) -> list[CognitiveRenderEvent]:
        self.feature_state.update(features, time_s)
        intent = self.intent_engine.update(time_s, self.feature_state)
        phrase = self.phrase_engine.update_with_intent(time_s, self.feature_state, intent)
        motif = self.motif_engine.evolve(phrase.motif, intent, self.feature_state)
        assert self.behavior_engine is not None
        return self.behavior_engine.update(time_s, self.feature_state, phrase, intent, motif)

    def run(self, frames: Iterable[tuple[float, Any]]) -> tuple[list[CognitiveRenderEvent], BirdsongQualityScore]:
        events: list[CognitiveRenderEvent] = []
        for time_s, features in frames:
            events.extend(self.update(features, time_s))
        return events, score_birdsong_events(events)
