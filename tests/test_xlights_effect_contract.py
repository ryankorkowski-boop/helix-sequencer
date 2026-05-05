from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helix_intent.xlights_effect_contract import build_xlights_effect_contract, write_xlights_effect_contract


def _plan(*, quality: float = 0.75, passed: bool = True) -> dict[str, object]:
    return {
        "visual_intents": [
            {"id": "intent_001", "start_time": 0.0, "end_time": 4.0},
            {"id": "intent_002", "start_time": 4.0, "end_time": 8.0},
        ],
        "prop_effect_intents": [
            {"visual_intent_id": "intent_001", "target_prop": "Mega Tree", "effect_family": "energy_wave", "render_style": "per_preview", "brightness_cap": 0.82},
            {"visual_intent_id": "intent_002", "target_prop": "Front Roof", "effect_family": "outline_pulse", "render_style": "per_model", "brightness_cap": 0.62},
            {"visual_intent_id": "intent_002", "target_prop": "Singer", "effect_family": "character_hit", "render_style": "per_model", "brightness_cap": 0.55},
        ],
        "validation_report": {"passed": passed, "errors": [] if passed else ["bad plan"], "warnings": []},
        "quality_report": {"overall_placement_score": quality, "grade": "good", "recommendations": []},
    }


class XlightsEffectContractTests(unittest.TestCase):
    def test_build_contract_maps_supported_families_and_skips_unsupported(self) -> None:
        placements, report = build_xlights_effect_contract(_plan())

        self.assertTrue(report.rendered)
        self.assertEqual(report.placement_count, 2)
        self.assertEqual(report.skipped_count, 1)
        self.assertEqual(report.skipped_effect_families, ["character_hit"])
        self.assertEqual([item.effect_name for item in placements], ["Bars", "On"])
        self.assertEqual(placements[0].start_time, 0.0)
        self.assertEqual(placements[0].end_time, 4.0)
        self.assertEqual(placements[1].target_model, "Front Roof")

    def test_build_contract_blocks_failed_permission(self) -> None:
        placements, report = build_xlights_effect_contract(_plan(passed=False))

        self.assertEqual(placements, [])
        self.assertFalse(report.rendered)
        self.assertFalse(report.permission["allowed"])

    def test_write_contract_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "xlights_effect_contract.json"
            report = write_xlights_effect_contract(_plan(), path)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertTrue(report.rendered)
        self.assertEqual(payload["schema"], "helix.xlights_effect_contract.v1")
        self.assertEqual(payload["output_json"], str(path))
        self.assertEqual(payload["effect_placements"][0]["effect_name"], "Bars")
        self.assertIn("soft_wash", payload["supported_render_families"])


if __name__ == "__main__":
    unittest.main()
