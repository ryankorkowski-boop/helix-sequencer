from __future__ import annotations

from dataclasses import replace

from core.choreography_intent import ChoreographyIntent
from core.intent_graph import IntentGraph


class SpatialChoreographyEngine:
    """Deterministic spatial orchestration pass.

    This lightweight pass makes the multi-pass director operational on the
    canonical branch without depending on optional layout/runtime state. It
    preserves every intent while adding spatial metadata that downstream
    placement/export code can inspect.
    """

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()
        for intent in graph:
            output.add_intent(self._with_spatial_metadata(intent))
        return output

    @staticmethod
    def _with_spatial_metadata(intent: ChoreographyIntent) -> ChoreographyIntent:
        focal_region = intent.focal_region or "stage"
        support_regions = tuple(intent.support_regions or ("background",))
        metadata = {
            **dict(intent.metadata),
            "spatial_choreography": {
                "focal_region": focal_region,
                "support_regions": support_regions,
                "target_families": tuple(target.value for target in intent.target_families),
                "density_budget": intent.density_budget,
            },
        }
        return replace(
            intent,
            focal_region=focal_region,
            support_regions=support_regions,
            metadata=metadata,
        )
