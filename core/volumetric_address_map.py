"""Controller-neutral, streamed physical pixel address mapping.

This is an installation planning CSV, not an xLights import or a wiring
approval. Channel numbering is one-based RGB and contiguous across zones.
"""
from __future__ import annotations

import csv
from pathlib import Path

from core.volumetric_grid import VolumetricGrid


def write_address_map(
    path: str | Path, grid: VolumetricGrid, *, max_pixels: int = 500000,
) -> dict[str, object]:
    """Write deterministic zone-serpentine RGB addresses without a pixel list."""
    if max_pixels < 1:
        raise ValueError("max_pixels must be positive")
    if grid.pixel_count > max_pixels:
        raise ValueError("grid exceeds explicit address-map safety cap")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    address = 1
    zx, zy = grid.zone_count
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("zone_x", "zone_y", "zone_pixel", "grid_x", "grid_y",
                         "grid_z", "x_ft", "y_ft", "z_ft", "channel_r",
                         "channel_g", "channel_b"))
        for zone_y in range(zy):
            for zone_x in range(zx):
                for zone_pixel, pixel in enumerate(grid.zone_wiring(zone_x, zone_y)):
                    xyz = grid.xyz_ft(*pixel)
                    writer.writerow((zone_x, zone_y, zone_pixel, *pixel, *xyz,
                                     address, address + 1, address + 2))
                    address += 3
    return {"path": str(target), "pixels": (address - 1) // 3,
            "channels": address - 1, "native_xlights_verified": False}
