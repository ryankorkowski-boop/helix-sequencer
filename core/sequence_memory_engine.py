from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.choreography_intent import ChoreographyIntent, MotionVocabulary
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class SequenceMotif:
    motif_id: str
    source_section: str
    dominant_prop: str
    motion_vocabulary: tuple[MotionVocabulary, ...]
    palette_family: Any
    emotional_energy: float
    callback_strength: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "motif_id": self.motif_id,
            "source_section": self.source_section,
            "dominant_prop": self.dominant_prop,
            "motion_vocabulary": [motion.value for motion in self.motion_vocabulary],
            "palette_family": getattr(self.palette_family, "value", str(self.palette_family)),
            "emotional_energy": self.emotional_energy,
            "callback_strength": self.callback_strength,
        }


@dataclass(frozen=True)
class SequenceMemorySnapshot:
    motifs: tuple[SequenceMotif, ...]
    recurring_props: tuple[str, ...]
    recurring_motions: tuple[str, ...]
    emotional_arc: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "motifs": [motif.to_dict() for motif in self.motifs],
            "recurring_props": list(self.recurring_props),
            "recurring_motions": list(self.recurring_motions),
            "emotional_arc": list(self.emotional_arc),
        }


class SequenceMemoryEngine:
    """Builds persistent visual memory across an entire sequence."""

    def analyze(self, graph: IntentGraph) -> SequenceMemorySnapshot:
        motifs: list[SequenceMotif] = []
        recurring_props: dict[str, int] = {}
        recurring_motions: dict[str, int] = {}
        emotional_arc: list[float] = []

        for index, intent in enumerate(graph):
            emotional_arc.append(intent.emotional_energy)

            if intent.dominant_prop:
                recurring_props[intent.dominant_prop] = recurring_props.get(intent.dominant_prop, 0) + 1

            for motion in intent.motion_vocabulary:
                recurring_motions[motion.value] = recurring_motions.get(motion.value, 0) + 1

            if self._is_motif_candidate(intent):
                motifs.append(
                    SequenceMotif(
                        motif_id=f"motif_{index}_{intent.section}",
                        source_section=intent.section,
                        dominant_prop=intent.dominant_prop or "whole_house",
                        motion_vocabulary=intent.motion_vocabulary,
                        palette_family=intent.palette_family,
                        emotional_energy=intent.emotional_energy,
                        callback_strength=self._callback_strength(intent, index, len(graph.intents)),
                    )
                )

        return SequenceMemorySnapshot(
            motifs=tuple(motifs),
            recurring_props=tuple(sorted(recurring_props, key=recurring_props.get, reverse=True)),
            recurring_motions=tuple(sorted(recurring_motions, key=recurring_motions.get, reverse=True)),
            emotional_arc=tuple(round(value, 4) for value in emotional_arc),
        )

    def apply_memory(self, graph: IntentGraph) -> IntentGraph:
        snapshot = self.analyze(graph)
        output = IntentGraph()

        motif_lookup = {motif.source_section: motif for motif in snapshot.motifs}

        for intent in graph:
            motif = motif_lookup.get(intent.section)
            if motif is None:
                output.add_intent(intent)
                continue

            output.add_intent(
                intent.__class__(
                    **{
                        **intent.__dict__,
                        "metadata": {
                            **dict(intent.metadata),
                            "sequence_memory": snapshot.to_dict(),
                            "motif_callback": motif.to_dict(),
                        },
                    }
                )
            )

        return output

    @staticmethod
    def _is_motif_candidate(intent: ChoreographyIntent) -> bool:
        return (
            intent.emotional_energy >= 0.75
            or len(intent.motion_vocabulary) >= 2
            or intent.escalation_phase >= 2
        )

    @staticmethod
    def _callback_strength(intent: ChoreographyIntent, index: int, total: int) -> float:
        progression = index / max(total - 1, 1)
        return round(min(1.0, intent.emotional_energy * 0.7 + progression * 0.3), 4)
