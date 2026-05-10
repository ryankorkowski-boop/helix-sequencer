from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class MotionVocabulary(str, Enum):
    PULSE = "pulse"
    CHASE = "chase"
    SWEEP = "sweep"
    BLOOM = "bloom"
    SHIMMER = "shimmer"
    CASCADE = "cascade"
    IMPACT = "impact"
    ORBITAL = "orbital"
    HELIX_SPIRAL = "helix_spiral"
    TEXTURE = "texture"
    BLACKOUT = "blackout"


class ContrastStrategy(str, Enum):
    NONE = "none"
    DARK_PRE_DROP = "dark_pre_drop"
    SPARSE_VERSE = "sparse_verse"
    ESCALATING_CHORUS = "escalating_chorus"
    WARM_COOL_ALTERNATION = "warm_cool_alternation"
    DENSE_SPARSE_ALTERNATION = "dense_sparse_alternation"


class DominanceStrategy(str, Enum):
    SINGLE_HERO = "single_hero"
    BAND_CENTRIC = "band_centric"
    MEGATREE_CENTRIC = "megatree_centric"
    DISTRIBUTED = "distributed"
    ORBITAL = "orbital"
    BACKGROUND_ONLY = "background_only"


class PaletteFamily(str, Enum):
    DEFAULT = "default"
    CLASSIC_CHRISTMAS = "classic_christmas"
    ELECTRIC_WINTER = "electric_winter"
    CINEMATIC_BLUE_GOLD = "cinematic_blue_gold"
    PARTY_NEON = "party_neon"
    SPATIAL_HELIX = "spatial_helix"
    WARM_WHITE_GOLD = "warm_white_gold"


class ChoreographyTarget(str, Enum):
    ALL = "all"
    CENTERPIECE = "centerpiece"
    MOTION = "motion"
    ACCENT = "accent"
    OUTLINE = "outline"
    MATRIX = "matrix"
    BACKGROUND = "background"
    PERFORMER = "performer"
    SEQUENTIAL = "sequential"
    SPECIAL = "special"


class IntentLayerRole(str, Enum):
    BASE = "base"
    EVENT = "event"
    MOTION = "motion"
    SUSTAIN = "sustain"
    ACCENT = "accent"


@dataclass(frozen=True)
class IntentValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChoreographyIntent:
    """Canonical choreography language used across Helix.

    This object represents what the show intends to do visually. It is authored
    by the Style Engine / choreography layer and interpreted by sequential
    layering, prop specialists, composition governor, exporters, and GUI.
    """

    start: float
    duration: float
    section: str
    event_type: str
    style: str
    emotional_energy: float
    intensity: float
    focal_region: str
    support_regions: tuple[str, ...] = ()
    target_families: tuple[ChoreographyTarget, ...] = (ChoreographyTarget.ALL,)
    dominant_prop: str | None = None
    dominance_strategy: DominanceStrategy = DominanceStrategy.SINGLE_HERO
    motion_vocabulary: tuple[MotionVocabulary, ...] = (MotionVocabulary.TEXTURE,)
    contrast_strategy: ContrastStrategy = ContrastStrategy.NONE
    escalation_phase: int = 0
    palette_family: PaletteFamily = PaletteFamily.DEFAULT
    density_budget: float = 0.5
    layer_roles: tuple[IntentLayerRole, ...] = (IntentLayerRole.BASE,)
    source: str = "unknown"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def end(self) -> float:
        return round(self.start + self.duration, 6)

    @property
    def intent_id(self) -> str:
        safe_style = self.style.replace(" ", "_")
        safe_section = self.section.replace(" ", "_")
        return f"{safe_style}:{safe_section}:{self.start:.3f}:{self.duration:.3f}:{self.event_type}"

    def validate(self) -> IntentValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if self.start < 0:
            errors.append("start must be non-negative")
        if self.duration <= 0:
            errors.append("duration must be positive")
        if not self.section:
            errors.append("section is required")
        if not self.event_type:
            errors.append("event_type is required")
        if not self.style:
            errors.append("style is required")
        if not 0.0 <= self.emotional_energy <= 1.0:
            errors.append("emotional_energy must be between 0 and 1")
        if not 0.0 <= self.intensity <= 1.0:
            errors.append("intensity must be between 0 and 1")
        if not 0.0 <= self.density_budget <= 1.0:
            errors.append("density_budget must be between 0 and 1")
        if not self.focal_region:
            warnings.append("focal_region is empty")
        if not self.motion_vocabulary:
            warnings.append("motion_vocabulary is empty")
        if not self.layer_roles:
            warnings.append("layer_roles is empty")

        return IntentValidationResult(valid=not errors, errors=tuple(errors), warnings=tuple(warnings))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["end"] = self.end
        data["intent_id"] = self.intent_id
        data["target_families"] = [target.value for target in self.target_families]
        data["dominance_strategy"] = self.dominance_strategy.value
        data["motion_vocabulary"] = [motion.value for motion in self.motion_vocabulary]
        data["contrast_strategy"] = self.contrast_strategy.value
        data["palette_family"] = self.palette_family.value
        data["layer_roles"] = [role.value for role in self.layer_roles]
        data["metadata"] = dict(self.metadata)
        return data

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ChoreographyIntent":
        def _enum_tuple(enum_type: type[Enum], values: Iterable[str]) -> tuple[Any, ...]:
            return tuple(enum_type(value) for value in values)

        return cls(
            start=float(data["start"]),
            duration=float(data["duration"]),
            section=str(data["section"]),
            event_type=str(data["event_type"]),
            style=str(data["style"]),
            emotional_energy=float(data["emotional_energy"]),
            intensity=float(data["intensity"]),
            focal_region=str(data.get("focal_region", "")),
            support_regions=tuple(str(item) for item in data.get("support_regions", ())),
            target_families=_enum_tuple(ChoreographyTarget, data.get("target_families", (ChoreographyTarget.ALL.value,))),
            dominant_prop=data.get("dominant_prop"),
            dominance_strategy=DominanceStrategy(data.get("dominance_strategy", DominanceStrategy.SINGLE_HERO.value)),
            motion_vocabulary=_enum_tuple(MotionVocabulary, data.get("motion_vocabulary", (MotionVocabulary.TEXTURE.value,))),
            contrast_strategy=ContrastStrategy(data.get("contrast_strategy", ContrastStrategy.NONE.value)),
            escalation_phase=int(data.get("escalation_phase", 0)),
            palette_family=PaletteFamily(data.get("palette_family", PaletteFamily.DEFAULT.value)),
            density_budget=float(data.get("density_budget", 0.5)),
            layer_roles=_enum_tuple(IntentLayerRole, data.get("layer_roles", (IntentLayerRole.BASE.value,))),
            source=str(data.get("source", "unknown")),
            metadata=dict(data.get("metadata", {})),
        )


def validate_intents(intents: Iterable[ChoreographyIntent]) -> IntentValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    for intent in intents:
        result = intent.validate()
        errors.extend(f"{intent.intent_id}: {error}" for error in result.errors)
        warnings.extend(f"{intent.intent_id}: {warning}" for warning in result.warnings)
    return IntentValidationResult(valid=not errors, errors=tuple(errors), warnings=tuple(warnings))
