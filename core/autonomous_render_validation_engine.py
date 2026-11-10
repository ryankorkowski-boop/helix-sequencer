from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.choreography_intent import ChoreographyIntent
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class RenderValidationIssue:
    category: str
    severity: float
    section: str
    description: str
    suggested_fix: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "section": self.section,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True)
class RenderValidationResult:
    passed: bool
    readability_score: float
    cinematic_score: float
    issues: tuple[RenderValidationIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "readability_score": self.readability_score,
            "cinematic_score": self.cinematic_score,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class AutonomousRenderValidationEngine:
    """Simulates cinematic readability validation before sequence export."""

    def validate(self, graph: IntentGraph) -> RenderValidationResult:
        issues: list[RenderValidationIssue] = []

        readability = 1.0
        cinematic = 1.0

        for intent in graph:
            issues.extend(self._evaluate_intent(intent))

        for issue in issues:
            readability -= issue.severity * 0.18
            cinematic -= issue.severity * 0.12

        readability = round(max(0.0, readability), 4)
        cinematic = round(max(0.0, cinematic), 4)

        return RenderValidationResult(
            passed=readability >= 0.75 and cinematic >= 0.78,
            readability_score=readability,
            cinematic_score=cinematic,
            issues=tuple(issues),
        )

    def auto_repair(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()

        for intent in graph:
            repaired = intent

            if intent.density_budget > 0.82:
                repaired = repaired.__class__(
                    **{
                        **repaired.__dict__,
                        "density_budget": 0.72,
                    }
                )

            if len(intent.motion_vocabulary) > 5:
                repaired = repaired.__class__(
                    **{
                        **repaired.__dict__,
                        "motion_vocabulary": repaired.motion_vocabulary[:4],
                    }
                )

            output.add_intent(
                repaired.__class__(
                    **{
                        **repaired.__dict__,
                        "metadata": {
                            **dict(repaired.metadata),
                            "render_validation_repaired": True,
                        },
                    }
                )
            )

        return output

    def _evaluate_intent(self, intent: ChoreographyIntent) -> list[RenderValidationIssue]:
        issues: list[RenderValidationIssue] = []

        if intent.density_budget > 0.88:
            issues.append(
                RenderValidationIssue(
                    category="visual_overcompression",
                    severity=0.9,
                    section=intent.section,
                    description="Visual density likely exceeds cinematic readability.",
                    suggested_fix="Reduce simultaneous active regions and pacing density.",
                )
            )

        if len(intent.motion_vocabulary) > 6:
            issues.append(
                RenderValidationIssue(
                    category="motion_conflict",
                    severity=0.72,
                    section=intent.section,
                    description="Too many concurrent motion languages competing for focus.",
                    suggested_fix="Reduce overlapping motion vocabulary.",
                )
            )

        if intent.intensity > 0.96 and intent.density_budget > 0.8:
            issues.append(
                RenderValidationIssue(
                    category="focal_collision",
                    severity=0.84,
                    section=intent.section,
                    description="Multiple focal regions likely collide during payoff moments.",
                    suggested_fix="Introduce dominance hierarchy and negative space.",
                )
            )

        if intent.emotional_energy > 0.95 and intent.section.lower().startswith("verse"):
            issues.append(
                RenderValidationIssue(
                    category="emotional_burnout",
                    severity=0.58,
                    section=intent.section,
                    description="Emotional escalation occurs too early in sequence progression.",
                    suggested_fix="Reserve emotional payoff for chorus or finale sections.",
                )
            )

        return issues
