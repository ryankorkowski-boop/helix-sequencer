import json
from core.volumetric_grid import VolumetricGrid
from core.volumetric_preview import grid_manifest, write_grid_manifest, write_sparse_preview
from core.birdsong_volumetric_adapter import VolumetricCue


def test_manifest_and_sparse_preview(tmp_path):
    grid = VolumetricGrid(width_ft=4, depth_ft=4, height_ft=4, spacing_in=12, zone_poles=3)
    data = grid_manifest(grid)
    assert data["pixel_count"] == 125
    assert data["native_xlights_verified"] is False
    output = write_grid_manifest(tmp_path / "grid.json", grid)
    assert json.loads(output.read_text()) == data
    cue = VolumetricCue("phrase1", "wave_sweep", 1000, 180, 1.0, 0, 0)
    receipt = write_sparse_preview(tmp_path / "preview.jsonl", grid, (cue,),
                                   time_ms=1000, threshold=0, max_pixels=7)
    assert receipt["emitted_pixels"] == 7
    assert receipt["truncated"] is True
    rows = [json.loads(line) for line in (tmp_path / "preview.jsonl").read_text().splitlines()]
    assert len(rows) == 8
    assert all(0 <= row["intensity"] <= 1 for row in rows[1:])
