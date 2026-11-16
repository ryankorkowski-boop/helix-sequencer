"""Deterministic, non-destructive diagnostics for competing choreography intents.

This module does not modify effect timing, targeting, or drummer behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class ArbitrationConflict:
    first_id: str
    second_id: str
    start: float
    end: float
    reason: str


def audit_intent_conflicts(graph: IntentGraph) -> tuple[ArbitrationConflict, ...]:
    """Find overlapping same-target motion intents without altering the graph.

    ALL is treated as potentially sharing a target with any family. Separate
    named performer props are exempt from target-family collision detection.
    """
    conflicts: list[ArbitrationConflict] = []
    for overlap in graph.detect_overlaps():
        left, right = overlap.left, overlap.right
        if left.dominant_prop and right.dominant_prop and left.dominant_prop != right.dominant_prop:
            continue
        a = {target.value for target in left.target_families}
        b = {target.value for target in right.target_families}
        if not (a & b or "all" in a or "all" in b):
            continue
        left_roles = {role.value for role in left.layer_roles}
        right_roles = {role.value for role in right.layer_roles}
        if "motion" not in left_roles or "motion" not in right_roles:
            continue
        conflicts.append(ArbitrationConflict(
            first_id=left.intent_id,
            second_id=right.intent_id,
            start=overlap.overlap_start,
            end=overlap.overlap_end,
            reason="overlapping_motion_same_target",
        ))
    return tuple(conflicts)


def arbitration_diagnostics(graph: IntentGraph) -> dict:
    conflicts = audit_intent_conflicts(graph)
    return {
        "schema_version": 1,
        "mode": "observe_only",
        "intent_count": len(graph),
        "motion_conflict_count": len(conflicts),
        "motion_conflicts": [vars(item).copy() for item in conflicts],
    }
