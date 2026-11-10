from __future__ import annotations

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helpers.helixville4_finished_band import add_finished_helixville4_band_models


EXPECTED_FINISHED_BAND_MODELS = {
    "HX_SNOWMAN_DRUMMER",
    "HX_SNOWMAN_BASSIST",
    "HX_SNOWMAN_GUITARIST",
    "HX_SNOWMAN_SINGER",
    "HX_SNOWMAN_SINGER_FEMALE",
}


def test_finished_band_helper_exports_all_members_without_placeholder_marker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout_path = Path(tmp) / "layout.xml"
        layout_path.write_text("<xrgb><models/><modelGroups/></xrgb>", encoding="utf-8")
        add_finished_helixville4_band_models(layout_path)
        root = ET.parse(layout_path).getroot()
        models = {model.attrib.get("name"): model for model in root.findall(".//model")}

    assert set(models) == EXPECTED_FINISHED_BAND_MODELS
    assert all(model.attrib.get("HelixImplementationState") != "placeholder_pending_finished_exporter" for model in models.values())
    assert all(int(model.attrib.get("HelixNodeCount", "0")) > 100 for model in models.values())
