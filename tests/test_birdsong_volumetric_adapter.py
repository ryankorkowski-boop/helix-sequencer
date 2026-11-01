from core.birdsong_volumetric_adapter import plan_volumetric_birdsong, sample_cue_pixels
from core.feature_state import FeatureState
from core.volumetric_grid import VolumetricGrid


def test_opt_in_and_bounded_zone_cues():
    state = FeatureState()
    frames = [state.update(0, energy=0.9, onset=0.95, low=0.8, mid=0.1,
                           high=0.1, time_s=1.0)]
    grid = VolumetricGrid(width_ft=4, depth_ft=4, height_ft=4, spacing_in=12, zone_poles=3)
    assert plan_volumetric_birdsong(frames, grid) == ()
    cues = plan_volumetric_birdsong(frames, grid, enabled=True, max_zones_per_phrase=2)
    assert len(cues) == 2
    assert cues == plan_volumetric_birdsong(frames, grid, enabled=True, max_zones_per_phrase=2)
    assert cues[0].motif == "pulse_cascade"
    pixels = list(sample_cue_pixels(cues[0], grid, time_ms=1000))
    assert len(pixels) == 3 * 3 * 5
    assert all(0 <= value <= 1 for _, value in pixels)
    assert list(sample_cue_pixels(cues[0], grid, time_ms=0)) == []
