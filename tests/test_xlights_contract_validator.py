from __future__ import annotations

import json
from copy import deepcopy

import pytest
import tempfile
import unittest
from pathlib import Path

from helix_intent.xlights_contract_validator import (
    validate_xlights_effect_contract,
    validate_xlights_effect_contract_file,
)


def _contract() -> dict[str, object]:
    return {
        "schema": "helix.xlights_effect_contract.v1",
        "rendered": True,
        "permission": {"allowed": True},
        "supported_render_families": {"energy_wave": "Bars", "outline_pulse": "On"},
        "skipped_count": 0,
        "effect_placements": [
            {
                "start_time": 0.0,
                "end_time": 4.0,
                "target_model": "Mega Tree",
                "effect_name": "Bars",
                "render_style": "per_preview",
                "brightness_cap": 0.82,
                "source_visual_intent_id": "intent_001",
                "source_effect_family": "energy_wave",
            },
            {
                "start_time": 4.0,
                "end_time": 8.0,
                "target_model": "Front Roof",
                "effect_name": "On",
                "render_style": "per_model",
                "brightness_cap": 0.62,
                "source_visual_intent_id": "intent_002",
                "source_effect_family": "outline_pulse",
            },
        ],
    }


class XlightsContractValidatorTests(unittest.TestCase):
    def test_valid_contract_passes(self) -> None:
        report = validate_xlights_effect_contract(_contract())

        self.assertTrue(report.passed)
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.metrics["placement_count"], 2)
        self.assertEqual(report.metrics["unique_target_count"], 2)

    def test_invalid_schema_and_permission_fail(self) -> None:
        payload = _contract()
        payload["schema"] = "bad.schema"
        payload["permission"] = {"allowed": False}

        report = validate_xlights_effect_contract(payload)

        self.assertFalse(report.passed)
        self.assertTrue(any("Unexpected schema" in error for error in report.errors))
        self.assertTrue(any("permission" in error for error in report.errors))

    def test_bad_placement_fields_fail(self) -> None:
        payload = _contract()
        payload["effect_placements"] = [
            {
                "start_time": 5.0,
                "end_time": 4.0,
                "target_model": "",
                "effect_name": "Unsupported",
                "brightness_cap": 1.2,
                "source_visual_intent_id": "",
                "source_effect_family": "",
            }
        ]

        report = validate_xlights_effect_contract(payload)

        self.assertFalse(report.passed)
        self.assertGreaterEqual(report.error_count, 5)
        self.assertTrue(any("unsupported effect_name" in error for error in report.errors))
        self.assertTrue(any("end_time <= start_time" in error for error in report.errors))

    def test_file_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.json"
            path.write_text(json.dumps(_contract()), encoding="utf-8")
            report = validate_xlights_effect_contract_file(path)

        self.assertTrue(report.passed)


if __name__ == "__main__":
    unittest.main()

@pytest.mark.parametrize(
    "field,value",
    [
        ("start_time", float("nan")),
        ("start_time", float("inf")),
        ("start_time", float("-inf")),
        ("end_time", float("nan")),
        ("end_time", float("inf")),
        ("end_time", float("-inf")),
        ("brightness_cap", float("nan")),
        ("brightness_cap", float("inf")),
        ("brightness_cap", float("-inf")),
    ],
)
def test_nonfinite_native_effect_contract_values_are_rejected(field, value):
    payload = deepcopy(_contract())
    payload["effect_placements"][0][field] = value
    report = validate_xlights_effect_contract(payload)
    assert not report.passed
    assert any(field in error for error in report.errors)


def test_writer_refuses_nonfinite_contract(tmp_path):
    from helix_intent.xsq_template_writer import write_xsq_from_template
    template = tmp_path / "template.xsq"
    template.write_text("<xsequence><ElementEffects /></xsequence>", encoding="utf-8")
    payload = _contract()
    payload["effect_placements"][0]["end_time"] = float("inf")
    contract = tmp_path / "contract.json"
    contract.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "output.xsq"
    report = write_xsq_from_template(
        template_path=template, effect_contract_json=contract, output_xsq=output
    )
    assert not report.wrote_sequence
    assert not output.exists()
    assert any("end_time" in error for error in report.errors)
