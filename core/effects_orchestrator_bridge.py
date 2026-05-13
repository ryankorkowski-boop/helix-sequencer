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
from helix_intent.placement_pipeline import build_placement_plan
from helix_intent.placement_planner import PlacementCandidate
from helix_intent.placement_report import write_placement_export_report
from helix_intent.visual_intent import VisualIntent
from helix_intent.xlights_effect_contract import write_xlights_effect_contract


@dataclass(frozen=True)
class EffectsOrchestrationRunReport:
    available: bool
    enabled: bool
    invoked: bool
    input_intents: int
    final_intents: int
    final_visual_intents: int
    placement_count: int
    effect_contract_placement_count: int
    export_driven: bool
    masterpiece_score: float
    masterpiece_candidate: bool
    passes: tuple[dict[str, Any], ...]
    report_path: str | None = None
    placement_plan_path: str | None = None
    effect_contract_path: str | None = None
    placement_source: str = "none"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _arg_value(engine_args: list[str] | None, flag: str) -> str | None:
    args = engine_args or []
    for idx, item in enumerate(args):
        if item == flag and idx + 1 < len(args):
            return args[idx + 1]
    return None


def orchestration_report_path(engine_args: list[str] | None) -> Path:
    root = Path(_arg_value(engine_args, "--output-dir") or "outputs")
    audio_name = Path(_arg_value(engine_args, "--audio") or "helix").stem or "helix"
    return root / f"{audio_name}.effects_orchestration.json"


def placement_report_path(engine_args: list[str] | None) -> Path:
    root = Path(_arg_value(engine_args, "--output-dir") or "outputs")
    audio_name = Path(_arg_value(engine_args, "--audio") or "helix").stem or "helix"
    return root / f"{audio_name}.orchestrated_placement_plan.json"


def effect_contract_path(engine_args: list[str] | None) -> Path:
    root = Path(_arg_value(engine_args, "--output-dir") or "outputs")
    audio_name = Path(_arg_value(engine_args, "--audio") or "helix").stem or "helix"
    return root / f"{audio_name}.orchestrated_xlights_effect_contract.json"


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


def _density_level(intent: ChoreographyIntent) -> str:
    if intent.density_budget >= 0.62 or intent.intensity >= 0.78:
        return "full"
    if intent.density_budget <= 0.34 and intent.intensity <= 0.42:
        return "sparse"
    return "medium"


def _intent_type(intent: ChoreographyIntent) -> str:
    motions = {motion.value for motion in intent.motion_vocabulary}
    if {"bloom", "impact", "helix_spiral", "orbital"}.intersection(motions):
        return "bloom"
    if {"chase", "sweep", "cascade"}.intersection(motions):
        return "transition"
    if "shimmer" in motions:
        return "color_wash"
    return "color_wash"


def _spatial_behavior(intent: ChoreographyIntent) -> str:
    motions = {motion.value for motion in intent.motion_vocabulary}
    if "helix_spiral" in motions:
        return "helix_orbit"
    if "chase" in motions or "sweep" in motions:
        return "left_to_right_sweep"
    if "impact" in motions:
        return "center_out_impact"
    return "section_wash"


def _target_roles(intent: ChoreographyIntent) -> list[str]:
    roles = ["hero", "background", "roofline"]
    if intent.dominance_strategy == DominanceStrategy.BAND_CENTRIC or intent.dominant_prop:
        roles.insert(0, "performer")
        roles.insert(1, "vocal_prop")
    if intent.density_budget >= 0.55:
        roles.append("whole_house")
    return list(dict.fromkeys(roles))


def _render_hint(intent: ChoreographyIntent) -> str:
    if intent.dominance_strategy == DominanceStrategy.BAND_CENTRIC:
        return "per_model"
    if intent.density_budget >= 0.55:
        return "per_preview"
    return "per_model"


def visual_intents_from_graph(graph: IntentGraph) -> list[VisualIntent]:
    visual_intents: list[VisualIntent] = []
    for intent in graph:
        visual_intents.append(
            VisualIntent(
                id=f"orchestrated:{intent.intent_id}",
                start_time=intent.start,
                end_time=intent.end,
                intent_type=_intent_type(intent),
                musical_trigger=intent.event_type,
                spatial_behavior=_spatial_behavior(intent),
                target_roles=_target_roles(intent),
                density_level=_density_level(intent),
                emotional_role=intent.section,
                color_strategy=intent.palette_family.value,
                brightness_strategy="safe_peak" if intent.intensity >= 0.75 else "controlled",
                curve_strategy="attack_decay" if intent.intensity >= 0.7 else "section_envelope",
                render_style_hint=_render_hint(intent),
                confidence=round(max(0.1, min(1.0, intent.intensity)), 4),
            )
        )
    return visual_intents


def _fallback_candidates() -> list[PlacementCandidate]:
    return [
        PlacementCandidate("HX_SNOWMAN_BAND", "performer", "snowman_band", 5),
        PlacementCandidate("HX_STAGE_HERO", "hero", "trees", 10),
        PlacementCandidate("HX_MAIN_ROOFLINE", "structure", "roofline", 20),
        PlacementCandidate("HX_BACKGROUND_WASH", "mood", "mood_washes", 35),
    ]


def _layout_file_from_args(engine_args: list[str] | None) -> Path | None:
    raw = _arg_value(engine_args, "--layout-file")
    if not raw:
        return None
    path = Path(raw)
    return path if path.exists() else None


def _build_orchestrated_exports(final_graph: IntentGraph, engine_args: list[str] | None) -> dict[str, Any]:
    visual_intents = visual_intents_from_graph(final_graph)
    layout_file = _layout_file_from_args(engine_args)
    parsed_layout = None
    placement_source = "fallback_candidates"
    if layout_file is not None:
        try:
            from core import model_parser as xmp

            parsed_layout = xmp.parse_layout(layout_file)
            placement_source = str(layout_file)
        except Exception:
            parsed_layout = None
            placement_source = "fallback_candidates"

    placement_report = build_placement_plan(
        visual_intents=visual_intents,
        parsed_layout=parsed_layout,
        extra_candidates=_fallback_candidates(),
    )
    placement_path = placement_report_path(engine_args)
    write_placement_export_report(placement_report, placement_path)
    contract_path = effect_contract_path(engine_args)
    contract_report = write_xlights_effect_contract(
        placement_report.to_dict(),
        contract_path,
        minimum_quality_score=0.55,
    )
    return {
        "visual_intent_count": len(visual_intents),
        "placement_count": int(placement_report.planner_report.get("placement_count", 0) or 0),
        "effect_contract_placement_count": contract_report.placement_count,
        "placement_plan_path": str(placement_path),
        "effect_contract_path": str(contract_path),
        "placement_source": placement_source,
        "export_driven": contract_report.placement_count > 0,
    }


def run_effects_orchestration(engine_args: list[str] | None = None, *, write_report: bool = True) -> EffectsOrchestrationRunReport:
    try:
        graph = build_seed_graph(engine_args)
        director = MultiPassOrchestrationDirector()
        result = director.direct(graph)
        passes = tuple({"pass_name": item.pass_name, "metadata": item.metadata} for item in result.passes)
        export_payload = _build_orchestrated_exports(result.final_graph, engine_args) if write_report else {
            "visual_intent_count": len(visual_intents_from_graph(result.final_graph)),
            "placement_count": 0,
            "effect_contract_placement_count": 0,
            "placement_plan_path": None,
            "effect_contract_path": None,
            "placement_source": "not_written",
            "export_driven": False,
        }
        path = orchestration_report_path(engine_args)
        report = EffectsOrchestrationRunReport(
            available=True,
            enabled=True,
            invoked=True,
            input_intents=len(graph.intents),
            final_intents=len(result.final_graph.intents),
            final_visual_intents=int(export_payload["visual_intent_count"]),
            placement_count=int(export_payload["placement_count"]),
            effect_contract_placement_count=int(export_payload["effect_contract_placement_count"]),
            export_driven=bool(export_payload["export_driven"]),
            masterpiece_score=result.masterpiece_score,
            masterpiece_candidate=result.masterpiece_candidate,
            passes=passes,
            report_path=str(path),
            placement_plan_path=export_payload["placement_plan_path"],
            effect_contract_path=export_payload["effect_contract_path"],
            placement_source=str(export_payload["placement_source"]),
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
            final_visual_intents=0,
            placement_count=0,
            effect_contract_placement_count=0,
            export_driven=False,
            masterpiece_score=0.0,
            masterpiece_candidate=False,
            passes=(),
            error=str(exc),
        )
