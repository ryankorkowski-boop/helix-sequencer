from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from math import sqrt
from typing import Any, Mapping, Sequence


BIRDSONG_MOTIFS = ("wave_sweep", "spiral", "pulse_cascade", "orbit", "sparkle_field")
SPATIAL_ROLE_ALIASES = {
    "center_ground": "ground",
    "high_vertical": "vertical",
}


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


def _feature_get(features: Any, key: str, default: float = 0.0) -> float:
    if isinstance(features, Mapping):
        value = features.get(key, default)
    else:
        value = getattr(features, key, default)
    try:
        return float(value)
    except Exception:
        return default


def _band(features: Any, index: int, name: str) -> float:
    if isinstance(features, Mapping):
        bands = features.get("bands")
        if isinstance(bands, Sequence) and not isinstance(bands, (str, bytes)) and len(bands) > index:
            return clamp(float(bands[index]))
        return clamp(float(features.get(name, 0.0) or 0.0))
    bands = getattr(features, "bands", None)
    if isinstance(bands, Sequence) and not isinstance(bands, (str, bytes)) and len(bands) > index:
        return clamp(float(bands[index]))
    return clamp(float(getattr(features, name, 0.0) or 0.0))


def _spatial_role(value: str) -> str:
    role = str(value or "generic").strip().lower()
    return SPATIAL_ROLE_ALIASES.get(role, role)


@dataclass
class FeatureSnapshot:
    time_s: float
    energy: float = 0.0
    energy_smooth: float = 0.0
    onset: float = 0.0
    centroid: float = 0.0
    low: float = 0.0
    mid: float = 0.0
    high: float = 0.0
    beat_phase: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "time_s": self.time_s,
            "energy": self.energy,
            "energy_smooth": self.energy_smooth,
            "onset": self.onset,
            "centroid": self.centroid,
            "low": self.low,
            "mid": self.mid,
            "high": self.high,
            "beat_phase": self.beat_phase,
        }


class FeatureState:
    """Stateful wrapper for audio_pipeline-style feature frames.

    The object intentionally exposes scalar attributes and a dict snapshot so
    older rule-based code can continue to consume plain feature values while the
    generative pipeline gets temporal memory.
    """

    def __init__(self, ema_alpha: float = 0.20, history_size: int = 128) -> None:
        self.ema_alpha = clamp(ema_alpha, 0.01, 1.0)
        self.history: deque[FeatureSnapshot] = deque(maxlen=max(8, int(history_size)))
        self.energy = 0.0
        self.energy_smooth = 0.0
        self.onset = 0.0
        self.centroid = 0.0
        self.low = 0.0
        self.mid = 0.0
        self.high = 0.0
        self.beat_phase = 0.0

    def update(self, features: Any, time_s: float | None = None) -> FeatureSnapshot:
        energy = clamp(_feature_get(features, "energy", 0.0))
        if not self.history:
            self.energy_smooth = energy
        else:
            self.energy_smooth = (self.ema_alpha * energy) + ((1.0 - self.ema_alpha) * self.energy_smooth)
        self.energy = energy
        self.onset = clamp(_feature_get(features, "onset", _feature_get(features, "onset_strength", 0.0)))
        self.centroid = clamp(_feature_get(features, "centroid", _feature_get(features, "spectral_centroid", 0.0)))
        self.low = _band(features, 0, "low")
        self.mid = _band(features, 1, "mid")
        self.high = _band(features, 2, "high")
        self.beat_phase = clamp(_feature_get(features, "beat_phase", 0.0))
        if time_s is None:
            time_s = _feature_get(features, "time_s", len(self.history) / 20.0)
        snapshot = FeatureSnapshot(
            time_s=float(time_s),
            energy=self.energy,
            energy_smooth=self.energy_smooth,
            onset=self.onset,
            centroid=self.centroid,
            low=self.low,
            mid=self.mid,
            high=self.high,
            beat_phase=self.beat_phase,
        )
        self.history.append(snapshot)
        return snapshot

    def trend(self, key: str, window: int = 8) -> float:
        if len(self.history) < 2:
            return 0.0
        rows = list(self.history)[-max(2, int(window)):]
        return float(getattr(rows[-1], key, 0.0) - getattr(rows[0], key, 0.0))

    def average(self, key: str, window: int = 16) -> float:
        rows = list(self.history)[-max(1, int(window)):]
        if not rows:
            return 0.0
        return sum(float(getattr(row, key, 0.0)) for row in rows) / len(rows)


@dataclass(frozen=True)
class Motif:
    name: str
    motion_pattern: str
    effect_preferences: tuple[str, ...]
    spatial_bias: str


MOTIF_LIBRARY: dict[str, Motif] = {
    "wave_sweep": Motif("wave_sweep", "linear_propagation", ("Ramp", "Wave", "On"), "horizontal"),
    "spiral": Motif("spiral", "rotational_ascent", ("Spirals", "Pinwheel", "Wave"), "vertical"),
    "pulse_cascade": Motif("pulse_cascade", "stepped_neighbor_burst", ("On", "Ramp", "Bars"), "ground"),
    "orbit": Motif("orbit", "looping_perimeter_motion", ("Pinwheel", "Single Strand", "Wave"), "perimeter"),
    "sparkle_field": Motif("sparkle_field", "distributed_high_frequency_points", ("Twinkle", "Shimmer", "On"), "vertical"),
}


@dataclass
class Phrase:
    start_time: float
    duration: float
    motif: str
    direction: str = "forward"

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration


class PhraseEngine:
    def __init__(self, min_duration_s: float = 2.0, max_duration_s: float = 8.0) -> None:
        self.min_duration_s = float(min_duration_s)
        self.max_duration_s = float(max_duration_s)
        self.current_phrase: Phrase | None = None
        self._motif_index = 0

    def update(self, time_s: float, feature_state: FeatureState) -> Phrase:
        if self.current_phrase is None or self._is_new_phrase(time_s, feature_state):
            self.current_phrase = self._create_phrase(time_s, feature_state)
        return self.current_phrase

    def _is_new_phrase(self, time_s: float, state: FeatureState) -> bool:
        if self.current_phrase is None:
            return True
        age = time_s - self.current_phrase.start_time
        if age >= self.max_duration_s:
            return True
        if age < self.min_duration_s:
            return False
        strong_onsets = sum(1 for row in list(state.history)[-12:] if row.onset >= 0.72)
        energy_shift = abs(state.trend("energy_smooth", 24)) >= 0.28
        return strong_onsets >= 3 or energy_shift

    def _create_phrase(self, time_s: float, state: FeatureState) -> Phrase:
        motif = self._choose_motif(state)
        self._motif_index += 1
        direction = "up" if state.high >= max(state.low, state.mid) else "down" if state.low > state.high else "forward"
        energy = clamp(state.energy_smooth)
        duration = self.min_duration_s + ((1.0 - energy) * (self.max_duration_s - self.min_duration_s))
        return Phrase(start_time=float(time_s), duration=duration, motif=motif, direction=direction)

    def _choose_motif(self, state: FeatureState) -> str:
        if state.high >= 0.62 and state.high >= state.low:
            candidates = ("sparkle_field", "spiral")
        elif state.low >= 0.58:
            candidates = ("pulse_cascade", "wave_sweep")
        elif state.mid >= 0.55:
            candidates = ("wave_sweep", "orbit")
        else:
            candidates = BIRDSONG_MOTIFS
        return candidates[self._motif_index % len(candidates)]


@dataclass(frozen=True)
class SpatialModel:
    name: str
    x: float
    y: float
    z: float
    category: str = "generic"


class SpatialMap:
    def __init__(self, models: Sequence[SpatialModel]) -> None:
        self.models = list(models)
        self.adjacency = self._build_adjacency(self.models)

    @classmethod
    def from_model_names(cls, names: Sequence[str]) -> "SpatialMap":
        models: list[SpatialModel] = []
        total = max(1, len(names))
        for index, name in enumerate(names):
            lower = name.lower()
            x = -1.0 + (2.0 * index / max(1, total - 1))
            y = 0.0
            z = 0.35
            category = "horizontal"
            if any(token in lower for token in ("bass", "kick", "drum", "snare", "sub", "floor", "low", "ground")):
                y, z, category = -0.6, 0.05, "ground"
            elif any(token in lower for token in ("star", "flake", "sparkle", "snow", "roof", "top", "high")):
                y, z, category = 0.25, 0.9, "vertical"
            elif any(token in lower for token in ("arch", "cane", "outline", "frame", "border", "perim")):
                y, z, category = 0.0, 0.35, "perimeter"
            models.append(SpatialModel(str(name), x, y, z, category))
        return cls(models)

    def query(self, position: tuple[float, float, float], radius: float) -> list[SpatialModel]:
        return [model for model in self.models if distance(position, (model.x, model.y, model.z)) <= radius]

    def feature_anchor(self, state: FeatureState) -> tuple[float, float, float]:
        if state.low >= max(state.mid, state.high):
            return (0.0, -0.65, 0.05)
        if state.high >= max(state.low, state.mid):
            return (0.0, 0.25, 0.95)
        return (0.0, 0.0, 0.35)

    @staticmethod
    def _build_adjacency(models: Sequence[SpatialModel]) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        for model in models:
            neighbors = sorted(
                (other for other in models if other.name != model.name),
                key=lambda other: distance((model.x, model.y, model.z), (other.x, other.y, other.z)),
            )[:4]
            graph[model.name] = [neighbor.name for neighbor in neighbors]
        return graph


def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


@dataclass
class EnergyWave:
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    energy: float
    decay: float = 0.92
    radius: float = 0.22

    def update(self, dt: float) -> None:
        self.position = (
            self.position[0] + self.velocity[0] * dt,
            self.position[1] + self.velocity[1] * dt,
            self.position[2] + self.velocity[2] * dt,
        )
        self.energy *= self.decay ** max(0.0, dt * 20.0)
        self.radius = min(0.75, self.radius + (dt * 0.18))

    @property
    def alive(self) -> bool:
        return self.energy >= 0.05


def spawn_energy_waves(state: FeatureState, phrase: Phrase, spatial_map: SpatialMap) -> list[EnergyWave]:
    if state.onset < 0.50 and state.energy_smooth < 0.66:
        return []
    anchor = spatial_map.feature_anchor(state)
    motif = MOTIF_LIBRARY.get(phrase.motif, MOTIF_LIBRARY["wave_sweep"])
    spatial_bias = _spatial_role(motif.spatial_bias)
    if phrase.motif == "spiral":
        velocity = (0.20, 0.05, 0.35)
    elif spatial_bias == "vertical":
        velocity = (0.35, 0.08, 0.18)
    elif spatial_bias == "ground":
        velocity = (0.42, 0.03, 0.05)
    elif spatial_bias == "perimeter":
        velocity = (0.48, 0.16, 0.02)
    else:
        velocity = (0.52, 0.0, 0.02)
    if phrase.direction == "down":
        velocity = (-velocity[0], velocity[1], -abs(velocity[2]))
    return [EnergyWave(position=anchor, velocity=velocity, energy=clamp(max(state.onset, state.energy_smooth)))]


def spawn_trigger_wave(trigger_type: str, state: FeatureState, spatial_map: SpatialMap) -> EnergyWave | None:
    trigger = str(trigger_type or "").strip().lower()
    if trigger in {"kick", "bass"}:
        position = (0.0, -0.65, 0.05)
        velocity = (0.56, 0.02, 0.02)
        energy = max(0.72, state.energy_smooth, state.onset, state.low)
        return EnergyWave(position=position, velocity=velocity, energy=clamp(energy), decay=0.90, radius=0.26)
    if trigger in {"snare", "clap"}:
        position = (0.0, 0.0, 0.35)
        velocity = (0.42, 0.00, 0.16)
        energy = max(0.62, state.energy_smooth, state.onset, state.mid)
        return EnergyWave(position=position, velocity=velocity, energy=clamp(energy), decay=0.91, radius=0.24)
    if trigger in {"hat", "hihat", "hi_hat", "cymbal"}:
        position = (0.0, 0.25, 0.95)
        velocity = (0.30, 0.08, 0.24)
        energy = max(0.55, state.energy_smooth, state.onset, state.high)
        return EnergyWave(position=position, velocity=velocity, energy=clamp(energy), decay=0.88, radius=0.20)
    return None


@dataclass(frozen=True)
class EffectCandidate:
    name: str
    energy_target: float = 0.5
    spatial_bias: str = "generic"


DEFAULT_EFFECTS: tuple[EffectCandidate, ...] = (
    EffectCandidate("On", 0.35, "ground"),
    EffectCandidate("Ramp", 0.55, "horizontal"),
    EffectCandidate("Wave", 0.65, "horizontal"),
    EffectCandidate("Pinwheel", 0.72, "perimeter"),
    EffectCandidate("Twinkle", 0.48, "vertical"),
    EffectCandidate("Shimmer", 0.62, "vertical"),
)


class EffectScoringEngine:
    def __init__(self) -> None:
        self._recent: deque[str] = deque(maxlen=24)

    def select(self, model: SpatialModel, wave: EnergyWave, phrase: Phrase, candidates: Sequence[EffectCandidate] = DEFAULT_EFFECTS) -> EffectCandidate:
        motif = MOTIF_LIBRARY.get(phrase.motif, MOTIF_LIBRARY["wave_sweep"])
        preferred = set(motif.effect_preferences)
        scored = [(self.score(candidate, model, wave, preferred), candidate) for candidate in candidates]
        scored.sort(key=lambda item: (-item[0], item[1].name))
        choice = scored[0][1]
        self._recent.append(choice.name)
        return choice

    def score(self, effect: EffectCandidate, model: SpatialModel, wave: EnergyWave, preferred: set[str]) -> float:
        energy_match = 1.0 - min(1.0, abs(wave.energy - effect.energy_target))
        effect_bias = _spatial_role(effect.spatial_bias)
        model_category = _spatial_role(model.category)
        spatial_fit = 1.0 if effect_bias == model_category else 0.55 if effect_bias == "generic" else 0.25
        novelty = 0.35 if effect.name in self._recent else 1.0
        continuity = 1.0 if effect.name in preferred else 0.55
        return (energy_match * 0.35) + (spatial_fit * 0.25) + (novelty * 0.20) + (continuity * 0.20)


@dataclass(frozen=True)
class RenderEvent:
    model: str
    start_ms: int
    end_ms: int
    effect: str
    motif: str
    intensity: float


class BehaviorEngine:
    def __init__(self, spatial_map: SpatialMap, scorer: EffectScoringEngine | None = None) -> None:
        self.spatial_map = spatial_map
        self.scorer = scorer or EffectScoringEngine()
        self.waves: list[EnergyWave] = []
        self._last_time_s: float | None = None

    def inject_wave(self, wave: EnergyWave | None) -> None:
        if wave is not None:
            self.waves.append(wave)

    def update(self, time_s: float, feature_state: FeatureState, phrase: Phrase) -> list[RenderEvent]:
        dt = 0.05 if self._last_time_s is None else max(0.01, min(0.25, time_s - self._last_time_s))
        self._last_time_s = time_s
        self.waves.extend(spawn_energy_waves(feature_state, phrase, self.spatial_map))
        events: list[RenderEvent] = []
        next_waves: list[EnergyWave] = []
        for wave in self.waves:
            wave.update(dt)
            if not wave.alive:
                continue
            next_waves.append(wave)
            for model in self.spatial_map.query(wave.position, wave.radius):
                effect = self.scorer.select(model, wave, phrase)
                start_ms = int(round(time_s * 1000.0))
                duration_ms = int(round(90 + (wave.energy * 210)))
                events.append(RenderEvent(model.name, start_ms, start_ms + duration_ms, effect.name, phrase.motif, wave.energy))
        self.waves = next_waves
        return events


@dataclass
class BirdsongPipeline:
    spatial_map: SpatialMap
    feature_state: FeatureState = field(default_factory=FeatureState)
    phrase_engine: PhraseEngine = field(default_factory=PhraseEngine)
    behavior_engine: BehaviorEngine | None = None

    def __post_init__(self) -> None:
        if self.behavior_engine is None:
            self.behavior_engine = BehaviorEngine(self.spatial_map)

    def update(self, features: Any, time_s: float) -> list[RenderEvent]:
        self.feature_state.update(features, time_s)
        phrase = self.phrase_engine.update(time_s, self.feature_state)
        assert self.behavior_engine is not None
        return self.behavior_engine.update(time_s, self.feature_state, phrase)
