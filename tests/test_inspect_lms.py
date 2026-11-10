from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.inspect_lms import inspect_lms, main


LMS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<sequence>
  <channels>
    <channel id="1" name="Roof 1" />
    <channel id="2" name="Roof 2" />
    <channel id="3" name="Tree 1" />
  </channels>
  <track name="Main">
    <timing centisecond="0" />
    <timing centisecond="500" />
    <effect channel="1" startCentisecond="0" endCentisecond="100">On intensity 100</effect>
    <effect channel="2" startCentisecond="100" endCentisecond="250">Fade up</effect>
    <effect channel="3" startCentisecond="250" endCentisecond="500">Twinkle</effect>
  </track>
</sequence>
"""


class InspectLmsTests(unittest.TestCase):
    def test_inspect_lms_reports_channels_duration_and_hints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.lms"
            path.write_text(LMS_FIXTURE, encoding="utf-8")
            report = inspect_lms(path)

        payload = report.to_dict()
        self.assertEqual(payload["xml_root"], "sequence")
        self.assertGreaterEqual(payload["probable_channel_count"], 3)
        self.assertGreaterEqual(payload["channel_tag_count"], 3)
        self.assertGreater(payload["event_like_tag_count"], 0)
        self.assertEqual(payload["probable_duration_seconds"], 5.0)
        self.assertGreater(payload["timing_density_events_per_second"], 0.0)
        self.assertGreaterEqual(payload["effect_hints"].get("on", 0), 1)
        self.assertGreaterEqual(payload["effect_hints"].get("fade", 0), 1)
        self.assertGreaterEqual(payload["effect_hints"].get("twinkle", 0), 1)

    def test_missing_lms_returns_warning(self) -> None:
        report = inspect_lms("missing_file.lms")

        self.assertTrue(any("Missing LMS file" in warning for warning in report.warnings))

    def test_main_writes_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lms = tmp_path / "fixture.lms"
            output = tmp_path / "inspection.json"
            lms.write_text(LMS_FIXTURE, encoding="utf-8")

            code = main([str(lms), "--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "helix.lms_inspection.v1")
        self.assertEqual(payload["probable_duration_seconds"], 5.0)


if __name__ == "__main__":
    unittest.main()
