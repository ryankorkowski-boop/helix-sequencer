from __future__ import annotations

from dataclasses import dataclass

from core.choreography_correction_loop import (
    ChoreographyCorrectionLoop,
    CorrectionLoopResult,
)
from core.composition_governor import CompositionGovernor
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class QualityConvergenceResult:
    initial_score: float
    final_score: float
    iterations: int
    converged: bool
    final_graph: IntentGraph
    history: tuple[CorrectionLoopResult, ...]

    @property
    def improved(self) -> bool:
        return self.final_score >= self.initial_score


class IterativeQualityConvergence:
    """Runs autonomous orchestration refinement until quality stabilizes."""

    def __init__(
        self,
        *,
        target_score: float = 0.92,
        max_iterations: int = 5,
        minimum_delta: float = 0.015,
        governor: CompositionGovernor | None = None,
        correction_loop: ChoreographyCorrectionLoop | None = None,
    ):
        self.target_score = target_score
        self.max_iterations = max_iterations
        self.minimum_delta = minimum_delta
        self.governor = governor or CompositionGovernor()
        self.correction_loop = correction_loop or ChoreographyCorrectionLoop(self.governor)

    def converge(self, graph: IntentGraph) -> QualityConvergenceResult:
        history: list[CorrectionLoopResult] = []
        current_graph = graph
        initial_report = self.governor.evaluate(graph)
        previous_score = initial_report.overall_score
        converged = previous_score >= self.target_score

        for _ in range(self.max_iterations):
            if converged:
                break

            result = self.correction_loop.run(current_graph)
            history.append(result)

            current_graph = result.corrected_graph
            current_score = result.corrected_report.overall_score
            delta = current_score - previous_score

            if current_score >= self.target_score:
                converged = True
                previous_score = current_score
                break

            if delta < self.minimum_delta:
                previous_score = current_score
                break

            previous_score = current_score

        return QualityConvergenceResult(
            initial_score=initial_report.overall_score,
            final_score=previous_score,
            iterations=len(history),
            converged=converged,
            final_graph=current_graph,
            history=tuple(history),
        )
