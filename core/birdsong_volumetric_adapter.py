"""Optional bridge between Birdsong phrase planning and 3D grid zones."""
from dataclasses import dataclass
from typing import Sequence

from core.birdsong_issue2_runtime import BirdsongRuntimeConfig, plan_birdsong_runtime
from core.feature_state import FeatureStateFrame
from core.volumetric_grid import VolumetricGrid, sample_spatial_intensity


@dataclass(frozen=True)
class VolumetricCue:
    phrase_id: str
    motif: str
    start_ms: int
    duration_ms: int
    intensity: float
    zone_x: int
    zone_y: int


def plan_volumetric_birdsong(
    frames: Sequence[FeatureStateFrame],
    grid: VolumetricGrid,
    *,
    enabled: bool = False,
    max_zones_per_phrase: int = 4,
) -> tuple[VolumetricCue, ...]:
    if enabled is not True:
        return ()
    if max_zones_per_phrase < 1:
        raise ValueError("max_zones_per_phrase must be positive")
    plan = plan_birdsong_runtime(
        frames, ("volumetric_grid",),
        config=BirdsongRuntimeConfig(enabled=True, max_targets_per_frame=1),
    )
    zx, zy = grid.zone_count
    cues = []
    for index, phrase in enumerate(plan.phrase_snapshots):
        zone_total = zx * zy
        cue_count = min(max_zones_per_phrase, zone_total)
        # Spread sparse cues across the complete footprint instead of clustering
        # every phrase in the first few adjacent zones. The phase shift makes
        # successive phrases deterministic but spatially progressive.
        for offset in range(cue_count):
            flat = ((offset * zone_total) // cue_count + index) % zone_total
            cues.append(VolumetricCue(
                phrase.phrase_id, phrase.motif, phrase.start_ms, 180,
                phrase.intensity, flat % zx, flat // zx,
            ))
    return tuple(cues)


def sample_cue_pixels(cue: VolumetricCue, grid: VolumetricGrid, *, time_ms: int):
    """Yield individual mapped pixels without constructing a full-volume buffer."""
    if not cue.start_ms <= time_ms < cue.start_ms + cue.duration_ms:
        return
    for pixel in grid.zone_wiring(cue.zone_x, cue.zone_y):
        yield pixel, sample_spatial_intensity(
            grid.xyz_ft(*pixel), grid, time_s=time_ms / 1000.0,
            motif=cue.motif, energy=cue.intensity,
        )
