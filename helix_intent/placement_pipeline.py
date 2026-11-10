from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from helix_intent.layout_candidates import (
    candidates_from_layout_intelligence,
    candidates_from_parsed_layout,
    merge_candidates,
)
from helix_intent.placement_planner import PlacementCandidate, plan_prop_effect_intents
from helix_intent.placement_quality import score_placement_plan
from helix_intent.placement_report import PlacementExportReport, build_placement_export_report, write_placement_export_report
from helix_intent.placement_validator import validate_placement_plan
from helix_intent.visual_intent import VisualIntent


def build_placement_plan(
    *,
    visual_intents: Iterable[VisualIntent],
    parsed_layout: Any | None = None,
    layout_intelligence: Mapping[str, Any] | None = None,
    extra_candidates: Iterable[PlacementCandidate] | None = None,
) -> PlacementExportReport:
    """Build an inspectable placement plan without rendering xLights effects.

    This function is the safe orchestration layer for placement logic. It connects
    layout-derived candidates to high-level visual intents and emits an exportable
    report that can be reviewed before the heavy effect engine writes XML.
    """
    candidate_sets: list[list[PlacementCandidate]] = []
    if parsed_layout is not None:
        candidate_sets.append(candidates_from_parsed_layout(parsed_layout))
    if layout_intelligence is not None:
        candidate_sets.append(candidates_from_layout_intelligence(layout_intelligence))
    if extra_candidates is not None:
        candidate_sets.append(list(extra_candidates))

    candidates = merge_candidates(*candidate_sets) if candidate_sets else []
    intents = list(visual_intents)
    placements, planner_report = plan_prop_effect_intents(intents, candidates)
    provisional = build_placement_export_report(
        visual_intents=intents,
        candidates=candidates,
        prop_effect_intents=placements,
        planner_report=planner_report,
    )
    validation = validate_placement_plan(provisional.to_dict())
    with_validation = build_placement_export_report(
        visual_intents=intents,
        candidates=candidates,
        prop_effect_intents=placements,
        planner_report=planner_report,
        validation_report=validation.to_dict(),
    )
    quality = score_placement_plan(with_validation.to_dict())
    return build_placement_export_report(
        visual_intents=intents,
        candidates=candidates,
        prop_effect_intents=placements,
        planner_report=planner_report,
        validation_report=validation.to_dict(),
        quality_report=quality.to_dict(),
    )


def build_and_write_placement_plan(
    *,
    visual_intents: Iterable[VisualIntent],
    output_path: str | Path,
    parsed_layout: Any | None = None,
    layout_intelligence: Mapping[str, Any] | None = None,
    extra_candidates: Iterable[PlacementCandidate] | None = None,
) -> Path:
    report = build_placement_plan(
        visual_intents=visual_intents,
        parsed_layout=parsed_layout,
        layout_intelligence=layout_intelligence,
        extra_candidates=extra_candidates,
    )
    return write_placement_export_report(report, output_path)
