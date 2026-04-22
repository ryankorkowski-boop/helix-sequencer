from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import build_helixville_layout


class BuildHelixvilleLayoutTests(unittest.TestCase):
    def test_build_layout_imports_xmodels_and_writes_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            base_layout = root / "xlights_rgbeffects.xml"
            xmodel_root = root / "models"
            output_layout = root / "outputs" / "xlights_rgbeffects.xml"

            base_layout.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<xrgb>
  <models>
    <model name="AC Roofline" DisplayAs="Single Line" StartChannel="1" WorldPosX="0" WorldPosY="0" WorldPosZ="0" />
  </models>
  <modelGroups />
</xrgb>
""",
                encoding="utf-8",
            )

            xmodel_root.mkdir(parents=True)
            (xmodel_root / "demo.xmodel").write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<custommodel name="Demo Model" parm1="4" parm2="4" StringType="RGB Nodes" CustomModel="1,2,3,4;5,6,7,8" />
""",
                encoding="utf-8",
            )

            result = build_helixville_layout.build_layout(
                base_layout=base_layout,
                xmodel_root=xmodel_root,
                output_layout=output_layout,
            )

            self.assertTrue(output_layout.exists())
            self.assertEqual(result["imported_xmodel_count"], 1)
            xml_text = output_layout.read_text(encoding="utf-8")
            self.assertIn("HELIXVILLE_IMPORTED_CUSTOM_MODELS", xml_text)
            self.assertIn("HELIXVILLE_OS_Demo Model", xml_text)


if __name__ == "__main__":
    unittest.main()
