from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools import showcase_clip


class ShowcaseClipTests(unittest.TestCase):
    def _write_xsq(self, root_dir: Path) -> Path:
        root = ET.Element("xsequence")
        head = ET.SubElement(root, "head")
        ET.SubElement(head, "song").text = "Demo"
        ET.SubElement(head, "comment").text = ""
        ET.SubElement(head, "mediaFile").text = "demo.wav"
        ET.SubElement(head, "sequenceDuration").text = "60.000"
        effects_root = ET.SubElement(root, "ElementEffects")
        element = ET.SubElement(effects_root, "Element", {"name": "Model 1", "type": "model"})
        layer = ET.SubElement(element, "EffectLayer")
        ET.SubElement(layer, "Effect", {"name": "On", "startTime": "5000", "endTime": "12000"})
        ET.SubElement(layer, "Effect", {"name": "Bars", "startTime": "22000", "endTime": "26000"})
        path = root_dir / "demo.xsq"
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        return path

    def test_build_showcase_clip_trims_and_rebases_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_dir = Path(tmp)
            xsq_path = self._write_xsq(root_dir)
            out_xsq, out_audio = showcase_clip.build_showcase_clip(
                xsq_path=xsq_path,
                out_dir=root_dir / "clips",
                start_s=4.0,
                duration_s=20.0,
                audio_path=None,
            )
            self.assertIsNone(out_audio)
            tree = ET.parse(out_xsq)
            root = tree.getroot()
            self.assertEqual(root.findtext("./head/sequenceDuration"), "20.000")
            self.assertIn("showcase_004s_20s", root.findtext("./head/song") or "")
            effects = root.findall(".//Effect")
            self.assertEqual(len(effects), 2)
            starts = [effect.attrib["startTime"] for effect in effects]
            ends = [effect.attrib["endTime"] for effect in effects]
            self.assertEqual(starts, ["1000", "18000"])
            self.assertEqual(ends, ["8000", "20000"])


if __name__ == "__main__":
    unittest.main()
