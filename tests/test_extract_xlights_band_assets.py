from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tools.extract_xlights_band_assets import extract_xlights_band_assets, main


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<xrgb>
  <models>
    <model name="Singing Bulb Left" DisplayAs="Custom" StartChannel="1">
      <subModel name="AI" />
      <subModel name="E" />
      <subModel name="FV" />
      <subModel name="MBP" />
      <subModel name="REST" />
      <subModel name="Bulb Outline" />
    </model>
    <model name="Mad Drummer Snowman" DisplayAs="Custom" StartChannel="500">
      <subModel name="Kick" />
      <subModel name="Snare" />
      <subModel name="Cymbals" />
    </model>
  </models>
  <modelGroups>
    <modelGroup name="Snowman Band" models="Singing Bulb Left,Mad Drummer Snowman" />
  </modelGroups>
  <TimingTrack name="snowman_singer_phonemes" kind="phoneme" />
  <TimingTrack name="snowman_drummer_kick" kind="drum" />
  <TimingTrack name="verse" kind="section" />
</xrgb>
"""


class ExtractXlightsBandAssetsTests(unittest.TestCase):
    def test_extracts_singing_bulb_models_groups_and_timing_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "xlights_rgbeffects.xml"
            path.write_text(SAMPLE_XML, encoding="utf-8")

            payload = extract_xlights_band_assets(path)

        self.assertEqual(payload["schema"], "helixville4.xlights_band_asset_extract.v1")
        self.assertEqual(payload["model_count"], 2)
        self.assertEqual(payload["group_count"], 1)
        self.assertEqual(payload["timing_track_count"], 3)
        singer = next(model for model in payload["models"] if model["name"] == "Singing Bulb Left")
        drummer = next(model for model in payload["models"] if model["name"] == "Mad Drummer Snowman")
        self.assertEqual(singer["member_hint"], "snowman_singer")
        self.assertTrue(singer["phoneme_capable"])
        self.assertIn("MBP", singer["phoneme_submodels"])
        self.assertEqual(drummer["member_hint"], "snowman_drummer")
        self.assertEqual(payload["groups"][0]["name"], "Snowman Band")
        self.assertEqual(
            {track["name"] for track in payload["band_related_timing_tracks"]},
            {"snowman_singer_phonemes", "snowman_drummer_kick"},
        )

    def test_cli_prints_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.xsq"
            path.write_text(SAMPLE_XML, encoding="utf-8")
            out = StringIO()
            with redirect_stdout(out):
                code = main([str(path)])

        payload = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["model_count"], 2)

    def test_cli_writes_output_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "sample.xml"
            output = tmp_path / "extract" / "band_assets.json"
            source.write_text(SAMPLE_XML, encoding="utf-8")

            code = main([str(source), "--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(payload["group_count"], 1)


if __name__ == "__main__":
    unittest.main()
