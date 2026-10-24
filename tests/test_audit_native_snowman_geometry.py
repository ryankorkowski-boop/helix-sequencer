"""Regression coverage for native Snowman Band physical-geometry audit."""
import csv
import json

from tools.audit_native_snowman_geometry import audit
from models.native_review_band import VISEMES


def test_native_geometry_audit_exports_actual_models(tmp_path):
    result = audit(tmp_path)
    assert len(result["models"]) == 14
    assert {m["mode"] for m in result["models"]} == {"pixel", "ac16"}
    assert result["physical_dimensions_verified"] is False
    assert result["controller_mapping_verified"] is False
    drummer = next(m for m in result["models"] if m["name"] == "HX_SNOW_DRUMMER_AC16")
    assert set(drummer["submodels"]) == {
        "BASE_DIM", "CYMBAL_LEFT", "TOM_FLOOR", "TOM_MID",
        "SNARE_LEFT", "SNARE_RIGHT", "KICK", "TOM_HIGH",
        "HI_HAT", "CYMBAL_RIGHT",
    }
    for role in ("LEAD", "HARMONY"):
        singer = next(m for m in result["models"] if m["name"] == f"HX_SNOW_{role}_AC16")
        mouths = [singer["submodels"][f"MOUTH_{v}"][0] for v in VISEMES]
        assert len(mouths) == len(set(mouths)) == 10
        assert len(singer["submodels"]) == 14
    for model in result["models"]:
        with (tmp_path / model["coordinate_csv"]).open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == model["geometry_positions"]
        assert all(row["node_or_circuit"].isdigit() for row in rows)
    persisted = json.loads((tmp_path / "audit.json").read_text())
    assert persisted["models"] == result["models"]
