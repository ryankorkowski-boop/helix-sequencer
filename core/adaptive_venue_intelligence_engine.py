from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.choreography_intent import ChoreographyIntent, DominanceStrategy
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class VenueProfile:
    venue_name: str
    house_width: float
    house_height: float
    yard_depth: float
    viewer_distance: float
    prop_density: float
    megatree_height: float
    driveway_width: float
    neighborhood_scale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue_name": self.venue_name,
            "house_width": self.house_width,
            "house_height": self.house_height,
            "yard_depth": self.yard_depth,
            "viewer_distance": self.viewer_distance,
            "prop_density": self.prop_density,
            "megatree_height": self.megatree_height,
            "driveway_width": self.driveway_width,
            "neighborhood_scale": self.neighborhood_scale,
        }


class AdaptiveVenueIntelligenceEngine:
    """Adapts choreography to physical layout and real-world viewing conditions."""

    DEFAULT_PROFILE = VenueProfile(
        venue_name="Helixia Reference Lot",
        house_width=72.0,
        house_height=28.0,
        yard_depth=95.0,
        viewer_distance=70.0,
        prop_density=0.72,
        megatree_height=24.0,
        driveway_width=18.0,
        neighborhood_scale="suburban_showcase",
    )

    def __init__(self, venue_profile: VenueProfile | None = None):
        self.venue_profile = venue_profile or self.DEFAULT_PROFILE

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()

        for intent in graph:
            output.add_intent(self._apply_venue_logic(intent))

        return output

    def _apply_venue_logic(self, intent: ChoreographyIntent) -> ChoreographyIntent:
        profile = self.venue_profile

        visibility_scale = min(1.0, profile.viewer_distance / 70.0)
        spacing_scale = max(0.08, 1.0 - profile.prop_density * 0.25)

        dominance = intent.dominance_strategy

        if profile.viewer_distance > 90:
            dominance = DominanceStrategy.DISTRIBUTED
        elif profile.prop_density > 0.82:
            dominance = DominanceStrategy.SINGLE_HERO

        cinematic_scale = 1.0

        if profile.megatree_height >= 24:
            cinematic_scale += 0.08

        if profile.house_width >= 70:
            cinematic_scale += 0.05

        if profile.neighborhood_scale == "dense_urban":
            cinematic_scale -= 0.12

        return intent.__class__(
            **{
                **intent.__dict__,
                "dominance_strategy": dominance,
                "density_budget": round(
                    max(0.05, intent.density_budget * spacing_scale),
                    4,
                ),
                "intensity": round(
                    min(1.0, intent.intensity * visibility_scale * cinematic_scale),
                    4,
                ),
                "metadata": {
                    **dict(intent.metadata),
                    "venue_profile": profile.to_dict(),
                    "venue_visibility_scale": round(visibility_scale, 4),
                    "venue_spacing_scale": round(spacing_scale, 4),
                    "venue_cinematic_scale": round(cinematic_scale, 4),
                },
            }
        )
