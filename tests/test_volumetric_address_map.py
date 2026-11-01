import csv
import pytest

from core.volumetric_grid import VolumetricGrid
from core.volumetric_address_map import write_address_map


def test_address_map_unique_contiguous_and_physical(tmp_path):
    grid = VolumetricGrid(width_ft=2, depth_ft=2, height_ft=2, spacing_in=12,
                          zone_poles=2)
    receipt = write_address_map(tmp_path / "addresses.csv", grid)
    assert receipt["pixels"] == 27
    assert receipt["channels"] == 81
    assert receipt["native_xlights_verified"] is False
    with (tmp_path / "addresses.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 27
    assert [int(r["channel_r"]) for r in rows] == list(range(1, 82, 3))
    assert len({(r["grid_x"], r["grid_y"], r["grid_z"]) for r in rows}) == 27
    assert rows[0]["grid_z"] == "0"
    assert rows[1]["grid_z"] == "1"
    assert rows[2]["grid_z"] == "2"
    assert rows[3]["grid_z"] == "2"


def test_address_map_cap_prevents_large_write(tmp_path):
    grid = VolumetricGrid()
    with pytest.raises(ValueError, match="safety cap"):
        write_address_map(tmp_path / "addresses.csv", grid, max_pixels=100)
    assert not (tmp_path / "addresses.csv").exists()
