from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from export.stage_pack_manifest_export import (
    STAGE_PACK_MANIFEST_SCHEMA,
    build_demo_stage_pack_export_manifest,
    write_demo_stage_pack_export_manifest,
)


class StagePackManifestExportTests(unittest.TestCase):
    def test_demo_manifest_flattens_reactive_stage_pack_rows(self) -> None:
        manifest = build_demo_stage_pack_export_manifest()

        self.assertEqual(manifest["schema"], STAGE_PACK_MANIFEST_SCHEMA)
        self.assertEqual(manifest["status"], "stage_pack_export_manifest")
        self.assertGreater(manifest["row_count"], 0)
        self.assertTrue(manifest["validation"]["has_rows"])
        self.assertTrue(manifest["validation"]["all_rows_have_targets"])
        self.assertTrue(manifest["validation"]["all_rows_have_positive_duration"])
        self.assertTrue(manifest["validation"]["includes_faces_effect"])
        self.assertTrue(manifest["validation"]["includes_drum_track"])
        self.assertTrue(manifest["validation"]["includes_floor_piano_hooks"])

        performers = {row["performer"] for row in manifest["rows"]}
        self.assertIn("singer", performers)
        self.assertIn("female_singer", performers)
        self.assertIn("guitarist", performers)
        self.assertIn("bassist", performers)
        self.assertIn("drummer", performers)
        self.assertIn("floor_piano", performers)

        self.assertTrue(any(row["effect"] == "Faces" for row in manifest["rows"]))
        self.assertTrue(any(row["performer"] == "floor_piano" and row["source"] == "player_piano_hook" for row in manifest["rows"]))
        self.assertTrue(all(row["end_ms"] > row["start_ms"] for row in manifest["rows"]))

    def test_write_demo_manifest_outputs_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "demo_manifest.json"
            result = write_demo_stage_pack_export_manifest(output_path)

            self.assertEqual(result["path"], str(output_path))
            self.assertEqual(result["schema"], STAGE_PACK_MANIFEST_SCHEMA)
            self.assertTrue(output_path.exists())
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], STAGE_PACK_MANIFEST_SCHEMA)
            self.assertEqual(data["row_count"], result["row_count"])
            self.assertTrue(data["validation"]["includes_floor_piano_hooks"])


if __name__ == "__main__":
    unittest.main()
