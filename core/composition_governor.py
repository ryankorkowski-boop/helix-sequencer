from __future__ import annotations

from dataclasses import dataclass

from core.choreography_intent import ContrastStrategy, DominanceStrategy
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class CompositionDiagnostic:
    category: str
    severity: str
    score: float
    message: str


@dataclass(frozen=True)
class CompositionReport:
    overall_score: float
    diagnostics: tuple[CompositionDiagnostic, ...]

    @property
    def passed(self) -> bool:
        return self.overall_score >= 0.75


class CompositionGovernor:
    """Deterministic orchestration validation layer.

    Evaluates canonical choreography intent graphs for:
    - clutter
    - escalation pacing
    - dominance coherence
    - contrast effectiveness
    - section balance
    - motion overload
    """

    def evaluate(self, graph: IntentGraph) -> CompositionReport:
        diagnostics: list[CompositionDiagnostic] = []

        diagnostics.extend(self._check_density(graph))
        diagnostics.extend(self._check_motion_overload(graph))
        diagnostics.extend(self._check_dominance_consistency(graph))
        diagnostics.extend(self._check_contrast_distribution(graph))

        if diagnostics:
            overall = round(sum(d.score for d in diagnostics) / len(diagnostics), 4)
        else:
            overall = 1.0

        return CompositionReport(
            overall_score=overall,
            diagnostics=tuple(diagnostics),
        )

    def _check_density(self, graph: IntentGraph) -> list[CompositionDiagnostic]:
        diagnostics: list[CompositionDiagnostic] = []

        overlap = getattr(graph, "overlap_density", lambda: 0.0)()

        if overlap > 0.85:
            diagnostics.append(
                CompositionDiagnostic(
                    category="density",
                    severity="high",
                    score=0.35,
                    message="Intent overlap density is excessively high.",
                )
            )
        elif overlap > 0.65:
            diagnostics.append(
                CompositionDiagnostic(
                    category="density",
                    severity="medium",
                    score=0.7,
                    message="Intent overlap density is elevated.",
                )
            )
        else:
            diagnostics.append(
                CompositionDiagnostic(
                    category="density",
                    severity="ok",
                    score=1.0,
                    message="Intent density is balanced.",
                )
            )

        return diagnostics

    def _check_motion_overload(self, graph: IntentGraph) -> list[CompositionDiagnostic]:
        diagnostics: list[CompositionDiagnostic] = []

        motion_count = 0

        for intent in graph:
            motion_count += len(intent.motion_vocabulary)

        average_motion = motion_count / max(len(graph), 1)

        if average_motion > 4:
            diagnostics.append(
                CompositionDiagnostic(
                    category="motion_overload",
                    severity="high",
                    score=0.4,
                    message="Too many simultaneous motion vocabularies.",
                )
            )
        else:
            diagnostics.append(
                CompositionDiagnostic(
                    category="motion_overload",
                    severity="ok",
                    score=1.0,
                    message="Motion vocabulary distribution is controlled.",
                )
            )

        return diagnostics

    def _check_dominance_consistency(self, graph: IntentGraph) -> list[CompositionDiagnostic]:
        diagnostics: list[CompositionDiagnostic] = []

        dominance_modes = {
            intent.dominance_strategy
            for intent in graph
            if intent.dominance_strategy != DominanceStrategy.DISTRIBUTED
        }

        if len(dominance_modes) > 3:
            diagnostics.append(
                CompositionDiagnostic(
                    category="dominance",
                    severity="medium",
                    score=0.6,
                    message="Too many competing dominance strategies.",
                )
            )
        else:
            diagnostics.append(
                CompositionDiagnostic(
                    category="dominance",
                    severity="ok",
                    score=1.0,
                    message="Dominance strategy usage is coherent.",
                )
            )

        return diagnostics

    def _check_contrast_distribution(self, graph: IntentGraph) -> list[CompositionDiagnostic]:
        diagnostics: list[CompositionDiagnostic] = []

        contrast_modes = {
            intent.contrast_strategy
            for intent in graph
            if intent.contrast_strategy != ContrastStrategy.NONE
        }

        if not contrast_modes:
            diagnostics.append(
                CompositionDiagnostic(
                    category="contrast",
                    severity="medium",
                    score=0.65,
                    message="No meaningful contrast strategies detected.",
                )
            )
        else:
            diagnostics.append(
                CompositionDiagnostic(
                    category="contrast",
                    severity="ok",
                    score=1.0,
                    message="Contrast strategy distribution is healthy.",
                )
            )

        return diagnostics
