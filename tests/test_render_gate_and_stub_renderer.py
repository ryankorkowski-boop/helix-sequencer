from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from helix_intent.placement_stub_renderer import render_placement_stub_xml
from helix_intent.render_gate import evaluate_render_permission


def _plan(*, passed: bool = True, quality: float = 0.75) -> dict[str, object]:
    return {
        "visual_intents": [{"id": "intent_001"}],
        "candidates": [{"prop_name": "Mega Tree", "role": "hero"}],
        "prop_effect_intents": [
            {
                "visual_intent_id": "intent_001",
                "target_prop": "Mega Tree",
                "target_role": "hero",
                "effect_family": "energy_wave",
                "render_style": "per_preview",
                "curve_type": "section_envelope",
                "brightness_cap": 0.82,
                "confidence": 0.8,
            }
        ],
        "planner_report": {"intent_count": 1, "placement_count": 1, "rejected_intents": [], "capped_density_intents": []},
        "validation_report": {"passed": passed, "errors": [] if passed else ["bad plan"], "warnings": [], "warning_count": 0},
        "quality_report": {"overall_placement_score": quality, "grade": "good" if quality >= 0.72 else "prototype", "recommendations": []},
    }


class RenderGateAndStubRendererTests(unittest.TestCase):
    def test_render_permission_allows_valid_quality_plan(self) -> None:
        report = evaluate_render_permission(_plan())

        self.assertTrue(report.allowed)
        self.assertEqual(report.reason, "allowed")
        self.assertEqual(report.errors, [])

    def test_render_permission_blocks_validation_failure(self) -> None:
        report = evaluate_render_permission(_plan(passed=False))

        self.assertFalse(report.allowed)
        self.assertTrue(any("validation failed" in error.lower() for error in report.errors))

    def test_render_permission_blocks_low_quality(self) -> None:
        report = evaluate_render_permission(_plan(quality=0.45), minimum_quality_score=0.6)

        self.assertFalse(report.allowed)
        self.assertTrue(any("quality below" in error.lower() for error in report.errors))

    def test_stub_renderer_writes_xml_for_allowed_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = render_placement_stub_xml(_plan(), Path(tmp))
            root = ET.parse(report.output_xml).getroot()
            saved_report = json.loads(Path(report.output_report).read_text(encoding="utf-8"))

        self.assertTrue(report.rendered)
        self.assertEqual(root.tag, "helixPlacementStub")
        self.assertEqual(root.find(".//placement").attrib["targetProp"], "Mega Tree")  # type: ignore[union-attr]
        self.assertTrue(saved_report["permission"]["allowed"])

    def test_stub_renderer_writes_block_report_without_xml_when_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = render_placement_stub_xml(_plan(passed=False), Path(tmp))
            saved_report = json.loads(Path(report.output_report).read_text(encoding="utf-8"))

        self.assertFalse(report.rendered)
        self.assertEqual(report.skipped_reason, "render_permission_blocked")
        self.assertFalse(Path(report.output_xml).exists())
        self.assertFalse(saved_report["permission"]["allowed"])


if __name__ == "__main__":
    unittest.main()
