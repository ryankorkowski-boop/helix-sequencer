from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.choreography_intent import ChoreographyIntent, DominanceStrategy
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class CinematographyFrame:
    section: str
    focus_mode: str
    depth_mode: str
    foreground: str
    background: str
    reveal_strategy: str
    negative_space: float
    silhouette_strength: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "focus_mode": self.focus_mode,
            "depth_mode": self.depth_mode,
            "foreground": self.foreground,
            "background": self.background,
            "reveal_strategy": self.reveal_strategy,
            "negative_space": self.negative_space,
            "silhouette_strength": self.silhouette_strength,
        }


class VisualCinematographyEngine:
    """Adds cinematic staging, focus, depth, and reveal guidance."""

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()
        frames = self._frames_for_graph(graph)

        for intent in graph:
            frame = frames.get(intent.section)
            if frame is None:
                output.add_intent(intent)
                continue

            output.add_intent(self._apply_frame(intent, frame))

        return output

    def _frames_for_graph(self, graph: IntentGraph) -> dict[str, CinematographyFrame]:
        frames: dict[str, CinematographyFrame] = {}

        for index, section in enumerate(graph.ordered_sections()):
            lowered = section.lower()
            if "intro" in lowered:
                frames[section] = CinematographyFrame(
                    section=section,
                    focus_mode="wide_establishing",
                    depth_mode="deep_background_glow",
                    foreground="outline",
                    background="whole_house",
                    reveal_strategy="slow_reveal",
                    negative_space=0.65,
                    silhouette_strength=0.75,
                )
            elif "verse" in lowered:
                frames[section] = CinematographyFrame(
                    section=section,
                    focus_mode="single_subject",
                    depth_mode="layered_midground",
                    foreground="featured_prop",
                    background="soft_texture",
                    reveal_strategy="selective_reveal",
                    negative_space=0.5,
                    silhouette_strength=0.45,
                )
            elif "build" in lowered or "pre" in lowered:
                frames[section] = CinematographyFrame(
                    section=section,
                    focus_mode="tightening_focus",
                    depth_mode="forward_motion_depth",
                    foreground="sequential_motion",
                    background="rising_texture",
                    reveal_strategy="progressive_reveal",
                    negative_space=0.28,
                    silhouette_strength=0.25,
                )
            elif "chorus" in lowered:
                frames[section] = CinematographyFrame(
                    section=section,
                    focus_mode="hero_wide",
                    depth_mode="full_depth_stack",
                    foreground="hero_prop",
                    background="supporting_groups",
                    reveal_strategy="full_reveal",
                    negative_space=0.12,
                    silhouette_strength=0.1,
                )
            elif "drop" in lowered or "final" in lowered:
                frames[section] = CinematographyFrame(
                    section=section,
                    focus_mode="maximum_impact",
                    depth_mode="all_planes_active",
                    foreground="impact_center",
                    background="whole_house",
                    reveal_strategy="instant_payoff",
                    negative_space=0.02,
                    silhouette_strength=0.0,
                )
            else:
                frames[section] = CinematographyFrame(
                    section=section,
                    focus_mode="transition_focus",
                    depth_mode="balanced_depth",
                    foreground="dominant_prop",
                    background="support_regions",
                    reveal_strategy="bridge_reveal",
                    negative_space=max(0.1, 0.45 - index * 0.05),
                    silhouette_strength=max(0.0, 0.35 - index * 0.04),
                )

        return frames

    def _apply_frame(
        self,
        intent: ChoreographyIntent,
        frame: CinematographyFrame,
    ) -> ChoreographyIntent:
        dominance = intent.dominance_strategy
        if frame.focus_mode in {"single_subject", "tightening_focus"}:
            dominance = DominanceStrategy.SINGLE_HERO
        elif frame.focus_mode in {"hero_wide", "maximum_impact"}:
            dominance = DominanceStrategy.DISTRIBUTED
        elif frame.focus_mode == "wide_establishing":
            dominance = DominanceStrategy.BACKGROUND_ONLY

        return intent.__class__(
            **{
                **intent.__dict__,
                "dominance_strategy": dominance,
                "density_budget": round(
                    max(0.05, intent.density_budget * (1.0 - frame.negative_space * 0.35)),
                    4,
                ),
                "metadata": {
                    **dict(intent.metadata),
                    "cinematography_frame": frame.to_dict(),
                },
            }
        )
