from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.adaptive_emotional_storytelling_engine import AdaptiveEmotionalStorytellingEngine
from core.autonomous_masterpiece_evaluator import AutonomousMasterpieceEvaluator
from core.choreography_correction_loop import ChoreographyCorrectionLoop
from core.intent_graph import IntentGraph
from core.iterative_quality_convergence import IterativeQualityConvergence
from core.live_audience_energy_engine import LiveAudienceEnergyEngine
from core.sequence_memory_engine import SequenceMemoryEngine
from core.show_identity_engine import ShowIdentityEngine
from core.spatial_choreography_engine import SpatialChoreographyEngine
from core.visual_cinematography_engine import VisualCinematographyEngine
from core.canonical_timeline_orchestrator import CanonicalTimelineOrchestrator


@dataclass(frozen=True)
class OrchestrationPassResult:
    pass_name: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DirectedOrchestrationResult:
    final_graph: IntentGraph
    masterpiece_score: float
    masterpiece_candidate: bool
    passes: tuple[OrchestrationPassResult, ...]


class MultiPassOrchestrationDirector:
    """Central deterministic choreography authority for Helix orchestration."""

    def __init__(self):
        self.timeline = CanonicalTimelineOrchestrator()
        self.memory = SequenceMemoryEngine()
        self.storytelling = AdaptiveEmotionalStorytellingEngine()
        self.cinematography = VisualCinematographyEngine()
        self.spatial = SpatialChoreographyEngine()
        self.signature = ShowIdentityEngine()
        self.audience = LiveAudienceEnergyEngine()
        self.correction = ChoreographyCorrectionLoop()
        self.convergence = IterativeQualityConvergence()
        self.masterpiece = AutonomousMasterpieceEvaluator()

    def direct(self, graph: IntentGraph) -> DirectedOrchestrationResult:
        passes: list[OrchestrationPassResult] = []

        graph = self.timeline.orchestrate(graph)
        passes.append(self._pass("timeline_orchestration", graph))

        graph = self.memory.apply_memory(graph)
        passes.append(self._pass("sequence_memory", graph))

        graph = self.storytelling.orchestrate(graph)
        passes.append(self._pass("emotional_storytelling", graph))

        graph = self.cinematography.orchestrate(graph)
        passes.append(self._pass("visual_cinematography", graph))

        graph = self.spatial.orchestrate(graph)
        passes.append(self._pass("spatial_choreography", graph))

        graph = self.signature.orchestrate(graph)
        passes.append(self._pass("signature_identity", graph))

        graph = self.audience.orchestrate(graph)
        passes.append(self._pass("audience_energy", graph))

        convergence = self.convergence.converge(graph)
        graph = convergence.final_graph

        passes.append(
            OrchestrationPassResult(
                pass_name="quality_convergence",
                metadata={
                    "iterations": convergence.iterations,
                    "improved": convergence.improved,
                    "converged": convergence.converged,
                    "final_score": convergence.final_score,
                },
            )
        )

        masterpiece = self.masterpiece.evaluate(graph)

        passes.append(
            OrchestrationPassResult(
                pass_name="masterpiece_evaluation",
                metadata=masterpiece.to_dict(),
            )
        )

        return DirectedOrchestrationResult(
            final_graph=graph,
            masterpiece_score=masterpiece.overall_score,
            masterpiece_candidate=masterpiece.masterpiece_candidate,
            passes=tuple(passes),
        )

    @staticmethod
    def _pass(name: str, graph: IntentGraph) -> OrchestrationPassResult:
        return OrchestrationPassResult(
            pass_name=name,
            metadata={
                "intent_count": len(graph.intents),
                "sections": graph.ordered_sections(),
            },
        )
