from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tools.build_helixville4_band_integration_plan import (
    build_integration_plan_from_extracts,
    infer_member_id,
    main,
)


class Helixville4BandIntegrationPlanTests(unittest.TestCase):
    def test_infer_member_id_from_common_band_terms(self) -> None:
        self.assertEqual(infer_member_id("Singing Bulb Left Phonemes"), "snowman_singer")
        self.assertEqual(infer_member_id("Slash Guitar Strum"), "snowman_guitarist")
        self.assertEqual(infer_member_id("Bassman Pluck Track"), "snowman_bassist")
        self.assertEqual(infer_member_id("Mad Drummer Kick Snare"), "snowman_drummer")
        self.assertEqual(infer_member_id("female harmony call response"), "snowman_singer_female")

    def test_build_plan_maps_extracted_models_and_timing_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            extract = Path(tmp) / "extract.json"
            extract.write_text(
                json.dumps(
                    {
                        "schema": "helixville4.xlights_band_asset_extract.v1",
                        "models": [
                            {
                                "name": "Singing Bulb Left",
                                "member_hint": "snowman_singer",
                                "display_as": "Custom",
                                "start_channel": "1",
                                "submodels": ["AI", "E", "MBP", "REST", "Bulb Outline"],
                                "phoneme_submodels": ["AI", "E", "MBP", "REST"],
                                "phoneme_capable": True,
                            },
                            {
                                "name": "Mad Drummer Snowman",
                                "member_hint": "snowman_drummer",
                                "display_as": "Custom",
                                "start_channel": "500",
                                "submodels": ["Kick", "Snare", "Cymbals"],
                            },
                        ],
                        "groups": [
                            {"name": "Snowman Band", "members": ["Singing Bulb Left", "Mad Drummer Snowman"]}
                        ],
                        "timing_tracks": [
                            {"name": "snowman_singer_phonemes", "tag": "TimingTrack", "member_hint": "snowman_singer"},
                            {"name": "snowman_drummer_kick", "tag": "TimingTrack", "member_hint": "snowman_drummer"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            plan = build_integration_plan_from_extracts([extract])

        by_member = {item["member_id"]: item for item in plan["assignments"]}
        self.assertEqual(plan["schema"], "helixville4.band_integration_plan.v1")
        self.assertEqual(by_member["snowman_singer"]["discovered_models"][0]["name"], "Singing Bulb Left")
        self.assertIn("MBP", by_member["snowman_singer"]["discovered_phoneme_submodels"])
        self.assertEqual(
            by_member["snowman_singer"]["discovered_timing_tracks"][0]["name"],
            "snowman_singer_phonemes",
        )
        self.assertEqual(by_member["snowman_drummer"]["discovered_models"][0]["name"], "Mad Drummer Snowman")
        self.assertTrue(by_member["snowman_singer"]["ready_for_layout_mapping"])
        self.assertTrue(by_member["snowman_singer"]["ready_for_timing_mapping"])
        self.assertIn("snowman_singer", plan["summary"]["phoneme_source_members"])

    def test_cli_prints_and_writes_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            extract = tmp_path / "extract.json"
            output = tmp_path / "plan" / "band_plan.json"
            extract.write_text(json.dumps({"models": [{"name": "Slash Guitar"}], "timing_tracks": []}), encoding="utf-8")

            printed = StringIO()
            with redirect_stdout(printed):
                print_code = main([str(extract)])
            write_code = main([str(extract), "--output", str(output)])

            printed_payload = json.loads(printed.getvalue())
            written_payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(print_code, 0)
        self.assertEqual(write_code, 0)
        self.assertEqual(printed_payload["assignment_count"], 5)
        self.assertEqual(written_payload["assignment_count"], 5)


if __name__ == "__main__":
    unittest.main()
