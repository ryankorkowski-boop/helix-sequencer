from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from helix_intent.visual_intent import VisualIntent
from tools import helix_cli


def _intent() -> VisualIntent:
    return VisualIntent(
        id="intent_001",
        start_time=0.0,
        end_time=8.0,
        intent_type="bloom",
        musical_trigger="chorus_entry",
        spatial_behavior="center_out",
        target_roles=["hero_prop"],
        density_level="medium",
        emotional_role="bright",
        color_strategy="adaptive_palette",
        brightness_strategy="balanced",
        curve_strategy="section_envelope",
        render_style_hint="per_preview",
        confidence=0.8,
    )


class HelixCliPlacementTests(unittest.TestCase):
    def test_parser_exposes_placement_plan_command(self) -> None:
        parser = helix_cli.build_parser()
        args = parser.parse_args(["placement-plan", "song.wav", "layout.xml"])

        self.assertEqual(args.command, "placement-plan")
        self.assertEqual(args.audio_file, "song.wav")
        self.assertEqual(args.layout_file, "layout.xml")
        self.assertIsNone(args.output)

    def test_parser_exposes_placement_stub_render_command(self) -> None:
        parser = helix_cli.build_parser()
        args = parser.parse_args(["placement-stub-render", "song.wav", "layout.xml", "out", "--minimum-quality-score", "0.72"])

        self.assertEqual(args.command, "placement-stub-render")
        self.assertEqual(args.audio_file, "song.wav")
        self.assertEqual(args.layout_file, "layout.xml")
        self.assertEqual(args.output_dir, "out")
        self.assertEqual(args.minimum_quality_score, 0.72)

    def test_parser_exposes_xlights_effect_contract_command(self) -> None:
        parser = helix_cli.build_parser()
        args = parser.parse_args(["xlights-effect-contract", "song.wav", "layout.xml", "contract.json", "--minimum-quality-score", "0.72"])

        self.assertEqual(args.command, "xlights-effect-contract")
        self.assertEqual(args.audio_file, "song.wav")
        self.assertEqual(args.layout_file, "layout.xml")
        self.assertEqual(args.output_json, "contract.json")
        self.assertEqual(args.minimum_quality_score, 0.72)

    @patch("tools.helix_cli.xmp.parse_layout")
    @patch("tools.helix_cli._visual_intents_for_audio")
    def test_placement_plan_command_prints_report(self, mock_intents: Mock, mock_parse_layout: Mock) -> None:
        mock_intents.return_value = [_intent()]
        mock_parse_layout.return_value = Mock(models={"Mega Tree": Mock(type="tree", is_submodel=False)})

        out = io.StringIO()
        with redirect_stdout(out):
            code = helix_cli.main(["placement-plan", "song.wav", "layout.xml"])

        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("helix.placement_plan.v1", text)
        self.assertIn("Mega Tree", text)

    @patch("tools.helix_cli.xmp.parse_layout")
    @patch("tools.helix_cli._visual_intents_for_audio")
    def test_placement_plan_command_writes_report(self, mock_intents: Mock, mock_parse_layout: Mock) -> None:
        mock_intents.return_value = [_intent()]
        mock_parse_layout.return_value = Mock(models={"Mega Tree": Mock(type="tree", is_submodel=False)})

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "placement_plan.json"
            out = io.StringIO()
            with redirect_stdout(out):
                code = helix_cli.main(["placement-plan", "song.wav", "layout.xml", "--output", str(output_path)])
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "helix.placement_plan.v1")
        self.assertIn("output", out.getvalue())

    @patch("tools.helix_cli.xmp.parse_layout")
    @patch("tools.helix_cli._visual_intents_for_audio")
    def test_placement_stub_render_command_writes_stub_outputs(self, mock_intents: Mock, mock_parse_layout: Mock) -> None:
        mock_intents.return_value = [_intent()]
        mock_parse_layout.return_value = Mock(models={"Mega Tree": Mock(type="tree", is_submodel=False)})

        with tempfile.TemporaryDirectory() as tmp:
            out = io.StringIO()
            with redirect_stdout(out):
                code = helix_cli.main([
                    "placement-stub-render",
                    "song.wav",
                    "layout.xml",
                    tmp,
                    "--minimum-quality-score",
                    "0.1",
                ])
            report_path = Path(tmp) / "placement_stub_report.json"
            payload = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(payload["permission"]["allowed"])
        self.assertTrue(payload["rendered"])
        self.assertIn("placement_stub.xml", out.getvalue())

    @patch("tools.helix_cli.xmp.parse_layout")
    @patch("tools.helix_cli._visual_intents_for_audio")
    def test_xlights_effect_contract_command_writes_json(self, mock_intents: Mock, mock_parse_layout: Mock) -> None:
        mock_intents.return_value = [_intent()]
        mock_parse_layout.return_value = Mock(models={"Mega Tree": Mock(type="tree", is_submodel=False)})

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "xlights_effect_contract.json"
            out = io.StringIO()
            with redirect_stdout(out):
                code = helix_cli.main([
                    "xlights-effect-contract",
                    "song.wav",
                    "layout.xml",
                    str(output_path),
                    "--minimum-quality-score",
                    "0.1",
                ])
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "helix.xlights_effect_contract.v1")
        self.assertTrue(payload["permission"]["allowed"])
        self.assertIn("output_json", out.getvalue())


if __name__ == "__main__":
    unittest.main()
