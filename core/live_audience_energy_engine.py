from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.choreography_intent import ChoreographyIntent, MotionVocabulary
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class AudienceEnergyState:
    section: str
    crowd_energy: float
    anticipation_pressure: float
    singalong_probability: float
    impact_expectation: float
    recovery_window: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "crowd_energy": self.crowd_energy,
            "anticipation_pressure": self.anticipation_pressure,
            "singalong_probability": self.singalong_probability,
            "impact_expectation": self.impact_expectation,
            "covery_window": self.recovery_window,
        }


class LiveAudienceEnergyEngine:
    """Models perceived audience energy and adapts choreography pacing."""

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()
        states = self._states_for_graph(graph)

        for intent in graph:
            state = states.get(intent.section)
            if state is None:
                output.add_intent(intent)
                continue

            output.add_intent(self._apply_state(intent, state))

        return output

    def _states_for_graph(self, graph: IntentGraph) -> dict[str, AudienceEnergyState]:
        states: dict[str, AudienceEnergyState] = {}

        for index, section in enumerate(graph.ordered_sections()):
            lowered = section.lower()
            progression = index / max(1, len(graph.ordered_sections()) - 1)

            if "intro" in lowered:
                states[section] = AudienceEnergyState(
                    section=section,
                    crowd_energy=0.28,
                    anticipation_pressure=0.72,
                    singalong_probability=0.1,
                    impact_expectation=0.25,
                    recovery_window=0.85,
                )
            elif "verse" in lowered:
                states[section] = AudienceEnergyState(
                    section=section,
                    crowd_energy=0.46,
                    anticipation_pressure=0.58,
                    singalong_probability=0.4,
                    impact_expectation=0.48,
                    recovery_window=0.55,
                )
            elif "build" in lowered or "pre" in lowered:
                states[section] = AudienceEnergyState(
                    section=section,
                    crowd_energy=0.74,
                    anticipation_pressure=0.92,
                    singalong_probability=0.66,
                    impact_expectation=0.86,
                    recovery_window=0.2,
                )
            elif "chorus" in lowered:
                states[section] = AudienceEnergyState(
                    section=section,
                    crowd_energy=0.9,
                    anticipation_pressure=0.45,
                    singalong_probability=0.94,
                    impact_expectation=0.82,
                    recovery_window=0.12,
                )
            elif "drop" in lowered or "final" in lowered:
                states[section] = AudienceEnergyState(
                    section=section,
                    crowd_energy=1.0,
                    anticipation_pressure=0.08,
                    singalong_probability=0.98,
                    impact_expectation=1.0,
                    recovery_window=0.0,
                )
            else:
                states[section] = AudienceEnergyState(
                    section=section,
                    crowd_energy=round(0.35 + progression * 0.5, 4),
                    anticipation_pressure=round(max(0.0, 0.7 - progression * 0.4), 4),
                    singalong_probability=round(0.25 + progression * 0.55, 4),
                    impact_expectation=round(0.3 + progression * 0.6, 4),
                    recovery_window=round(max(0.0, 0.6 - progression * 0.4), 4),
                )

        return states

    def _apply_state(
        self,
        intent: ChoreographyIntent,
        state: AudienceEnergyState,
    ) -> ChoreographyIntent:
        vocabulary = intent.motion_vocabulary

        if state.crowd_energy >= 0.85 and MotionVocabulary.IMPACT not in vocabulary:
            vocabulary = (*vocabulary, MotionVocabulary.IMPACT)

        if state.singalong_probability >= 0.8 and MotionVocabulary.PULSE not in vocabulary:
            vocabulary = (*vocabulary, MotionVocabulary.PULSE)

        density_scale = 1.0 - state.recovery_window * 0.25

        return intent.__class__(
            **{
                **intent.__dict__,
                "motion_vocabulary": tuple(dict.fromkeys(vocabulary)),
                "emotional_energy": round(min(1.0, intent.emotional_energy * 0.7 + state.crowd_energy * 0.3), 4),
                "density_budget": round(max(0.08, intent.density_budget * density_scale), 4),
                "metadata": {
                    **dict(intent.metadata),
                    "audience_energy_state": state.to_dict(),
                },
            }
        )
