from core.volumetric_grid import VolumetricGrid, sample_spatial_intensity
import pytest


def test_city_block_counts():
    assert VolumetricGrid(spacing_in=16).shape == (226, 226, 4)
    assert VolumetricGrid(spacing_in=16).pixel_count == 204304
    assert VolumetricGrid(spacing_in=12).pixel_count == 453005


def test_zone_serpentine_unique_and_complete():
    grid = VolumetricGrid(width_ft=4, depth_ft=4, height_ft=4, spacing_in=12, zone_poles=3)
    wired = [p for zx in range(grid.zone_count[0]) for zy in range(grid.zone_count[1])
             for p in grid.zone_wiring(zx, zy)]
    assert len(wired) == len(set(wired)) == grid.pixel_count
    first = list(grid.zone_wiring(0, 0))
    assert first[:5] == [(0, 0, z) for z in range(5)]
    assert first[5:10] == [(1, 0, z) for z in reversed(range(5))]


def test_sampling_bounded_deterministic():
    grid = VolumetricGrid()
    xyz = grid.xyz_ft(2, 3, 1)
    for motif in ("wave_sweep", "pulse_cascade", "spiral", "orbit", "sparkle_field"):
        a = sample_spatial_intensity(xyz, grid, time_s=2.5, motif=motif)
        assert 0 <= a <= 1
        assert a == sample_spatial_intensity(xyz, grid, time_s=2.5, motif=motif)
    with pytest.raises(ValueError):
        sample_spatial_intensity(xyz, grid, time_s=0, motif="invalid")
