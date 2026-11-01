"""Small-scale opt-in Birdsong volumetric proof-of-concept runner.

Generates engineering artifacts, not native xLights/FSEQ or an MP4.
Example: python -m tools.volumetric_demo --output-dir /tmp/helix-volumetric
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.birdsong_volumetric_adapter import plan_volumetric_birdsong
from core.feature_state import FeatureState
from core.volumetric_address_map import write_address_map
from core.volumetric_grid import VolumetricGrid
from core.volumetric_preview import write_grid_manifest, write_sparse_preview


def run_demo(output_dir: str | Path, *, spacing_in: float = 12.0) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    grid = VolumetricGrid(width_ft=8, depth_ft=8, height_ft=4,
                          spacing_in=spacing_in, zone_poles=4)
    state = FeatureState()
    # Deterministic demonstration frames; not claimed as real audio.
    frames = [
        state.update(0, energy=0.9, onset=0.9, centroid=900,
                     low=0.8, mid=0.1, high=0.1, beat_phase=0.1, time_s=1.0),
        state.update(1, energy=0.9, onset=0.9, centroid=6500,
                     low=0.1, mid=0.2, high=0.9, beat_phase=0.5, time_s=1.2),
    ]
    cues = plan_volumetric_birdsong(frames, grid, enabled=True,
                                   max_zones_per_phrase=4)
    manifest = write_grid_manifest(out / "grid.json", grid)
    address_receipt = write_address_map(out / "addresses.csv", grid)
    cue_data = [cue.__dict__ for cue in cues]
    (out / "cues.json").write_text(json.dumps(cue_data, indent=2) + "\n",
                                   encoding="utf-8")
    preview_receipt = write_sparse_preview(
        out / "frame_1000ms.jsonl", grid, cues, time_ms=1000,
        threshold=0.1, max_pixels=10000,
    )
    result = {
        "status": "synthetic_engineering_preview_not_native_xlights",
        "pixel_count": grid.pixel_count,
        "cue_count": len(cues),
        "manifest": str(manifest),
        "address_map": address_receipt,
        "preview": preview_receipt,
    }
    (out / "receipt.json").write_text(json.dumps(result, indent=2) + "\n",
                                       encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="evidence/volumetric_demo")
    parser.add_argument("--spacing-in", type=float, choices=(12.0, 16.0),
                        default=12.0)
    args = parser.parse_args()
    print(json.dumps(run_demo(args.output_dir, spacing_in=args.spacing_in),
                     indent=2))


if __name__ == "__main__":
    main()
