"""Verify front projections contain exactly the native exported coordinates."""
import csv
import json
import xml.etree.ElementTree as ET

from tools.audit_native_snowman_geometry import audit
from tools.preview_native_snowman_geometry import render


def test_native_front_projection_is_exact_coordinate_plot(tmp_path):
    result = audit(tmp_path)
    previews = render(tmp_path)
    assert len(previews) == len(result["models"]) == 14
    for model, preview in zip(result["models"], previews):
        root = ET.parse(preview).getroot()
        circles = root.findall("{http://www.w3.org/2000/svg}circle")
        with (tmp_path / model["coordinate_csv"]).open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(circles) == len(rows) == model["geometry_positions"]
        assert "NOT DRILL TEMPLATE" in preview.read_text(encoding="utf-8")
