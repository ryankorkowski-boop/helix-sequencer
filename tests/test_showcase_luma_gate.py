"""Low-value dark and frozen sequences must not qualify as new show videos."""
import numpy as np
import pytest
from tools.verify_showcase_luma import evaluate_showcase_frames


def test_obscured_bells_like_clip_fails_all_readability_gates():
    frames=np.full((24,90,160),6,dtype=np.uint8)
    for i in range(len(frames)):
        frames[i,40:44,30+i:34+i]=70
    qc=evaluate_showcase_frames(frames)
    assert qc["passed"] is False
    assert not qc["checks"]["median_stage_luminance"]
    assert not qc["checks"]["bright_stage_area"]


def test_bright_but_frozen_rig_is_not_accepted():
    frames=np.full((24,90,160),6,dtype=np.uint8)
    frames[:,20:60,20:95]=200
    qc=evaluate_showcase_frames(frames)
    assert qc["passed"] is False
    assert qc["checks"]["median_stage_luminance"]
    assert not qc["checks"]["visible_stage_motion"]


def test_bright_dynamic_real_geometry_analogue_meets_numeric_gate():
    frames=np.full((24,90,160),6,dtype=np.uint8)
    for i in range(len(frames)):
        x=15+(i*5)%90
        frames[i,22:52,x:x+40]=190
    qc=evaluate_showcase_frames(frames)
    assert qc["passed"] is True
    assert qc["frames"]==24 and qc["sample_fps"]==2
    assert all(qc["checks"].values())


@pytest.mark.parametrize("bad", [
    np.zeros((2,90,160),dtype=np.uint8),
    np.zeros((24,90,160),dtype=np.int16),
    np.zeros((24,100,160),dtype=np.uint8),
])
def test_bad_decode_shape_or_dtype_rejected(bad):
    with pytest.raises(ValueError):
        evaluate_showcase_frames(bad)
