from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from core.birdsong_behavior_planner import EffectIntent, plan_effect_intent
from core.birdsong_feature_state import FeatureState as BirdsongFeatureState
from core.birdsong_issue2_runtime import BirdsongRuntimeConfig, BirdsongSequenceRow, generate_birdsong_rows
from core.birdsong_phrase_engine import BIRDSONG_MOTIFS, Phrase, PhraseEngine
from core.birdsong_quality_score import BirdsongQualityReport, score_birdsong_manifest
from core.birdsong_xsq_export import emit_birdsong_xsq_sequence
from core.feature_state import FeatureStateFrame


@dataclass(frozen=True)
class BirdsongCompletionGateConfig:
    """Deterministic acceptance gate for the Issue #2 Birdsong stack.

    The gate is intentionally opt-in and side-effect free: it does not mutate the
    canonical engine path, write files, or alter v27/v28 defaults. Its job is to
    prove that the Issue #2 subsystems can operate together on real feature-state
    frames and real layout model names.
    """

    bpm: float = 120.0
    min_quality_score: float = 0.35
    runtime_min_energy: float = 0.20
    runtime_min_onset: float = 0.45
    runtime_duration_ms: int = 180
    max_runtime_targets_per_frame: int = 3
    require_xsq_effects: bool = True


@dataclass(frozen=True)
class BirdsongCompletionGateReport:
    schema: str
    passed: bool
    quality: dict[str, float | int]
    checks: dict[str, bool]
    frame_count: int
    phrase_count: int
    motif_count: int
    intent_count: int
    runtime_row_count: int
    xsq_effect_count: int
    motifs: list[str] = field(default_factory=list)
    phrases: list[dict[str, Any]] = field(default_factory=list)
    intents: list[dict[str, Any]] = field(default_factory=list)
    runtime_rows: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_birdsong_completion_gate(
    frames: Sequence[FeatureStateFrame],
    model_pool: Sequence[str],
    *,
    config: BirdsongCompletionGateConfig | None = None,
) -> BirdsongCompletionGateReport:
    """Run a full Issue #2 proof pass from feature frames to XSQ-ready output.

    Proven path:
    FeatureStateFrame -> smoothed Birdsong FeatureState -> PhraseEngine ->
    behavior/effect intent -> guarded runtime rows -> XSQ XML -> quality score.
    """

    cfg = config or BirdsongCompletionGateConfig()
    models = _clean_model_pool(model_pool)
    warnings: list[str] = []

    if not frames:
        warnings.append("No feature-state frames were provided.")
    if not models:
        warnings.append("No layout model names were provided.")

    phrase_engine = PhraseEngine(bpm=max(1.0, float(cfg.bpm)))
    state = BirdsongFeatureState()
    phrases_by_key: dict[tuple[float, str, str], Phrase] = {}
    intents: list[EffectIntent] = []
    recent_effects: list[str] = []
    previous_effect: str | None = None

    for frame in sorted(frames, key=lambda item: (item.time_s, item.frame_index)):
        state.update(_frame_mapping(frame))
        phrase = phrase_engine.update(frame.time_s, state)
        phrases_by_key[(phrase.start_time, phrase.motif, phrase.direction)] = phrase
        intent = plan_effect_intent(
            state=state,
            phrase=phrase,
            time=frame.time_s,
            recent_effects=tuple(recent_effects[-6:]),
            previous_effect=previous_effect,
        )
        if intent is None:
            continue
        intents.append(intent)
        previous_effect = intent.effect_name
        recent_effects.append(intent.effect_name)

    runtime_rows = generate_birdsong_rows(
        frames,
        models,
        config=BirdsongRuntimeConfig(
            enabled=True,
            min_energy=cfg.runtime_min_energy,
            min_onset=cfg.runtime_min_onset,
            duration_ms=cfg.runtime_duration_ms,
            max_targets_per_frame=cfg.max_runtime_targets_per_frame,
        ),
    )

    manifest = {"schema": "helix.birdsong_completion_gate.intent_manifest.v1", "intents": [_intent_record(item) for item in intents]}
    quality = score_birdsong_manifest(manifest)
    xsq = emit_birdsong_xsq_sequence(intents=intents, model_pool=tuple(models) or None)
    xsq_effect_count = xsq.xml_text.count("<effect ") + xsq.xml_text.count("<Effect ")

    motifs = sorted({item.motif for item in intents} | {row.motif for row in runtime_rows})
    checks = {
        "has_frames": bool(frames),
        "has_models": bool(models),
        "has_phrases": bool(phrases_by_key),
        "uses_allowed_motifs_only": all(motif in BIRDSONG_MOTIFS for motif in motifs),
        "has_intents": bool(intents),
        "has_runtime_rows": bool(runtime_rows),
        "has_xsq_effects": (xsq_effect_count > 0) if cfg.require_xsq_effects else True,
        "quality_meets_gate": quality.score >= cfg.min_quality_score,
    }
    passed = all(checks.values())
    if not passed:
        warnings.extend(_warnings_for_failed_checks(checks, quality, cfg))

    return BirdsongCompletionGateReport(
        schema="helix.issue2_birdsong_completion_gate.v1",
        passed=passed,
        quality=quality.as_dict(),
        checks=checks,
        frame_count=len(frames),
        phrase_count=len(phrases_by_key),
        motif_count=len(motifs),
        intent_count=len(intents),
        runtime_row_count=len(runtime_rows),
        xsq_effect_count=xsq_effect_count,
        motifs=motifs,
        phrases=[_phrase_record(item) for item in sorted(phrases_by_key.values(), key=lambda phrase: phrase.start_time)],
        intents=[_intent_record(item) for item in intents],
        runtime_rows=[_row_record(item) for item in runtime_rows],
        warnings=warnings,
    )


def _clean_model_pool(model_pool: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in model_pool:
        model = str(raw).strip()
        key = model.lower()
        if not model or key in seen:
            continue
        seen.add(key)
        out.append(model)
    return out


def _frame_mapping(frame: FeatureStateFrame) -> Mapping[str, object]:
    return {
        "energy": frame.energy,
        "onset": frame.onset,
        "centroid": frame.centroid,
        "low": frame.low,
        "mid": frame.mid,
        "high": frame.high,
        "beat_phase": frame.beat_phase,
    }


def _phrase_record(phrase: Phrase) -> dict[str, Any]:
    return {
        "start_time": phrase.start_time,
        "duration": phrase.duration,
        "end_time": phrase.end_time,
        "motif": phrase.motif,
        "direction": phrase.direction,
        "energy_anchor": phrase.energy_anchor,
    }


def _intent_record(intent: EffectIntent) -> dict[str, Any]:
    return {
        "effect_name": intent.effect_name,
        "motif": intent.motif,
        "direction": intent.direction,
        "start_time": intent.start_time,
        "duration": intent.duration,
        "end_time": intent.end_time,
        "strength": intent.strength,
        "score": intent.score,
    }


def _row_record(row: BirdsongSequenceRow) -> dict[str, Any]:
    return {
        "model": row.model,
        "start_ms": row.start_ms,
        "end_ms": row.end_ms,
        "label": row.label,
        "effect": row.effect,
        "motif": row.motif,
        "intensity": row.intensity,
    }


def _warnings_for_failed_checks(
    checks: Mapping[str, bool],
    quality: BirdsongQualityReport,
    config: BirdsongCompletionGateConfig,
) -> list[str]:
    warnings: list[str] = []
    for name, passed in checks.items():
        if passed:
            continue
        if name == "quality_meets_gate":
            warnings.append(f"Birdsong quality score {quality.score:.3f} is below gate {config.min_quality_score:.3f}.")
        else:
            warnings.append(f"Birdsong completion check failed: {name}.")
    return warnings


__all__ = [
    "BirdsongCompletionGateConfig",
    "BirdsongCompletionGateReport",
    "run_birdsong_completion_gate",
]
