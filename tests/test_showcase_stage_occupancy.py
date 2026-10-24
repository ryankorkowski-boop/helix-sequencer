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
