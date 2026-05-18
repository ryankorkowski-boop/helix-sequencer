from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools import export_helixville4_band_xmodels as exporter


class ExportHelixville4BandXmodelsTests(unittest.TestCase):
    def test_build_xmodel_element_preserves_name_and_custom_model(self) -> None:
        spec = exporter.FULL_BAND_SPECS[0]

        element = exporter.build_xmodel_element(spec)

        self.assertEqual(element.tag, "custommodel")
        self.assertEqual(element.attrib["name"], "HX_SNOWMAN_DRUMMER")
        self.assertEqual(element.attrib["StringType"], "RGB Nodes")
        self.assertIn("CustomModel", element.attrib)
        self.assertGreater(len(element.findall("subModel")), 5)
        self.assertEqual(element.find("subModel").attrib["name"], "DefaultRenderBuffer")  # type: ignore[union-attr]

    def test_export_band_xmodels_writes_all_members(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = exporter.export_band_xmodels(Path(tmp))
            xmodels = sorted((Path(tmp) / "xmodels").glob("*.xmodel"))
            sequence_target_xmodels = sorted((Path(tmp) / "sequence_target_xmodels").glob("*.xmodel"))

            self.assertEqual(payload["model_count"], 5)
            self.assertEqual(len(xmodels), 5)
            self.assertEqual(payload["sequence_target_model_count"], 10)
            self.assertEqual(len(sequence_target_xmodels), 10)
            names = {ET.parse(path).getroot().attrib["name"] for path in xmodels}
            sequence_target_names = {ET.parse(path).getroot().attrib["name"] for path in sequence_target_xmodels}

        self.assertEqual(
            names,
            {
                "HX_SNOWMAN_DRUMMER",
                "HX_SNOWMAN_BASSIST",
                "HX_SNOWMAN_GUITARIST",
                "HX_SNOWMAN_SINGER",
                "HX_SNOWMAN_SINGER_FEMALE",
            },
        )
        self.assertIn("HX_SNOWMAN_DRUMMER_BODY", sequence_target_names)
        self.assertIn("HX_SNOWMAN_DRUMMER_INSTRUMENT", sequence_target_names)
        self.assertIn("HX_SNOWMAN_SINGER_FEMALE_INSTRUMENT", sequence_target_names)


if __name__ == "__main__":
    unittest.main()
