from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.write_helixville4_band_assets import write_band_assets


class WriteHelixville4BandAssetsTests(unittest.TestCase):
    def test_write_band_assets_creates_svgs_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = write_band_assets(Path(tmp))
            manifest = Path(payload["manifest"])
            svg_files = [Path(path) for path in payload["svg_files"]]
            decoded = json.loads(manifest.read_text(encoding="utf-8"))

            self.assertEqual(payload["asset_count"], 5)
            self.assertEqual(len(svg_files), 5)
            self.assertTrue(manifest.exists())
            self.assertEqual(decoded["asset_count"], 5)
            for svg_file in svg_files:
                text = svg_file.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("<svg"))
                self.assertIn("data-submodel=", text)
                self.assertIn("</svg>", text)


if __name__ == "__main__":
    unittest.main()
