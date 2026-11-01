"""Bounded, reproducible 3D grid preview frames and installation manifests.

These are engineering preview artifacts, NOT native xLights models/FSEQ.
"""
from __future__ import annotations

import json
from pathlib import Path

from core.volumetric_grid import VolumetricGrid
from core.birdsong_volumetric_adapter import VolumetricCue, sample_cue_pixels


def grid_manifest(grid: VolumetricGrid) -> dict:
    nx, ny, nz = grid.shape
    zx, zy = grid.zone_count
    return {
        "schema": "helix.volumetric_grid.preview.v1",
        "units": "feet",
        "dimensions_ft": [grid.width_ft, grid.depth_ft, grid.height_ft],
        "spacing_in": grid.spacing_in,
        "shape": [nx, ny, nz],
        "pixel_count": grid.pixel_count,
        "rgb_channel_count": grid.pixel_count * 3,
        "zone_poles": grid.zone_poles,
        "zone_count": [zx, zy],
        "mapping": "zone-row-serpentine, alternating vertical pole direction",
        "native_xlights_verified": False,
        "hardware_wiring_qualified": False,
    }


def write_grid_manifest(path: str | Path, grid: VolumetricGrid) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(grid_manifest(grid), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def write_sparse_preview(
    path: str | Path,
    grid: VolumetricGrid,
    cues: tuple[VolumetricCue, ...],
    *,
    time_ms: int,
    threshold: float = 0.15,
    max_pixels: int = 10000,
) -> dict:
    """Stream sparse coordinate/intensity samples, capped to avoid huge previews.

    Each line is JSON; first line is metadata. No full frame buffer allocated.
    """
    if max_pixels < 1:
        raise ValueError("max_pixels must be positive")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between zero and one")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    emitted = 0
    clipped = False
    with target.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"schema": "helix.volumetric_sparse_preview.v1", "time_ms": time_ms}) + "\n")
        for cue in cues:
            for pixel, intensity in sample_cue_pixels(cue, grid, time_ms=time_ms):
                if intensity < threshold:
                    continue
                if emitted >= max_pixels:
                    clipped = True
                    break
                x, y, z = grid.xyz_ft(*pixel)
                handle.write(json.dumps({"xyz_ft": [x, y, z], "intensity": round(intensity, 6),
                                         "motif": cue.motif, "phrase_id": cue.phrase_id}) + "\n")
                emitted += 1
            if clipped:
                break
    return {"path": str(target), "emitted_pixels": emitted, "truncated": clipped}
