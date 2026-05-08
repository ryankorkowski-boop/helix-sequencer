from __future__ import annotations

import unittest
from dataclasses import dataclass

from helix_intent.layout_candidates import (
    candidate_from_model,
    candidates_from_layout_intelligence,
    candidates_from_parsed_layout,
    merge_candidates,
)
from helix_intent.placement_planner import PlacementCandidate, plan_prop_effect_intents
from helix_intent.visual_intent import VisualIntent


@dataclass
class FakeModel:
    type: str
    is_submodel: bool = False


@dataclass
class FakeParsedLayout:
    models: dict[str, FakeModel]


def _intent() -> VisualIntent:
    return VisualIntent(
        id="intent_001",
        start_time=0.0,
        end_time=12.0,
        intent_type="bloom",
        musical_trigger="chorus_entry",
        spatial_behavior="center_out",
        target_roles=["hero_prop", "whole_house", "vocal_prop"],
        density_level="full",
        emotional_role="bright",
        color_strategy="adaptive_palette",
        brightness_strategy="balanced",
        curve_strategy="section_envelope",
        render_style_hint="per_preview",
        confidence=0.8,
    )


class LayoutCandidateTests(unittest.TestCase):
    def test_candidate_from_model_uses_type_defaults(self) -> None:
        self.assertEqual(candidate_from_model("Mega Tree", "tree").role, "hero")
        self.assertEqual(candidate_from_model("Front Arch", "arch").role, "travel")
        self.assertEqual(candidate_from_model("Main Matrix", "matrix").family, "matrices")
        self.assertEqual(candidate_from_model("Front Roof", "line").role, "structure")

    def test_candidate_from_model_name_hints_override_type(self) -> None:
        cactus = candidate_from_model("HX_CACTUS_BODY", "custom")
        singer = candidate_from_model("HX_SNOWMAN_SINGER_BODY", "custom")
        drum = candidate_from_model("HX_SNOWMAN_DRUMMER_INSTRUMENT", "custom")

        self.assertEqual(cactus.role, "performer")
        self.assertEqual(cactus.family, "character")
        self.assertEqual(singer.role, "performer")
        self.assertEqual(singer.family, "snowman_band")
        self.assertEqual(drum.role, "performer")
        self.assertEqual(drum.family, "snowman_band")

    def test_candidates_from_parsed_layout_skips_submodels(self) -> None:
        parsed = FakeParsedLayout(
            models={
                "Mega Tree": FakeModel("tree"),
                "Mega Tree/TOP": FakeModel("submodel", is_submodel=True),
                "Front Roof": FakeModel("line"),
            }
        )

        candidates = candidates_from_parsed_layout(parsed)

        self.assertEqual({candidate.prop_name for candidate in candidates}, {"Mega Tree", "Front Roof"})

    def test_candidates_from_layout_intelligence_includes_performers_and_lots(self) -> None:
        intelligence = {
            "performer_models": {
                "snowman_band": ["HX_SNOWMAN_DRUMMER_BODY"],
                "cactus_tubeman": ["HX_CACTUS_BODY", "HX_TUBEMAN_ARMS"],
            },
            "house_lots": [
                {"lot_id": "house_1_1", "roles": ["structure"], "families": ["lines"]},
            ],
            "special_lots": [
                {"lot_id": "arches_lot", "roles": ["travel"], "families": ["travel_props"]},
            ],
        }

        candidates = candidates_from_layout_intelligence(intelligence)
        by_name = {candidate.prop_name: candidate for candidate in candidates}

        self.assertEqual(by_name["HX_SNOWMAN_DRUMMER_BODY"].role, "performer")
        self.assertEqual(by_name["HX_CACTUS_BODY"].family, "character")
        self.assertEqual(by_name["arches_lot"].role, "travel")
        self.assertEqual(by_name["house_1_1"].role, "structure")

    def test_merge_candidates_keeps_highest_priority_version(self) -> None:
        merged = merge_candidates(
            [PlacementCandidate("mega_tree", "support", "unknown", priority=90)],
            [PlacementCandidate("mega_tree", "hero", "trees", priority=10)],
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].role, "hero")
        self.assertEqual(merged[0].priority, 10)

    def test_candidates_feed_placement_planner(self) -> None:
        parsed = FakeParsedLayout(
            models={
                "Mega Tree": FakeModel("tree"),
                "Front Roof": FakeModel("line"),
                "HX_SNOWMAN_SINGER_BODY": FakeModel("custom"),
            }
        )
        candidates = candidates_from_parsed_layout(parsed)

        placements, report = plan_prop_effect_intents([_intent()], candidates)

        self.assertEqual(report.rejected_intents, [])
        self.assertEqual({placement.target_prop for placement in placements}, {"Mega Tree", "Front Roof", "HX_SNOWMAN_SINGER_BODY"})
        by_prop = {placement.target_prop: placement for placement in placements}
        self.assertEqual(by_prop["Mega Tree"].effect_family, "energy_wave")
        self.assertEqual(by_prop["Front Roof"].effect_family, "outline_pulse")
        self.assertEqual(by_prop["HX_SNOWMAN_SINGER_BODY"].effect_family, "character_hit")


if __name__ == "__main__":
    unittest.main()
