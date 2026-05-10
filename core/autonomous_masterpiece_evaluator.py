from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.composition_governor import CompositionGovernor
from core.intent_graph import IntentGraph
from core.sequence_memory_engine import SequenceMemoryEngine


@dataclass(frozen=True)
class MasterpieceDimension:
    category: str
    score: float
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "score": self.score,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True)
class MasterpieceEvaluation:
    overall_score: float
    masterpiece_threshold: float
    masterpiece_candidate: bool
    dimensions: tuple[MasterpieceDimension, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "masterpiece_threshold": self.masterpiece_threshold,
            "masterpiece_candidate": self.masterpiece_candidate,
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
        }


class AutonomousMasterpieceEvaluator:
    """Grades cinematic sequence quality beyond basic correctness."""

    def __init__(
        self,
        *,
        masterpiece_threshold: float = 0.94,
        governor: CompositionGovernor | None = None,
        memory_engine: SequenceMemoryEngine | None = None,
    ):
        self.masterpiece_threshold = masterpiece_threshold
        self.governor = governor or CompositionGovernor()
        self.memory_engine = memory_engine or SequenceMemoryEngine()

    def evaluate(self, graph: IntentGraph) -> MasterpieceEvaluation:
        report = self.governor.evaluate(graph)
        memory = self.memory_engine.analyze(graph)

        dimensions = (
            self._memorability_dimension(memory),
            self._emotional_clarity_dimension(graph),
            self._motif_payoff_dimension(memory),
            self._visual_fatigue_dimension(graph),
            self._signature_identity_dimension(graph),
            self._cinematic_pacing_dimension(report.overall_score),
        )

        overall = round(sum(dimension.score for dimension in dimensions) / len(dimensions), 4)

        return MasterpieceEvaluation(
            overall_score=overall,
            masterpiece_threshold=self.masterpiece_threshold,
            masterpiece_candidate=overall >= self.masterpiece_threshold,
            dimensions=dimensions,
        )

    def _memorability_dimension(self, memory) -> MasterpieceDimension:
        motif_count = len(memory.motifs)
        recurring_motion_count = len(memory.recurring_motions)
        score = min(1.0, 0.35 + motif_count * 0.08 + recurring_motion_count * 0.03)

        return MasterpieceDimension(
            category="memorability",
            score=round(score, 4),
            reasoning="Measures persistent motif reuse and recognizable motion language.",
        )

    def _emotional_clarity_dimension(self, graph: IntentGraph) -> MasterpieceDimension:
        energies = [intent.emotional_energy for intent in graph]

        if not energies:
            score = 0.0
        else:
            spread = max(energies) - min(energies)
            score = min(1.0, 0.45 + spread * 0.55)

        return MasterpieceDimension(
            category="emotional_clarity",
            score=round(score, 4),
            reasoning="Measures emotional contrast and progression throughout the sequence.",
        )

    def _motif_payoff_dimension(self, memory) -> MasterpieceDimension:
        if not memory.motifs:
            score = 0.25
        else:
            average_callback = sum(m.callback_strength for m in memory.motifs) / len(memory.motifs)
            score = min(1.0, average_callback * 1.05)

        return MasterpieceDimension(
            category="motif_payoff",
            score=round(score, 4),
            reasoning="Measures recurring thematic callbacks and payoff strength.",
        )

    def _visual_fatigue_dimension(self, graph: IntentGraph) -> MasterpieceDimension:
        densities = [intent.density_budget for intent in graph]

        if not densities:
            score = 0.0
        else:
            average_density = sum(densities) / len(densities)
            score = max(0.0, 1.0 - max(0.0, average_density - 0.55) * 1.2)

        return MasterpieceDimension(
            category="visual_fatigue",
            score=round(score, 4),
            reasoning="Rewards restraint and reduced visual exhaustion.",
        )

    def _signature_identity_dimension(self, graph: IntentGraph) -> MasterpieceDimension:
        signature_hits = 0
        total = 0

        for intent in graph:
            total += 1
            motions = {motion.value for motion in intent.motion_vocabulary}
            if {"helix_spiral", "orbital"}.intersection(motions):
                signature_hits += 1

        score = 0.0 if total == 0 else signature_hits / total

        return MasterpieceDimension(
            category="signature_identity",
            score=round(score, 4),
            reasoning="Measures recognizable Helix choreography language consistency.",
        )

    def _cinematic_pacing_dimension(self, composition_score: float) -> MasterpieceDimension:
        score = min(1.0, composition_score * 1.08)

        return MasterpieceDimension(
            category="cinematic_pacing",
            score=round(score, 4),
            reasoning="Measures pacing quality, escalation discipline, and orchestration flow.",
        )
