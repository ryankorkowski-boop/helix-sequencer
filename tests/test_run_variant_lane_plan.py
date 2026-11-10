from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tools.run_variant_lane_plan import load_entries, main


class RunVariantLanePlanTests(unittest.TestCase):
    def test_load_entries_accepts_candidate_list_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidates.json"
            path.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {"label": "signature"},
                            {"label": "wide_stage"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            entries = load_entries([path])

        self.assertEqual([entry["label"] for entry in entries], ["signature", "wide_stage"])

    def test_main_prints_lane_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.json"
            path.write_text(json.dumps({"label": "hook_focus", "shortlist_score": 91.5}), encoding="utf-8")
            out = StringIO()
            with redirect_stdout(out):
                code = main([str(path)])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["mode"], "variant_lanes_plan")
        self.assertEqual(payload["assignments"][0]["lane"], "lane_hook_accents")

    def test_main_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidate = tmp_path / "candidate.json"
            output = tmp_path / "plans" / "variant_lanes.json"
            candidate.write_text(json.dumps({"label": "cinematic_arc"}), encoding="utf-8")

            code = main([str(candidate), "--output", str(output)])

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(payload["assignments"][0]["lane"], "lane_cinematic_reveals")


if __name__ == "__main__":
    unittest.main()
