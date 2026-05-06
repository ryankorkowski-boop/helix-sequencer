from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from xlights import layout_sync, timing_tracks, xml_io


def _display_rows(root: ET.Element) -> dict[str, ET.Element]:
    display = xml_io.find_root_child(root, "DisplayElements")
    assert display is not None
    return {row.attrib["name"]: row for row in list(display)}


class LayoutViewTests(unittest.TestCase):
    def test_master_keeps_auto_timing_visible_and_hidetimings_excludes_it(self) -> None:
        root = ET.Element("Sequence")
        display = ET.SubElement(root, "DisplayElements")
        ET.SubElement(
            display,
            "Element",
            {
                "collapsed": "0",
                "type": "timing",
                "name": "AUTO Snowman Band v28.1",
                "visible": "0",
                "views": "hidetimings",
                "active": "0",
            },
        )
        ET.SubElement(
            display,
            "Element",
            {
                "collapsed": "0",
                "type": "model",
                "name": "HX_LOT_SNOWMAN_BAND_STAGE",
                "visible": "1",
            },
        )

        layout_sync.normalize_display_views(root, force=True)

        rows = _display_rows(root)
        timing = rows["AUTO Snowman Band v28.1"]
        model = rows["HX_LOT_SNOWMAN_BAND_STAGE"]
        self.assertEqual(timing.attrib["visible"], "1")
        self.assertEqual(timing.attrib["views"], "")
        self.assertEqual(model.attrib["views"], timing_tracks.HIDE_TIMINGS_VIEW_NAME)

    def test_sync_to_layout_preserves_groups_in_master_and_hidetimings_view(self) -> None:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        layout_path = Path(tempdir.name) / "xlights_rgbeffects.xml"
        layout_path.write_text(
            '<xrgb><models><model name="HX_MODEL" /></models>'
            '<modelGroups><modelGroup name="HX_GROUP" models="HX_MODEL" /></modelGroups></xrgb>',
            encoding="utf-8",
        )
        root = ET.Element("Sequence")
        ET.SubElement(root, "DisplayElements")
        ET.SubElement(root, "ElementEffects")
        xsq = type("Xsq", (), {"root": root, "elements": {}})()

        layout_sync.sync_xsq_to_layout(xsq, layout_path)
        layout_sync.ensure_master_view_models(root)

        rows = _display_rows(root)
        self.assertIn("HX_GROUP", rows)
        self.assertIn("HX_MODEL", rows)
        self.assertEqual(rows["HX_GROUP"].attrib["visible"], "1")
        self.assertEqual(rows["HX_GROUP"].attrib["views"], timing_tracks.HIDE_TIMINGS_VIEW_NAME)
        self.assertEqual(rows["HX_MODEL"].attrib["views"], timing_tracks.HIDE_TIMINGS_VIEW_NAME)


if __name__ == "__main__":
    unittest.main()
