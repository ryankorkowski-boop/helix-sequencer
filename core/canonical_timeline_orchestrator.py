from __future__ import annotations

from dataclasses import replace

from core.intent_graph import IntentGraph


class CanonicalTimelineOrchestrator:
    def __init__(self, *, minimum_duration: float = 0.25):
        self.minimum_duration = minimum_duration

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()
        for intent in graph:
            start = max(0.0, round(float(intent.start), 6))
            duration = max(self.minimum_duration, round(float(intent.duration), 6))
            output.add_intent(
                replace(
                    intent,
                    start=start,
                    duration=duration,
                    metadata={
                        **dict(intent.metadata),
                        "canonical_timeline": {
                            "minimum_duration": self.minimum_duration,
                        },
                    },
                )
            )
        return output
