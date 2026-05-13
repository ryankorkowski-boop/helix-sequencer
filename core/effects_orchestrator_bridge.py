from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.choreography_intent import (
    ChoreographyIntent,
    ChoreographyTarget,
    ContrastStrategy,
    DominanceStrategy,
    IntentLayerRole,
    MotionVocabulary,
    PaletteFamily,
)
from core.intent_graph import IntentGraph
from core.multi_pass_orchestration_director import MultiPassOrchestrationDirector


@dataclass(frozen=True)
class EffectsOrchestrationRunReport:
    available: bool
    enabled: bool
    invoked: bool
    input_intents: int
    final_intents: int
    masterpiece_score: float
    masterpiece_candidate: bool
    passes: tuple[dict[str, Any], ...]
    report_path: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def orchestration_report_path(engine_args: list[str] | None) -> Path:
    args = engine_args or []
    output_dir: Path | None = None
    audio_name = "helix"
    for idx, item in enumerate(args):
        if item == "--output-dir" and idx + 1 < len(args):
            output_dir = Path(args[idx + 1])
        if item == "--audio" and idx + 1 < len(args):
            audio_name = Path(args[idx + 1]).stem or audio_name
    root = output_dir or Path("outputs")
    return root / f"{audio_name}.effects_orchestration.json"


def build_seed_graph(engine_args: list[str] | None = None) -> IntentGraph:
    args = engine_args or []
    song_length_seconds = 30.0
    for idx, item in enumerate(args):
        if item in {"--duration", "--seconds"} and idx + 1 < len(args):
            try:
                song_length_seconds = max(8.0, float(args[idx + 1]))
            except ValueError:
                pass
    section_count = 5
    section_duration = max(1.0, song_length_seconds / section_count)
    sections = ("intro", "verse", "build", "chorus", "finale")
    motions = (
        (MotionVocabulary.TEXTURE, MotionVocabulary.PULSE),
        (MotionVocabulary.SHIMMER, MotionVocabulary.PULSE),
        (MotionVocabulary.CHASE, MotionVocabulary.SWEEP),
        (MotionVocabulary.BLOOM, MotionVocabulary.CASCADE, MotionVocabulary.HELIX_SPIRAL),
        (MotionVocabulary.IMPACT, MotionVocabulary.ORBITAL, MotionVocabulary.HELIX_SPIRAL),
    )
    graph = IntentGraph()
    for index, section in enumerate(sections):
        energy = min(1.0, 0.25 + index * 0.17)
        graph.add_intent(
            ChoreographyIntent(
                start=round(index * section_duration, 3),
                duration=round(section_duration, 3),
                section=section,
                event_type="section_choreography",
                style="canonical_effects_orchestrator",
                emotional_energy=energy,
                intensity=energy,
                focal_region="stage" if section in {"chorus", "finale"} else "village",
                support_regions=("background", "skyline"),
                target_families=(ChoreographyTarget.PERFORMER, ChoreographyTarget.SEQUENTIAL, ChoreographyTarget.BACKGROUND),
                dominant_prop="HX_SNOWMAN_BAND" if section in {"chorus", "finale"} else None,
                dominance_strategy=DominanceStrategy.BAND_CENTRIC if section in {"chorus", "finale"} else DominanceStrategy.DISTRIBUTED,
                motion_vocabulary=motions[index],
                contrast_strategy=ContrastStrategy.ESCALATING_CHORUS if section in {"build", "chorus"} else ContrastStrategy.NONE,
                escalation_phase=index,
                palette_family=PaletteFamily.SPATIAL_HELIX if section == "finale" else PaletteFamily.CLASSIC_CHRISTMAS,
                density_budget=min(1.0, 0.25 + index * 0.12),
                layer_roles=(IntentLayerRole.BASE, IntentLayerRole.MOTION, IntentLayerRole.ACCENT),
                source="canonical_effects_orchestrator_bridge",
                metadata={"seed_section_index": index},
            )
        )
    return graph


def run_effects_orchestration(engine_args: list[str] | None = None, *, write_report: bool = True) -> EffectsOrchestrationRunReport:
    try:
        graph = build_seed_graph(engine_args)
        director = MultiPassOrchestrationDirector()
        result = director.direct(graph)
        passes = tuple({"pass_name": item.pass_name, "metadata": item.metadata} for item in result.passes)
        path = orchestration_report_path(engine_args)
        report = EffectsOrchestrationRunReport(
            available=True,
            enabled=True,
            invoked=True,
            input_intents=len(graph.intents),
            final_intents=len(result.final_graph.intents),
            masterpiece_score=result.masterpiece_score,
            masterpiece_candidate=result.masterpiece_candidate,
            passes=passes,
            report_path=str(path),
        )
        if write_report:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
    except Exception as exc:
        return EffectsOrchestrationRunReport(
            available=True,
            enabled=True,
            invoked=False,
            input_intents=0,
            final_intents=0,
            masterpiece_score=0.0,
            masterpiece_candidate=False,
            passes=(),
            error=str(exc),
        )
