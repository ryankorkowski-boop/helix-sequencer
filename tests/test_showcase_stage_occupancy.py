"""Stage occupancy must reject small bright moving islands in black frames."""
import numpy as np
from tools.verify_showcase_luma import evaluate_showcase_frames, HEIGHT, WIDTH


def test_tiny_center_band_fails_stage_occupancy():
    frames=np.zeros((12,HEIGHT,WIDTH),dtype=np.uint8)
    for i in range(len(frames)):
        frames[i,35:50,65+i%3:90+i%3]=255
    report=evaluate_showcase_frames(frames)
    assert report['checks']['visible_stage_width'] is False
    assert report['checks']['visible_stage_height'] is False
    assert report['passed'] is False


def test_wide_tall_band_passes_occupancy_dimensions():
    frames=np.zeros((12,HEIGHT,WIDTH),dtype=np.uint8)
    for i in range(len(frames)):
        frames[i,20:70,30+i%2:130+i%2]=255
    report=evaluate_showcase_frames(frames)
    assert report['checks']['visible_stage_width'] is True
    assert report['checks']['visible_stage_height'] is True


def test_static_cast_rejects_opening_crop_that_the_global_median_misses():
    frames=np.zeros((20,HEIGHT,WIDTH),dtype=np.uint8)
    for i in range(len(frames)):
        frames[i,20:70,20:130]=100+(i%2)*40
    frames[:4]=0
    for i in range(4):frames[i,40:70,10:26]=120+(i%2)*40
    assert evaluate_showcase_frames(frames)['passed']
    report=evaluate_showcase_frames(frames,static_cast=True)
    assert not report['passed']
    assert report['checks']['opening_static_cast_framing'] is False
