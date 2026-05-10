from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.composition_governor import CompositionGovernor
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class IntentTimelineRow:
    intent_id: str
    start: float
    end: float
    section: str
    style: str
    event_type: str
    focal_region: str
    dominant_prop: str | None
    motions: tuple[str, ...]
    density_budget: float


@dataclass(frozen=True)
class OrchestrationDiagnosticsSnapshot:
    timeline: tuple[IntentTimelineRow, ...]
    ordered_sections: tuple[str, ...]
    motion_summary: dict[str, int]
    dominance_summary: dict[str, int]
    section_summary: dict[str, int]
    composition_score: float
    composition_passed: bool
    diagnostics: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeline": [row.__dict__ for row in self.timeline],
            "ordered_sections": list(self.ordered_sections),
            "motion_summary": dict(self.motion_summary),
            "dominance_summary": dict(self.dominance_summary),
            "section_summary": dict(self.section_summary),
            "composition_score": self.composition_score,
            "composition_passed": self.composition_passed,
            "diagnostics": tuple(self.diagnostics),
        }


class GuiOrchestrationDiagnostics:
    """Builds GUI-friendly orchestration diagnostics from canonical intent.

    This module is read-only. It does not author choreography or mutate the
    intent graph. It prepares timeline, summary, and governor data for GUI
    panels and reports.
    """

    def __init__(self, governor: CompositionGovernor | None = None):
        self.governor = governor or CompositionGovernor()

    def build_snapshot(self, graph: IntentGraph) -> OrchestrationDiagnosticsSnapshot:
        report = self.governor.evaluate(graph)
        timeline = tuple(self._row_for_intent(intent) for intent in graph)

        return OrchestrationDiagnosticsSnapshot(
            timeline=timeline,
            ordered_sections=graph.ordered_sections(),
            motion_summary=self._motion_summary(graph),
            dominance_summary=self._dominance_summary(graph),
            section_summary={section: len(intents) for section, intents in graph.sections().items()},
            composition_score=report.overall_score,
            composition_passed=report.passed,
            diagnostics=tuple(diagnostic.__dict__ for diagnostic in report.diagnostics),
        )

    @staticmethod
    def _row_for_intent(intent) -> IntentTimelineRow:
        return IntentTimelineRow(
            intent_id=intent.intent_id,
            start=intent.start,
            end=intent.end,
            section=intent.section,
            style=intent.style,
            event_type=intent.event_type,
            focal_region=intent.focal_region,
            dominant_prop=intent.dominant_prop,
            motions=tuple(motion.value for motion in intent.motion_vocabulary),
            density_budget=intent.density_budget,
        )

    @staticmethod
    def _motion_summary(graph: IntentGraph) -> dict[str, int]:
        summary: dict[str, int] = {}
        for intent in graph:
            for motion in intent.motion_vocabulary:
                summary[motion.value] = summary.get(motion.value, 0) + 1
        return summary

    @staticmethod
    def _dominance_summary(graph: IntentGraph) -> dict[str, int]:
        summary: dict[str, int] = {}
        for intent in graph:
            key = intent.dominance_strategy.value
            summary[key] = summary.get(key, 0) + 1
        return summary
