from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from tools.build_demo_snowman_stage_pack import build_demo_snowman_stage_pack, write_demo_snowman_stage_pack


class DemoSnowmanStagePackTests(unittest.TestCase):
    def test_demo_stage_pack_contains_reactive_cues_for_every_member_and_prop(self) -> None:
        payload = build_demo_snowman_stage_pack()

        self.assertEqual(payload["status"], "reactive_working_stage_pack_slice")
        self.assertEqual(payload["demo"]["schema"], "helix.demo_snowman_stage_pack.v1")
        self.assertTrue(payload["validation"]["all_members_have_reactive_cues"])
        self.assertTrue(payload["validation"]["all_stage_props_have_reactive_cues"])
        self.assertTrue(payload["validation"]["drummer_feeds_floor_piano"])
        self.assertTrue(payload["integration"]["drummer_feeds_floor_piano"])

        for member_name in payload["demo"]["expected_members"]:
            self.assertIn(member_name, payload["band_members"])
            self.assertTrue(payload["band_members"][member_name]["reactive_cues"])

        for prop_name in payload["demo"]["expected_stage_props"]:
            self.assertIn(prop_name, payload["stage_props"])
            self.assertTrue(payload["stage_props"][prop_name]["reactive_cues"])

        floor_sources = {cue["source"] for cue in payload["stage_props"]["floor_piano"]["reactive_cues"]}
        self.assertIn("player_piano_hook", floor_sources)
        self.assertIn("note_events", floor_sources)
        self.assertIn("phrase_hit", floor_sources)

    def test_write_demo_stage_pack_outputs_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "demo_snowman_stage_pack.json"
            result = write_demo_snowman_stage_pack(output_path)

            self.assertEqual(result["path"], str(output_path))
            self.assertTrue(output_path.exists())
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["pack_id"], "HX_SNOWMAN_BAND_STAGE_PACK")
            self.assertEqual(data["demo"]["schema"], "helix.demo_snowman_stage_pack.v1")
            self.assertTrue(data["validation"]["drummer_feeds_floor_piano"])


if __name__ == "__main__":
    unittest.main()
