"""Unified engine coordinator and role-lane arbiter for Helix Sequencer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable


LAYER_ROLE_PRIORITY: dict[str, int] = {
    "base": 1,
    "texture": 2,
    "motion": 3,
    "accent": 4,
    "focus": 5,
}


class ConflictStrategy(str, Enum):
    SKIP = "skip"
    TRIM = "trim"
    STACK = "stack"


@dataclass(frozen=True)
class SectionWindow:
    name: str
    start_ms: int
    end_ms: int
    energy: float = 0.5


@dataclass(frozen=True)
class LayoutProp:
    prop_id: str
    prop_type: str = "generic"
    max_layers: int = 1
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class AudioAnalysisContext:
    audio_path: str = ""
    duration_ms: int = 0
    bpm: float = 120.0
    beat_grid_ms: tuple[int, ...] = ()
    sections: tuple[SectionWindow, ...] = ()
    sample_rate: int = 44100

    @property
    def fingerprint(self) -> str:
        payload = {
            "audio_path": self.audio_path,
            "duration_ms": self.duration_ms,
            "bpm": self.bpm,
            "beat_grid_ms": list(self.beat_grid_ms),
            "sections": [
                {
                    "name": s.name,
                    "start_ms": s.start_ms,
                    "end_ms": s.end_ms,
                    "energy": s.energy,
                }
                for s in self.sections
            ],
            "sample_rate": self.sample_rate,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def section_for_ms(self, ms: int) -> SectionWindow | None:
        for idx, section in enumerate(self.sections):
            is_last = idx == len(self.sections) - 1
            if section.start_ms <= ms < section.end_ms or (is_last and ms == section.end_ms):
                return section
        return None

    def snap_ms(self, ms: int, tolerance_ms: int | None = None) -> int:
        if not self.beat_grid_ms:
            return ms
        nearest = min(self.beat_grid_ms, key=lambda beat: (abs(beat - ms), beat))
        if tolerance_ms is not None and abs(nearest - ms) > tolerance_ms:
            return ms
        return nearest


@dataclass(frozen=True)
class EngineEffectCandidate:
    engine_id: str
    prop_id: str
    role: str
    effect_type: str
    start_ms: int
    end_ms: int
    score: float = 1.0
    layer_index: int = 0
    snap_to_beat: bool = True
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlannedEffect:
    engine_id: str
    prop_id: str
    role: str
    effect_type: str
    start_ms: int
    end_ms: int
    layer_index: int = 0
    score: float = 1.0
    priority: int = 1
    section_name: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnginePolicy:
    engine_id: str
    allowed_roles: tuple[str, ...]
    prop_scopes: tuple[str, ...] = ()
    precedence: int = 0
    max_per_section: int | None = None
    cooldown_ms: int = 0
    conflict_strategy: ConflictStrategy = ConflictStrategy.STACK
    fallback_strategy: ConflictStrategy = ConflictStrategy.TRIM
    snap_to_beat: bool = True
    enabled: bool = True


@dataclass(frozen=True)
class ArbitrationDecision:
    candidate: EngineEffectCandidate
    accepted: bool
    reason: str
    strategy_used: str = ""
    planned_effects: tuple[PlannedEffect, ...] = ()


@dataclass(frozen=True)
class ArbitrationReport:
    context_fingerprint: str
    total_candidates: int
    accepted_count: int
    rejected_count: int
    decisions: tuple[ArbitrationDecision, ...] = ()
    engine_errors: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_fingerprint": self.context_fingerprint,
            "total_candidates": self.total_candidates,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "engine_errors": [
                {"engine_id": engine_id, "error": err}
                for engine_id, err in self.engine_errors
            ],
            "decisions": [
                {
                    "engine_id": d.candidate.engine_id,
                    "prop_id": d.candidate.prop_id,
                    "role": d.candidate.role,
                    "effect_type": d.candidate.effect_type,
                    "start_ms": d.candidate.start_ms,
                    "end_ms": d.candidate.end_ms,
                    "accepted": d.accepted,
                    "reason": d.reason,
                    "strategy_used": d.strategy_used,
                    "planned_count": len(d.planned_effects),
                }
                for d in self.decisions
            ],
        }


@dataclass(frozen=True)
class CoordinationResult:
    planned_effects: tuple[PlannedEffect, ...]
    report: ArbitrationReport
    errors: dict[str, str] = field(default_factory=dict)

DEFAULT_ENGINE_POLICIES: dict[str, EnginePolicy] = {
    "core_base": EnginePolicy(
        engine_id="core_base",
        allowed_roles=("base",),
        precedence=10,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "helix_intent": EnginePolicy(
        engine_id="helix_intent",
        allowed_roles=("base", "texture", "motion"),
        precedence=20,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "chronoflow": EnginePolicy(
        engine_id="chronoflow",
        allowed_roles=("texture", "motion"),
        precedence=30,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "helixualizer": EnginePolicy(
        engine_id="helixualizer",
        allowed_roles=("texture", "motion", "accent"),
        precedence=40,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "matrix_intelligence": EnginePolicy(
        engine_id="matrix_intelligence",
        allowed_roles=("texture", "accent", "focus"),
        prop_scopes=("matrix",),
        precedence=50,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "snowman_band": EnginePolicy(
        engine_id="snowman_band",
        allowed_roles=("motion", "accent"),
        prop_scopes=("snowman", "band"),
        precedence=55,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "band_sync": EnginePolicy(
        engine_id="band_sync",
        allowed_roles=("motion", "accent"),
        prop_scopes=("band",),
        precedence=60,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "piano_effect": EnginePolicy(
        engine_id="piano_effect",
        allowed_roles=("motion", "accent", "focus"),
        precedence=70,
        max_per_section=8,
        cooldown_ms=100,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "drum_effects": EnginePolicy(
        engine_id="drum_effects",
        allowed_roles=("accent", "focus"),
        precedence=80,
        max_per_section=12,
        cooldown_ms=50,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "hardkor_engine": EnginePolicy(
        engine_id="hardkor_engine",
        allowed_roles=("accent", "focus"),
        precedence=90,
        max_per_section=6,
        cooldown_ms=150,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
    "birdsong": EnginePolicy(
        engine_id="birdsong",
        allowed_roles=("texture", "accent", "focus"),
        precedence=65,
        max_per_section=4,
        cooldown_ms=250,
        conflict_strategy=ConflictStrategy.STACK,
        fallback_strategy=ConflictStrategy.TRIM,
    ),
}


@runtime_checkable
class SequencerEngineAdapter(Protocol):
    engine_id: str

    def generate_candidates(
        self,
        context: AudioAnalysisContext,
        props: Sequence[LayoutProp],
    ) -> Sequence[EngineEffectCandidate]:
        ...


class CallableEngineAdapter:
    def __init__(
        self,
        engine_id: str,
        fn: Callable[[AudioAnalysisContext, Sequence[LayoutProp]], Sequence[EngineEffectCandidate]],
    ) -> None:
        self.engine_id = engine_id
        self._fn = fn

    def generate_candidates(
        self,
        context: AudioAnalysisContext,
        props: Sequence[LayoutProp],
    ) -> Sequence[EngineEffectCandidate]:
        return self._fn(context, props)


class EngineArbiter:
    def __init__(self, policies: Mapping[str, EnginePolicy] | None = None) -> None:
        self.policies: dict[str, EnginePolicy] = dict(DEFAULT_ENGINE_POLICIES)
        if policies:
            self.policies.update(policies)

    def _policy_for(self, engine_id: str) -> EnginePolicy:
        if engine_id in self.policies:
            return self.policies[engine_id]
        return EnginePolicy(
            engine_id=engine_id,
            allowed_roles=tuple(LAYER_ROLE_PRIORITY.keys()),
        )

    @staticmethod
    def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
        return a_start < b_end and b_start < a_end

    @classmethod
    def _find_free_layer(
        cls,
        occupied: Mapping[tuple[str, int], list[tuple[int, int]]],
        prop_id: str,
        max_layers: int,
        preferred_layer: int,
        start_ms: int,
        end_ms: int,
    ) -> int | None:
        if max_layers <= 0:
            return None
        order: list[int] = []
        if 0 <= preferred_layer < max_layers:
            order.append(preferred_layer)
        for layer in range(max_layers):
            if layer not in order:
                order.append(layer)
        for layer in order:
            intervals = occupied.get((prop_id, layer), ())
            if not any(cls._overlaps(start_ms, end_ms, s, e) for s, e in intervals):
                return layer
        return None

    @staticmethod
    def _subtract_intervals(
        start_ms: int,
        end_ms: int,
        intervals: Sequence[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        segments: list[tuple[int, int]] = [(start_ms, end_ms)]
        for occ_start, occ_end in sorted(intervals):
            next_segments: list[tuple[int, int]] = []
            for seg_start, seg_end in segments:
                if occ_end <= seg_start or occ_start >= seg_end:
                    next_segments.append((seg_start, seg_end))
                else:
                    if seg_start < occ_start:
                        next_segments.append((seg_start, occ_start))
                    if occ_end < seg_end:
                        next_segments.append((occ_end, seg_end))
            segments = next_segments
            if not segments:
                break
        return [(s, e) for s, e in segments if e > s]

    def arbitrate(
        self,
        context: AudioAnalysisContext,
        candidates: Sequence[EngineEffectCandidate],
        props: Sequence[LayoutProp],
        engine_errors: Sequence[tuple[str, str]] = (),
    ) -> CoordinationResult:
        prop_map = {prop.prop_id: prop for prop in props}
        ordered = sorted(
            candidates,
            key=lambda c: (
                -LAYER_ROLE_PRIORITY.get(c.role, 0),
                -float(c.score),
                -self._policy_for(c.engine_id).precedence,
                c.start_ms,
                c.end_ms,
                c.engine_id,
                c.prop_id,
                c.effect_type,
            ),
        )

        occupied: dict[tuple[str, int], list[tuple[int, int]]] = {}
        section_counts: dict[tuple[str, str], int] = {}
        cooldown_history: dict[tuple[str, str], list[tuple[int, int]]] = {}
        decisions: list[ArbitrationDecision] = []
        planned: list[PlannedEffect] = []

        for cand in ordered:
            policy = self._policy_for(cand.engine_id)
            if not policy.enabled:
                decisions.append(ArbitrationDecision(cand, False, "engine_disabled"))
                continue

            if cand.role not in LAYER_ROLE_PRIORITY or cand.role not in policy.allowed_roles:
                decisions.append(ArbitrationDecision(cand, False, "role_not_allowed"))
                continue

            prop = prop_map.get(cand.prop_id)
            if prop is None:
                decisions.append(ArbitrationDecision(cand, False, "unknown_prop"))
                continue

            if policy.prop_scopes:
                in_scope = (
                    prop.prop_type in policy.prop_scopes
                    or prop.prop_id in policy.prop_scopes
                    or any(tag in policy.prop_scopes for tag in prop.tags)
                )
                if not in_scope:
                    decisions.append(ArbitrationDecision(cand, False, "prop_out_of_scope"))
                    continue

            start_ms = context.snap_ms(cand.start_ms) if (policy.snap_to_beat and cand.snap_to_beat) else cand.start_ms
            end_ms = context.snap_ms(cand.end_ms) if (policy.snap_to_beat and cand.snap_to_beat) else cand.end_ms
            if end_ms <= start_ms:
                decisions.append(ArbitrationDecision(cand, False, "invalid_time_window"))
                continue

            section = context.section_for_ms(start_ms)
            section_name = section.name if section is not None else "__global__"
            if policy.max_per_section is not None:
                used = section_counts.get((cand.engine_id, section_name), 0)
                if used >= policy.max_per_section:
                    decisions.append(ArbitrationDecision(cand, False, "section_budget_exceeded"))
                    continue

            if policy.cooldown_ms > 0:
                prev_windows = cooldown_history.get((cand.engine_id, cand.prop_id), ())
                in_cooldown = any(
                    not (end_ms + policy.cooldown_ms <= ps or start_ms >= pe + policy.cooldown_ms)
                    for ps, pe in prev_windows
                )
                if in_cooldown:
                    decisions.append(ArbitrationDecision(cand, False, "cooldown_active"))
                    continue

            max_layers = max(1, prop.max_layers)
            target_layer = min(max(cand.layer_index, 0), max_layers - 1)
            chosen_segments: list[tuple[int, int, int]] = []
            strategy_used = ""

            if policy.conflict_strategy == ConflictStrategy.STACK:
                free_layer = self._find_free_layer(occupied, cand.prop_id, max_layers, target_layer, start_ms, end_ms)
                if free_layer is not None:
                    chosen_segments = [(start_ms, end_ms, free_layer)]
                    strategy_used = "stack"
                elif policy.fallback_strategy == ConflictStrategy.TRIM:
                    trimmed = self._subtract_intervals(
                        start_ms,
                        end_ms,
                        occupied.get((cand.prop_id, target_layer), ()),
                    )
                    if trimmed:
                        chosen_segments = [(s, e, target_layer) for s, e in trimmed]
                        strategy_used = "trim"
            elif policy.conflict_strategy == ConflictStrategy.TRIM:
                trimmed = self._subtract_intervals(
                    start_ms,
                    end_ms,
                    occupied.get((cand.prop_id, target_layer), ()),
                )
                if trimmed:
                    chosen_segments = [(s, e, target_layer) for s, e in trimmed]
                    strategy_used = "trim"
            else:
                intervals = occupied.get((cand.prop_id, target_layer), ())
                if not any(self._overlaps(start_ms, end_ms, s, e) for s, e in intervals):
                    chosen_segments = [(start_ms, end_ms, target_layer)]
                    strategy_used = "skip"

            if not chosen_segments:
                reason = (
                    "conflict_trimmed_empty"
                    if ConflictStrategy.TRIM in (policy.conflict_strategy, policy.fallback_strategy)
                    else "conflict_skipped"
                )
                decisions.append(ArbitrationDecision(cand, False, reason))
                continue

            priority = LAYER_ROLE_PRIORITY[cand.role]
            created: list[PlannedEffect] = []
            for seg_start, seg_end, layer_idx in chosen_segments:
                occupied.setdefault((cand.prop_id, layer_idx), []).append((seg_start, seg_end))
                created.append(
                    PlannedEffect(
                        engine_id=cand.engine_id,
                        prop_id=cand.prop_id,
                        role=cand.role,
                        effect_type=cand.effect_type,
                        start_ms=seg_start,
                        end_ms=seg_end,
                        layer_index=layer_idx,
                        score=cand.score,
                        priority=priority,
                        section_name=section.name if section is not None else None,
                        params=dict(cand.params),
                    )
                )

            section_counts[(cand.engine_id, section_name)] = section_counts.get((cand.engine_id, section_name), 0) + 1
            cooldown_history.setdefault((cand.engine_id, cand.prop_id), []).append((start_ms, end_ms))
            planned.extend(created)
            decisions.append(
                ArbitrationDecision(
                    candidate=cand,
                    accepted=True,
                    reason="accepted",
                    strategy_used=strategy_used,
                    planned_effects=tuple(created),
                )
            )

        planned.sort(key=lambda e: (e.prop_id, e.layer_index, e.start_ms, e.end_ms, -e.priority, e.engine_id))
        accepted_count = sum(1 for d in decisions if d.accepted)
        report = ArbitrationReport(
            context_fingerprint=context.fingerprint,
            total_candidates=len(decisions),
            accepted_count=accepted_count,
            rejected_count=len(decisions) - accepted_count,
            decisions=tuple(decisions),
            engine_errors=tuple(engine_errors),
        )
        return CoordinationResult(
            planned_effects=tuple(planned),
            report=report,
            errors=dict(engine_errors),
        )


class EngineCoordinator:
    def __init__(
        self,
        adapters: Sequence[SequencerEngineAdapter] | None = None,
        policies: Mapping[str, EnginePolicy] | None = None,
    ) -> None:
        self._adapters: list[SequencerEngineAdapter] = list(adapters or ())
        self.arbiter = EngineArbiter(policies=policies)

    def register(self, adapter: SequencerEngineAdapter) -> None:
        self._adapters.append(adapter)

    def coordinate(
        self,
        context: AudioAnalysisContext,
        props: Sequence[LayoutProp],
    ) -> CoordinationResult:
        all_candidates: list[EngineEffectCandidate] = []
        engine_errors: list[tuple[str, str]] = []
        for adapter in self._adapters:
            try:
                generated = adapter.generate_candidates(context, props)
                if generated:
                    all_candidates.extend(generated)
            except Exception as exc:
                engine_errors.append((adapter.engine_id, str(exc)))
        return self.arbiter.arbitrate(context, all_candidates, props, engine_errors=engine_errors)


def build_default_coordinator(
    adapters: Sequence[SequencerEngineAdapter] | None = None,
    policies: Mapping[str, EnginePolicy] | None = None,
) -> EngineCoordinator:
    return EngineCoordinator(adapters=adapters, policies=policies)

  
