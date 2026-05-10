from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.choreography_intent import (
    ChoreographyIntent,
    ContrastStrategy,
    MotionVocabulary,
)
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class EmotionalStoryBeat:
    section: str
    emotional_state: str
    tension: float
    restraint: float
    payoff_strength: float
    darkness_budget: float
    silence_budget: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "emotional_state": self.emotional_state,
            "tension": self.tension,
            "restraint": self.restraint,
            "payoff_strength": self.payoff_strength,
            "darkness_budget": self.darkness_budget,
            "silence_budget": self.silence_budget,
        }


class AdaptiveEmotionalStorytellingEngine:
    """Shapes cinematic emotional pacing across the sequence."""

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()
        beats = self._build_story_beats(graph)

        for intent in graph:
            beat = beats.get(intent.section)
            if beat is None:
                output.add_intent(intent)
                continue

            output.add_intent(self._apply_story_beat(intent, beat))

        return output

    def _build_story_beats(self, graph: IntentGraph) -> dict[str, EmotionalStoryBeat]:
        beats: dict[str, EmotionalStoryBeat] = {}
        ordered_sections = graph.ordered_sections()

        for index, section in enumerate(ordered_sections):
            lowered = section.lower()
            progression = index / max(len(ordered_sections) - 1, 1)

            if "intro" in lowered:
                beats[section] = EmotionalStoryBeat(
                    section=section,
                    emotional_state="anticipation",
                    tension=0.35,
                    restraint=0.85,
                    payoff_strength=0.15,
                    darkness_budget=0.65,
                    silence_budget=0.55,
                )
            elif "verse" in lowered:
                beats[section] = EmotionalStoryBeat(
                    section=section,
                    emotional_state="development",
                    tension=0.45,
                    restraint=0.7,
                    payoff_strength=0.25,
                    darkness_budget=0.45,
                    silence_budget=0.35,
                )
            elif "build" in lowered or "pre" in lowered:
                beats[section] = EmotionalStoryBeat(
                    section=section,
                    emotional_state="rising_tension",
                    tension=0.78,
                    restraint=0.45,
                    payoff_strength=0.55,
                    darkness_budget=0.35,
                    silence_budget=0.2,
                )
            elif "chorus" in lowered:
                beats[section] = EmotionalStoryBeat(
                    section=section,
                    emotional_state="release",
                    tension=0.65,
                    restraint=0.25,
                    payoff_strength=0.82,
                    darkness_budget=0.12,
                    silence_budget=0.08,
                )
            elif "drop" in lowered or "final" in lowered:
                beats[section] = EmotionalStoryBeat(
                    section=section,
                    emotional_state="maximum_payoff",
                    tension=0.92,
                    restraint=0.05,
                    payoff_strength=1.0,
                    darkness_budget=0.0,
                    silence_budget=0.0,
                )
            else:
                beats[section] = EmotionalStoryBeat(
                    section=section,
                    emotional_state="transition",
                    tension=round(0.4 + progression * 0.4, 4),
                    restraint=round(max(0.1, 0.8 - progression * 0.5), 4),
                    payoff_strength=round(0.2 + progression * 0.6, 4),
                    darkness_budget=round(max(0.0, 0.5 - progression * 0.3), 4),
                    silence_budget=round(max(0.0, 0.4 - progression * 0.3), 4),
                )

        return beats

    def _apply_story_beat(
        self,
        intent: ChoreographyIntent,
        beat: EmotionalStoryBeat,
    ) -> ChoreographyIntent:
        restrained_vocab = tuple(
            motion
            for motion in intent.motion_vocabulary
            if motion not in {MotionVocabulary.CASCADE, MotionVocabulary.CHASE}
        )

        vocabulary = (
            restrained_vocab
            if beat.restraint >= 0.7 and restrained_vocab
            else intent.motion_vocabulary
        )

        contrast = intent.contrast_strategy
        if beat.darkness_budget >= 0.5:
            contrast = ContrastStrategy.DARK_PRE_DROP

        return intent.__class__(
            **{
                **intent.__dict__,
                "motion_vocabulary": vocabulary,
                "contrast_strategy": contrast,
                "emotional_energy": round(
                    min(1.0, intent.emotional_energy * 0.6 + beat.payoff_strength * 0.4),
                    4,
                ),
                "intensity": round(
                    min(1.0, intent.intensity * 0.65 + beat.tension * 0.35),
                    4,
                ),
                "density_budget": round(
                    max(0.08, intent.density_budget * (1.0 - beat.restraint * 0.3)),
                    4,
                ),
                "metadata": {
                    **dict(intent.metadata),
                    "emotional_story_beat": beat.to_dict(),
                },
            }
        )
