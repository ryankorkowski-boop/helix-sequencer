"""Integration smoke test for the executable volumetric demonstration."""
import csv
import json

from tools.volumetric_demo import run_demo


def test_demo_emits_complete_consistent_artifacts(tmp_path):
    receipt = run_demo(tmp_path)
    assert receipt["status"] == "synthetic_engineering_preview_not_native_xlights"
    assert receipt["cue_count"] >= 2
    manifest = json.loads((tmp_path / "grid.json").read_text())
    assert manifest["pixel_count"] == receipt["pixel_count"]
    assert manifest["native_xlights_verified"] is False
    with (tmp_path / "addresses.csv").open(newline="") as handle:
        addresses = list(csv.DictReader(handle))
    assert len(addresses) == receipt["pixel_count"]
    assert len({(row["grid_x"], row["grid_y"], row["grid_z"])
                for row in addresses}) == receipt["pixel_count"]
    cues = json.loads((tmp_path / "cues.json").read_text())
    assert len(cues) == receipt["cue_count"]
    preview = [json.loads(row) for row in
               (tmp_path / "frame_1000ms.jsonl").read_text().splitlines()]
    assert preview[0]["schema"] == "helix.volumetric_sparse_preview.v1"
    assert len(preview) > 1
    assert receipt["preview"]["emitted_pixels"] == len(preview) - 1
    assert receipt["address_map"]["channels"] == receipt["pixel_count"] * 3
