from __future__ import annotations

import csv
import tempfile
from io import StringIO
from pathlib import Path
import unittest

from export.stage_pack_manifest_csv_export import (
    CSV_COLUMNS,
    STAGE_PACK_CSV_SCHEMA,
    build_demo_stage_pack_manifest_csv,
    write_demo_stage_pack_manifest_csv,
)


class StagePackManifestCsvExportTests(unittest.TestCase):
    def test_demo_manifest_csv_contains_expected_rows_and_columns(self) -> None:
        payload = build_demo_stage_pack_manifest_csv()

        self.assertEqual(payload["schema"], STAGE_PACK_CSV_SCHEMA)
        self.assertEqual(payload["status"], "stage_pack_manifest_csv")
        self.assertGreater(payload["row_count"], 0)
        self.assertEqual(payload["columns"], CSV_COLUMNS)
        self.assertTrue(payload["validation"]["has_rows"])
        self.assertTrue(payload["validation"]["has_header"])
        self.assertTrue(payload["validation"]["row_count_matches_manifest"])
        self.assertTrue(payload["validation"]["includes_faces_effect"])
        self.assertTrue(payload["validation"]["includes_floor_piano_hooks"])
        self.assertTrue(payload["validation"]["includes_all_expected_performers"])

        rows = list(csv.DictReader(StringIO(payload["csv_text"])))
        self.assertEqual(len(rows), payload["row_count"])
        self.assertEqual(list(rows[0].keys()), CSV_COLUMNS)
        performers = {row["performer"] for row in rows}
        self.assertIn("singer", performers)
        self.assertIn("female_singer", performers)
        self.assertIn("guitarist", performers)
        self.assertIn("bassist", performers)
        self.assertIn("drummer", performers)
        self.assertIn("floor_piano", performers)
        self.assertTrue(any(row["effect"] == "Faces" for row in rows))
        self.assertTrue(any(row["performer"] == "floor_piano" and row["source"] == "player_piano_hook" for row in rows))

    def test_write_demo_manifest_csv_outputs_csv_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "manifest.csv"
            result = write_demo_stage_pack_manifest_csv(output_path)

            self.assertEqual(result["path"], str(output_path))
            self.assertEqual(result["schema"], STAGE_PACK_CSV_SCHEMA)
            self.assertTrue(output_path.exists())
            self.assertTrue(Path(result["summary"]).exists())
            text = output_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(",".join(CSV_COLUMNS)))
            self.assertTrue(result["validation"]["includes_floor_piano_hooks"])


if __name__ == "__main__":
    unittest.main()
