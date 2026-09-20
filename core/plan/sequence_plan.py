from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping
import json

PLAN_VERSION = "0.1"
PLAN_SCHEMA = "helix.sequence_plan.v1"


def _clean(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_clean(item) for item in value]
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _clean(item) for key, item in value.items()}
    return value


def _clamp01(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except Exception:
        number = default
    return max(0.0, min(1.0, number))


@dataclass
class PlanSection:
    name: str
    kind: str
    start: float
    end: float
    target_intensity: float = 0.5
    primary_groups: list[str] = field(default_factory=list)
    secondary_groups: list[str] = field(default_factory=list)
    palette: str | None = None
    motion_intent: str | None = None
    density: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class PlanPropGroup:
    name: str
    role: str
    members: list[str] = field(default_factory=list)
    best_for: list[str] = field(default_factory=list)
    energy_capacity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class PlanCue:
    time: float
    kind: str
    confidence: float = 0.5
    target_groups: list[str] = field(default_factory=list)
    effect_family: str | None = None
    intensity: float = 0.5
    locked: bool = False
    source: str = "planner"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = _clamp01(payload["confidence"], 0.5)
        payload["intensity"] = _clamp01(payload["intensity"], 0.5)
        return _clean(payload)


@dataclass
class RestraintRules:
    max_whole_house_hits_per_section: int = 4
    min_seconds_between_major_hits: float = 2.0
    max_simultaneous_dominant_groups: int = 3
    allow_strobe: bool = True
    strobe_requires_intensity_at_least: float = 0.85
    protect_manual_effects: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["strobe_requires_intensity_at_least"] = _clamp01(
            payload["strobe_requires_intensity_at_least"], 0.85
        )
        return _clean(payload)


Restraint = RestraintRules


PropGroup = PlanPropGroup


@dataclass
class ScoringTargets:
    timing_alignment_min: float = 0.90
    section_contrast_min: float = 0.75
    palette_consistency_min: float = 0.80
    density_penalty_max: float = 0.20
    prop_coverage_min: float = 0.70
    finale_strength_min: float = 0.85

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class SequencePlan:
    source_audio: str
    fps: int
    duration_seconds: float
    style: str = "general"
    sections: list[PlanSection] = field(default_factory=list)
    prop_groups: list[PlanPropGroup] = field(default_factory=list)
    restraint: RestraintRules = field(default_factory=RestraintRules)
    cues: list[PlanCue] = field(default_factory=list)
    scoring_targets: ScoringTargets = field(default_factory=ScoringTargets)
    schema: str = PLAN_SCHEMA
    version: str = PLAN_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.source_audio:
            errors.append("source_audio is required")
        if self.fps <= 0:
            errors.append("fps must be positive")
        if self.duration_seconds < 0:
            errors.append("duration_seconds must be non-negative")
        previous_end = 0.0
        for section in self.sections:
            if section.end < section.start:
                errors.append(f"section {section.name!r} has end before start")
            if section.start < previous_end - 1e-6:
                errors.append(f"sections overlap or are out of order at {section.name!r}")
            previous_end = max(previous_end, section.end)
        for cue in self.cues:
            if cue.time < 0 or cue.time > self.duration_seconds + 0.001:
                errors.append(f"cue {cue.kind!r} is outside the song duration")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "source_audio": self.source_audio,
            "fps": self.fps,
            "duration_seconds": round(float(self.duration_seconds), 6),
            "style": self.style,
            "sections": [item.to_dict() for item in self.sections],
            "prop_groups": [item.to_dict() for item in self.prop_groups],
            "restraint": self.restraint.to_dict(),
            "cues": [item.to_dict() for item in self.cues],
            "scoring_targets": self.scoring_targets.to_dict(),
            "metadata": _clean(self.metadata),
        }

    def write_json(self, path: Path) -> Path:
        errors = self.validate()
        if errors:
            raise ValueError("Invalid SequencePlan: " + "; ".join(errors))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SequencePlan":
        return cls(
            schema=str(payload.get("schema", PLAN_SCHEMA)),
            version=str(payload.get("version", PLAN_VERSION)),
            source_audio=str(payload.get("source_audio", "")),
            fps=int(payload.get("fps", 40)),
            duration_seconds=float(payload.get("duration_seconds", 0.0)),
            style=str(payload.get("style", "general")),
            sections=[PlanSection(**item) for item in payload.get("sections", [])],
            prop_groups=[PlanPropGroup(**item) for item in payload.get("prop_groups", [])],
            restraint=RestraintRules(**payload.get("restraint", {})),
            cues=[PlanCue(**item) for item in payload.get("cues", [])],
            scoring_targets=ScoringTargets(**payload.get("scoring_targets", {})),
            metadata=dict(payload.get("metadata", {})),
        )


class SequencePlanBuilder:
    """Adapter from existing analysis/layout/style objects into one renderer-neutral plan."""

    def __init__(self, *, fps: int = 40):
        self.fps = int(fps)

    def from_audio_analysis(
        self,
        analysis: Any,
        *,
        source_audio: str,
        style: str = "general",
        style_metadata: Mapping[str, Any] | None = None,
    ) -> SequencePlan:
        duration_ms = int(getattr(analysis, "metadata", {}).get("duration_ms", 0) or 0)
        sections: list[PlanSection] = []
        for item in getattr(analysis, "section_events", []) or []:
            name = str(getattr(item, "name", getattr(item, "section_type", "section")))
            start_ms = int(getattr(item, "start_ms", 0))
            end_ms = int(getattr(item, "end_ms", start_ms))
            strength = _clamp01(getattr(item, "strength", getattr(item, "energy", 0.5)), 0.5)
            sections.append(
                PlanSection(
                    name=name,
                    kind=name.lower().replace(" ", "_"),
                    start=start_ms / 1000.0,
                    end=end_ms / 1000.0,
                    target_intensity=strength,
                    density="high" if strength >= 0.72 else "low" if strength <= 0.35 else "medium",
                )
            )

        cues: list[PlanCue] = []
        for event in list(getattr(analysis, "beat_events", []) or [])[:512]:
            metadata = getattr(event, "metadata", {}) or {}
            cues.append(
                PlanCue(
                    time=float(getattr(event, "time_ms", 0)) / 1000.0,
                    kind="downbeat" if bool(metadata.get("downbeat")) else "beat",
                    confidence=_clamp01(getattr(event, "confidence", 0.5), 0.5),
                    intensity=_clamp01(getattr(event, "strength", 0.5), 0.5),
                    source="audio_intelligence",
                )
            )
        for event in list(getattr(analysis, "onset_events", []) or [])[:512]:
            cues.append(
                PlanCue(
                    time=float(getattr(event, "time_ms", 0)) / 1000.0,
                    kind="onset",
                    confidence=_clamp01(getattr(event, "confidence", 0.5), 0.5),
                    intensity=_clamp01(getattr(event, "strength", 0.5), 0.5),
                    source="audio_intelligence",
                )
            )

        metadata = dict(style_metadata or {})
        metadata["planner"] = "sequence_plan_builder"
        metadata["analysis_schema"] = getattr(analysis, "metadata", {}).get("analysis_schema", "")
        return SequencePlan(
            source_audio=source_audio,
            fps=self.fps,
            duration_seconds=duration_ms / 1000.0,
            style=style,
            sections=sections,
            cues=sorted(cues, key=lambda cue: (cue.time, cue.kind)),
            metadata=metadata,
        )

    def add_layout(self, plan: SequencePlan, parsed_layout: Any) -> SequencePlan:
        from helix_layout.prop_roles import classify_prop_role

        groups: dict[str, PlanPropGroup] = {}
        models = getattr(parsed_layout, "models", {}) or {}
        for model in models.values():
            if getattr(model, "is_submodel", False):
                continue
            roles = classify_prop_role(model)
            primary_role = next((role for role in roles if role not in {"pixel_prop", "AC_channel"}), roles[0])
            group = groups.setdefault(
                primary_role,
                PlanPropGroup(
                    name=primary_role,
                    role=primary_role,
                    energy_capacity="high" if "hero" in roles else "medium",
                ),
            )
            group.members.append(model.name)
            for role in roles:
                if role == primary_role or role in {"pixel_prop", "AC_channel"}:
                    continue
                secondary = groups.setdefault(
                    role,
                    PlanPropGroup(
                        name=role,
                        role=role,
                        energy_capacity="high" if "hero" in roles else "medium",
                    ),
                )
                if model.name not in secondary.members:
                    secondary.members.append(model.name)

        plan.prop_groups = sorted(groups.values(), key=lambda item: item.name)
        plan.metadata["layout_model_count"] = len(models)
        plan.metadata["layout_group_count"] = len(getattr(parsed_layout, "groups", {}) or {})
        return plan

    def apply_style_decision(self, plan: SequencePlan, decision: Any) -> SequencePlan:
        plan.style = str(getattr(decision, "detected_style", plan.style) or plan.style)
        profile = getattr(decision, "profile", None)
        if profile is not None:
            plan.metadata["style_profile"] = (
                profile.to_dict() if hasattr(profile, "to_dict") else _clean(profile)
            )
        plan.metadata["style_confidence"] = _clamp01(getattr(decision, "confidence", 0.0))
        return plan
