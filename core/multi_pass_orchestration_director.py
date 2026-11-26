from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from core.adaptive_emotional_storytelling_engine import AdaptiveEmotionalStorytellingEngine
from core.autonomous_masterpiece_evaluator import AutonomousMasterpieceEvaluator
from core.autonomous_render_validation_engine import AutonomousRenderValidationEngine
from core.composition_governor import CompositionGovernor
from core.choreography_correction_loop import ChoreographyCorrectionLoop
from core.intent_graph import IntentGraph
from core.iterative_quality_convergence import IterativeQualityConvergence
from core.live_audience_energy_engine import LiveAudienceEnergyEngine
from core.sequence_memory_engine import SequenceMemoryEngine
from core.show_identity_engine import ShowIdentityEngine
from core.spatial_choreography_engine import SpatialChoreographyEngine
from core.visual_cinematography_engine import VisualCinematographyEngine
from core.canonical_timeline_orchestrator import CanonicalTimelineOrchestrator, MusicalContext


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
        self.governor = CompositionGovernor()
        self.correction = ChoreographyCorrectionLoop()
        self.render_validator = AutonomousRenderValidationEngine()
        self.convergence = IterativeQualityConvergence(governor=self.governor, correction_loop=self.correction)
        self.masterpiece = AutonomousMasterpieceEvaluator(governor=self.governor, memory_engine=self.memory)

    def direct_music(self, music: MusicalContext) -> DirectedOrchestrationResult:
        return self._direct(self.timeline.from_music(music), live=True)

    def direct(self, graph: IntentGraph) -> DirectedOrchestrationResult:
        return self._direct(self.timeline.orchestrate(graph))

    def _direct(self, graph: IntentGraph, *, live: bool = False) -> DirectedOrchestrationResult:
        passes: list[OrchestrationPassResult] = []
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

        if live:
            graph, validation = self._validate_live_plan(graph)
            passes.append(OrchestrationPassResult("intent_render_validation", validation))
        else:
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

    def _validate_live_plan(self, graph: IntentGraph) -> tuple[IntentGraph, dict[str, Any]]:
        before = self.render_validator.validate(graph)
        after = before
        actions: tuple[str, ...] = ()
        accepted = False
        if before.issues:
            attempt = self.correction.run(graph)
            after = self.render_validator.validate(attempt.corrected_graph)
            actions = attempt.actions
            old_issues = Counter((issue.section, issue.category) for issue in before.issues)
            new_issues = Counter((issue.section, issue.category) for issue in after.issues)
            accepted = bool(actions and new_issues < old_issues)
            if accepted:
                graph = attempt.corrected_graph
        return graph, {
            "scope": "intent_simulation",
            "iterations": int(bool(before.issues)),
            "correction_accepted": accepted,
            "actions": list(actions),
            "before": before.to_dict(),
            "candidate": after.to_dict(),
        }

    @staticmethod
    def _pass(name: str, graph: IntentGraph) -> OrchestrationPassResult:
        return OrchestrationPassResult(
            pass_name=name,
            metadata={
                "intent_count": len(graph.intents),
                "sections": graph.ordered_sections(),
            },
        )
