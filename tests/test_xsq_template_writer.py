from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from helix_intent.xsq_template_writer import write_xsq_from_template


def _contract() -> dict[str, object]:
    return {
        "schema": "helix.xlights_effect_contract.v1",
        "rendered": True,
        "permission": {"allowed": True},
        "supported_render_families": {"energy_wave": "Bars"},
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
            }
        ],
    }


class XsqTemplateWriterTests(unittest.TestCase):
    def test_writes_xsq_from_parseable_template_with_helix_contract_node(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            template = tmp_path / "template.xsq"
            contract = tmp_path / "contract.json"
            output = tmp_path / "out.xsq"
            template.write_text("<?xml version='1.0'?><xsequence><ElementEffects /></xsequence>", encoding="utf-8")
            contract.write_text(json.dumps(_contract()), encoding="utf-8")

            report = write_xsq_from_template(
                template_path=template,
                effect_contract_json=contract,
                output_xsq=output,
            )
            root = ET.parse(output).getroot()
            placement = root.find(".//HelixEffectContract/EffectPlacement")
            sidecar = json.loads(Path(report.sidecar_json).read_text(encoding="utf-8"))

        self.assertTrue(report.wrote_sequence)
        self.assertEqual(report.effect_count, 1)
        self.assertEqual(placement.attrib["targetModel"], "Mega Tree")  # type: ignore[union-attr]
        self.assertEqual(sidecar["schema"], "helix.xsq_template_writer.v1")

    def test_missing_template_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            contract = tmp_path / "contract.json"
            output = tmp_path / "out.xsq"
            contract.write_text(json.dumps(_contract()), encoding="utf-8")

            report = write_xsq_from_template(
                template_path=tmp_path / "missing_template.xsq",
                effect_contract_json=contract,
                output_xsq=output,
            )

        self.assertFalse(report.wrote_sequence)
        self.assertFalse(output.exists())
        self.assertTrue(any("Missing template XSQ" in error for error in report.errors))

    def test_invalid_contract_blocks_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            template = tmp_path / "template.xsq"
            contract = tmp_path / "contract.json"
            output = tmp_path / "out.xsq"
            template.write_text("<xsequence />", encoding="utf-8")
            bad = _contract()
            bad["permission"] = {"allowed": False}
            contract.write_text(json.dumps(bad), encoding="utf-8")

            report = write_xsq_from_template(
                template_path=template,
                effect_contract_json=contract,
                output_xsq=output,
            )

        self.assertFalse(report.wrote_sequence)
        self.assertFalse(output.exists())
        self.assertTrue(report.errors)


if __name__ == "__main__":
    unittest.main()
