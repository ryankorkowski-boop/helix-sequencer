from __future__ import annotations

from dataclasses import dataclass, replace

from core.choreography_intent import ChoreographyIntent, ContrastStrategy
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class ChoreographyCorrectionReport:
    overall_score: float
    issue_count: int
    intent_count: int


@dataclass(frozen=True)
class ChoreographyCorrectionResult:
    original_graph: IntentGraph
    corrected_graph: IntentGraph
    original_report: ChoreographyCorrectionReport
    corrected_report: ChoreographyCorrectionReport
    actions: tuple[str, ...]

    @property
    def improved(self) -> bool:
        return self.corrected_report.overall_score >= self.original_report.overall_score and bool(self.actions)


class ChoreographyCorrectionLoop:
    """Deterministic cleanup pass for over-busy choreography intents."""

    max_motion_terms = 3
    max_density_budget = 0.75
    max_intensity = 0.9

    def run(self, graph: IntentGraph) -> ChoreographyCorrectionResult:
        original_report = self._score(graph)
        corrected_intents: list[ChoreographyIntent] = []
        actions: list[str] = []

        for intent in graph:
            updated = intent

            if len(updated.motion_vocabulary) > self.max_motion_terms:
                updated = replace(updated, motion_vocabulary=updated.motion_vocabulary[: self.max_motion_terms])
                actions.append(f"trim_motion_vocabulary:{intent.intent_id}")

            if updated.contrast_strategy == ContrastStrategy.NONE:
                updated = replace(updated, contrast_strategy=self._contrast_for(updated))
                actions.append(f"add_contrast:{intent.intent_id}")

            if updated.density_budget > self.max_density_budget:
                updated = replace(updated, density_budget=self.max_density_budget)
                actions.append(f"reduce_density:{intent.intent_id}")

            if updated.intensity > self.max_intensity:
                updated = replace(updated, intensity=self.max_intensity)
                actions.append(f"reduce_intensity:{intent.intent_id}")

            corrected_intents.append(updated)

        corrected_graph = IntentGraph(corrected_intents)
        corrected_report = self._score(corrected_graph)

        return ChoreographyCorrectionResult(
            original_graph=graph,
            corrected_graph=corrected_graph,
            original_report=original_report,
            corrected_report=corrected_report,
            actions=tuple(actions),
        )

    def _score(self, graph: IntentGraph) -> ChoreographyCorrectionReport:
        issues = 0
        for intent in graph:
            if len(intent.motion_vocabulary) > self.max_motion_terms:
                issues += len(intent.motion_vocabulary) - self.max_motion_terms
            if intent.contrast_strategy == ContrastStrategy.NONE:
                issues += 1
            if intent.density_budget > self.max_density_budget:
                issues += 1
            if intent.intensity > self.max_intensity:
                issues += 1
        score = max(0.0, round(1.0 - issues * 0.1, 4))
        return ChoreographyCorrectionReport(score, issues, len(graph))

    @staticmethod
    def _contrast_for(intent: ChoreographyIntent) -> ContrastStrategy:
        section = intent.section.lower()
        if section in {"drop", "breakdown"}:
            return ContrastStrategy.DARK_PRE_DROP
        if section in {"chorus", "post_chorus"}:
            return ContrastStrategy.ESCALATING_CHORUS
        if section == "verse":
            return ContrastStrategy.SPARSE_VERSE
        return ContrastStrategy.DENSE_SPARSE_ALTERNATION
