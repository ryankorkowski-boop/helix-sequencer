from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helix_intent.placement_planner import PlacementCandidate, plan_prop_effect_intents
from helix_intent.placement_report import build_placement_export_report, write_placement_export_report
from helix_intent.visual_intent import VisualIntent


def _intent(target_roles: list[str] | None = None) -> VisualIntent:
    return VisualIntent(
        id="intent_001",
        start_time=0.0,
        end_time=8.0,
        intent_type="bloom",
        musical_trigger="chorus_entry",
        spatial_behavior="center_out",
        target_roles=target_roles or ["hero_prop"],
        density_level="medium",
        emotional_role="bright",
        color_strategy="adaptive_palette",
        brightness_strategy="balanced",
        curve_strategy="section_envelope",
        render_style_hint="per_preview",
        confidence=0.8,
    )


class PlacementReportTests(unittest.TestCase):
    def test_build_placement_export_report_serializes_plan(self) -> None:
        intents = [_intent()]
        candidates = [PlacementCandidate("mega_tree", "hero", "trees", priority=10)]
        placements, planner_report = plan_prop_effect_intents(intents, candidates)

        report = build_placement_export_report(
            visual_intents=intents,
            candidates=candidates,
            prop_effect_intents=placements,
            planner_report=planner_report,
        )
        payload = report.to_dict()

        self.assertEqual(payload["schema"], "helix.placement_plan.v1")
        self.assertEqual(payload["warnings"], [])
        self.assertEqual(payload["planner_report"]["placement_count"], 1)
        self.assertEqual(payload["visual_intents"][0]["id"], "intent_001")
        self.assertEqual(payload["candidates"][0]["prop_name"], "mega_tree")
        self.assertEqual(payload["prop_effect_intents"][0]["effect_family"], "energy_wave")

    def test_report_warns_for_rejected_intents(self) -> None:
        intents = [_intent(target_roles=["vocal_prop"])]
        candidates = [PlacementCandidate("roofline", "structure", "roofline", priority=10)]
        placements, planner_report = plan_prop_effect_intents(intents, candidates)

        report = build_placement_export_report(
            visual_intents=intents,
            candidates=candidates,
            prop_effect_intents=placements,
            planner_report=planner_report,
        )

        self.assertEqual(placements, [])
        self.assertTrue(any("Rejected intents" in warning for warning in report.warnings))
        self.assertTrue(any("produced no prop-effect intents" in warning for warning in report.warnings))

    def test_write_placement_export_report_outputs_json(self) -> None:
        intents = [_intent()]
        candidates = [PlacementCandidate("mega_tree", "hero", "trees", priority=10)]
        placements, planner_report = plan_prop_effect_intents(intents, candidates)
        report = build_placement_export_report(
            visual_intents=intents,
            candidates=candidates,
            prop_effect_intents=placements,
            planner_report=planner_report,
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = write_placement_export_report(report, Path(tmp) / "placement" / "plan.json")
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["schema"], "helix.placement_plan.v1")
        self.assertEqual(payload["prop_effect_intents"][0]["target_prop"], "mega_tree")


if __name__ == "__main__":
    unittest.main()
