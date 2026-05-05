from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from helix_intent.placement_planner import PlacementCandidate, PlacementPlanReport
from helix_intent.visual_intent import PropEffectIntent, VisualIntent


@dataclass(frozen=True)
class PlacementExportReport:
    schema: str = "helix.placement_plan.v1"
    visual_intents: list[dict[str, Any]] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    prop_effect_intents: list[dict[str, Any]] = field(default_factory=list)
    planner_report: dict[str, Any] = field(default_factory=dict)
    validation_report: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def _candidate_to_dict(candidate: PlacementCandidate) -> dict[str, Any]:
    return {
        "prop_name": candidate.prop_name,
        "role": candidate.role,
        "family": candidate.family,
        "priority": candidate.priority,
    }


def _warnings_for_report(
    *,
    intents: list[VisualIntent],
    candidates: list[PlacementCandidate],
    placements: list[PropEffectIntent],
    planner_report: PlacementPlanReport,
    validation_report: Mapping[str, Any] | None = None,
) -> list[str]:
    warnings: list[str] = []
    if not intents:
        warnings.append("No visual intents were provided.")
    if not candidates:
        warnings.append("No placement candidates were provided.")
    if planner_report.rejected_intents:
        warnings.append(f"Rejected intents: {', '.join(planner_report.rejected_intents)}")
    if planner_report.capped_density_intents:
        warnings.append(f"Density-capped intents: {', '.join(planner_report.capped_density_intents)}")
    if intents and not placements:
        warnings.append("Visual intents produced no prop-effect intents.")
    if validation_report and not bool(validation_report.get("passed", True)):
        warnings.append("Placement validation did not pass.")
    return warnings


def build_placement_export_report(
    *,
    visual_intents: Iterable[VisualIntent],
    candidates: Iterable[PlacementCandidate],
    prop_effect_intents: Iterable[PropEffectIntent],
    planner_report: PlacementPlanReport,
    validation_report: Mapping[str, Any] | None = None,
) -> PlacementExportReport:
    intents = list(visual_intents)
    candidate_list = list(candidates)
    placement_list = list(prop_effect_intents)
    validation_payload = dict(validation_report or {})
    return PlacementExportReport(
        visual_intents=[intent.to_dict() for intent in intents],
        candidates=[_candidate_to_dict(candidate) for candidate in candidate_list],
        prop_effect_intents=[placement.to_dict() for placement in placement_list],
        planner_report=planner_report.to_dict(),
        validation_report=validation_payload,
        warnings=_warnings_for_report(
            intents=intents,
            candidates=candidate_list,
            placements=placement_list,
            planner_report=planner_report,
            validation_report=validation_payload,
        ),
    )


def write_placement_export_report(report: PlacementExportReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.to_json() + "\n", encoding="utf-8")
    return path
