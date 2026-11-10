from __future__ import annotations

import unittest

from helix_intent.placement_planner import PlacementCandidate, plan_prop_effect_intents
from helix_intent.visual_intent import VisualIntent


def _intent(
    *,
    intent_id: str = "intent_001",
    intent_type: str = "bloom",
    density: str = "medium",
    target_roles: list[str] | None = None,
    render_style_hint: str = "per_preview",
) -> VisualIntent:
    return VisualIntent(
        id=intent_id,
        start_time=0.0,
        end_time=10.0,
        intent_type=intent_type,
        musical_trigger="section_change",
        spatial_behavior="center_out",
        target_roles=target_roles or ["hero_prop", "whole_house"],
        density_level=density,
        emotional_role="bright",
        color_strategy="adaptive_palette",
        brightness_strategy="balanced",
        curve_strategy="section_envelope",
        render_style_hint=render_style_hint,
        confidence=0.8,
    )


class PlacementPlannerTests(unittest.TestCase):
    def test_maps_visual_intent_to_role_matched_prop_effects(self) -> None:
        intents = [_intent(target_roles=["hero_prop", "whole_house"])]
        candidates = [
            PlacementCandidate("mega_tree", "hero", "trees", priority=10),
            PlacementCandidate("roofline_front", "structure", "roofline", priority=20),
            PlacementCandidate("random_spinner", "accent", "spinners", priority=90),
        ]

        placements, report = plan_prop_effect_intents(intents, candidates)

        self.assertEqual(report.intent_count, 1)
        self.assertEqual(report.rejected_intents, [])
        self.assertEqual({placement.target_prop for placement in placements}, {"mega_tree", "roofline_front"})
        by_prop = {placement.target_prop: placement for placement in placements}
        self.assertEqual(by_prop["mega_tree"].effect_family, "energy_wave")
        self.assertEqual(by_prop["roofline_front"].effect_family, "outline_pulse")
        self.assertEqual(by_prop["mega_tree"].brightness_cap, 0.62)

    def test_density_caps_full_intent_targets_deterministically(self) -> None:
        intents = [_intent(density="sparse", target_roles=["whole_house", "background", "hero_prop"])]
        candidates = [
            PlacementCandidate("mega_tree", "hero", "trees", priority=50),
            PlacementCandidate("roofline_front", "structure", "roofline", priority=10),
            PlacementCandidate("roofline_back", "structure", "roofline", priority=20),
            PlacementCandidate("window_left", "window", "windows", priority=30),
            PlacementCandidate("mood_wash", "mood", "wash", priority=40),
        ]

        placements, report = plan_prop_effect_intents(intents, candidates)

        self.assertEqual(len(placements), 2)
        self.assertEqual(report.capped_density_intents, ["intent_001"])
        self.assertEqual([placement.target_prop for placement in placements], ["roofline_front", "roofline_back"])
        self.assertTrue(all(placement.brightness_cap == 0.38 for placement in placements))

    def test_rejects_intent_when_no_candidate_matches_target_roles(self) -> None:
        intents = [_intent(intent_id="intent_no_match", target_roles=["vocal_prop"])]
        candidates = [PlacementCandidate("roofline_front", "structure", "roofline", priority=10)]

        placements, report = plan_prop_effect_intents(intents, candidates)

        self.assertEqual(placements, [])
        self.assertEqual(report.rejected_intents, ["intent_no_match"])
        self.assertEqual(report.placement_count, 0)

    def test_accepts_mapping_candidates_from_layout_metadata(self) -> None:
        intents = [_intent(intent_type="transition", target_roles=["arches"])]
        candidates = [
            {"name": "arch_left", "role": "travel", "family": "travel_props", "priority": 20},
            {"name": "matrix_main", "role": "detail_surface", "family": "matrices", "priority": 5},
        ]

        placements, report = plan_prop_effect_intents(intents, candidates)

        self.assertEqual(report.rejected_intents, [])
        self.assertEqual(len(placements), 1)
        self.assertEqual(placements[0].target_prop, "arch_left")
        self.assertEqual(placements[0].effect_family, "directional_sweep")
        self.assertEqual(placements[0].curve_type, "section_envelope")


if __name__ == "__main__":
    unittest.main()
