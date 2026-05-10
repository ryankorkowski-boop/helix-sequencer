from __future__ import annotations

from dataclasses import dataclass

from core.choreography_intent import ChoreographyIntent, MotionVocabulary
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class ShowIdentity:
    name: str
    theme: str
    finale_signature: str


class ShowIdentityEngine:
    """Maintains recurring show-wide choreography identity."""

    def __init__(self):
        self.identity = ShowIdentity(
            name="Helixia",
            theme="spatial_cinematic",
            finale_signature="orbital_resolution",
        )

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()

        for intent in graph:
            vocabulary = list(intent.motion_vocabulary)

            if MotionVocabulary.ORBITAL not in vocabulary:
                vocabulary.append(MotionVocabulary.ORBITAL)

            if MotionVocabulary.HELIX_SPIRAL not in vocabulary:
                vocabulary.append(MotionVocabulary.HELIX_SPIRAL)

            metadata = {
                **dict(intent.metadata),
                "show_identity": {
                    "name": self.identity.name,
                    "theme": self.identity.theme,
                    "finale_signature": self.identity.finale_signature,
                },
            }

            output.add_intent(
                intent.__class__(
                    **{
                        **intent.__dict__,
                        "motion_vocabulary": tuple(dict.fromkeys(vocabulary)),
                        "metadata": metadata,
                    }
                )
            )

        return output
