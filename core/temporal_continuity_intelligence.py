from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.choreography_intent import ChoreographyIntent, MotionVocabulary
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class TemporalContinuityFrame:
    source_section: str
    destination_section: str
    continuity_score: float
    transition_style: str
    momentum_transfer: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_section": self.source_section,
            "destination_section": self.destination_section,
            "continuity_score": self.continuity_score,
            "transition_style": self.transition_style,
            "momentum_transfer": self.momentum_transfer,
        }


class TemporalContinuityIntelligence:
    """Maintains continuity and motion phrasing across song sections."""

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()
        intents = list(graph)

        for index, intent in enumerate(intents):
            nxt = intents[index + 1] if index + 1 < len(intents) else None
            frame = self._frame(intent, nxt)
            output.add_intent(self._apply(intent, frame))

        return output

    def _frame(
        self,
        current: ChoreographyIntent,
        nxt: ChoreographyIntent | None,
    ) -> TemporalContinuityFrame | None:
        if nxt is None:
            return None

        shared = len(set(current.motion_vocabulary).intersection(set(nxt.motion_vocabulary)))
        continuity = round(min(1.0, 0.4 + shared * 0.15), 4)

        if MotionVocabulary.ORBITAL in current.motion_vocabulary:
            transition = "orbital_bridge"
        elif current.intensity > 0.8 and nxt.intensity > 0.8:
            transition = "impact_carryover"
        else:
            transition = "smooth_resolution"

        return TemporalContinuityFrame(
            source_section=current.section,
            destination_section=nxt.section,
            continuity_score=continuity,
            transition_style=transition,
            momentum_transfer=round((current.intensity + nxt.intensity) / 2.0, 4),
        )

    def _apply(
        self,
        intent: ChoreographyIntent,
        frame: TemporalContinuityFrame | None,
    ) -> ChoreographyIntent:
        if frame is None:
            return intent

        vocabulary = list(intent.motion_vocabulary)

        if frame.transition_style == "orbital_bridge":
            if MotionVocabulary.ORBITAL not in vocabulary:
                vocabulary.append(MotionVocabulary.ORBITAL)

        if frame.momentum_transfer >= 0.75:
            if MotionVocabulary.SWEEP not in vocabulary:
                vocabulary.append(MotionVocabulary.SWEEP)

        return intent.__class__(
            **{
                **intent.__dict__,
                "motion_vocabulary": tuple(dict.fromkeys(vocabulary)),
                "metadata": {
                    **dict(intent.metadata),
                    "temporal_continuity": frame.to_dict(),
                },
            }
        )
