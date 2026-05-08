from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from helix_intent.placement_pipeline import build_and_write_placement_plan, build_placement_plan
from helix_intent.placement_planner import PlacementCandidate
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
        end_time=16.0,
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
        confidence=0.9,
    )


class PlacementPipelineTests(unittest.TestCase):
    def test_build_placement_plan_from_parsed_layout(self) -> None:
        parsed = FakeParsedLayout(
            models={
                "Mega Tree": FakeModel("tree"),
                "Front Roof": FakeModel("line"),
                "Mega Tree/TOP": FakeModel("submodel", is_submodel=True),
            }
        )

        report = build_placement_plan(visual_intents=[_intent()], parsed_layout=parsed)
        payload = report.to_dict()

        self.assertEqual(payload["schema"], "helix.placement_plan.v1")
        self.assertEqual(payload["planner_report"]["rejected_intents"], [])
        self.assertEqual({item["target_prop"] for item in payload["prop_effect_intents"]}, {"Mega Tree", "Front Roof"})

    def test_build_placement_plan_merges_extra_candidates(self) -> None:
        parsed = FakeParsedLayout(models={"Mega Tree": FakeModel("tree")})
        report = build_placement_plan(
            visual_intents=[_intent()],
            parsed_layout=parsed,
            extra_candidates=[PlacementCandidate("Lead Singer", "vocals", "faces", priority=5)],
        )
        payload = report.to_dict()

        self.assertEqual(
            {item["target_prop"] for item in payload["prop_effect_intents"]},
            {"Mega Tree", "Lead Singer"},
        )

    def test_build_placement_plan_from_layout_intelligence(self) -> None:
        intelligence = {
            "performer_models": {"snowman_band": ["HX_SNOWMAN_SINGER_BODY"]},
            "house_lots": [{"lot_id": "house_1_1", "roles": ["structure"], "families": ["lines"]}],
            "special_lots": [],
        }

        report = build_placement_plan(visual_intents=[_intent()], layout_intelligence=intelligence)
        payload = report.to_dict()

        self.assertEqual(payload["planner_report"]["rejected_intents"], [])
        self.assertEqual(
            {item["target_prop"] for item in payload["prop_effect_intents"]},
            {"HX_SNOWMAN_SINGER_BODY", "house_1_1"},
        )

    def test_build_and_write_placement_plan_outputs_json(self) -> None:
        parsed = FakeParsedLayout(models={"Mega Tree": FakeModel("tree")})
        with tempfile.TemporaryDirectory() as tmp:
            path = build_and_write_placement_plan(
                visual_intents=[_intent()],
                parsed_layout=parsed,
                output_path=Path(tmp) / "placement_plan.json",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["schema"], "helix.placement_plan.v1")
        self.assertEqual(payload["prop_effect_intents"][0]["target_prop"], "Mega Tree")


if __name__ == "__main__":
    unittest.main()
