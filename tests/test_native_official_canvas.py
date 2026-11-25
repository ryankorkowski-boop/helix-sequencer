import numpy as np
import pytest
from tools.native_official_canvas import bbox, house_pane


def test_house_pane_requires_exact_stacked_pair():
    rows = [('0x1',250,608,2,175), ('0x2',250,608,2,807), ('0x3',1780,1031,764,361)]
    assert house_pane(rows) == '0x2'
    with pytest.raises(ValueError):
        house_pane(rows[:1])
    with pytest.raises(ValueError):
        house_pane(rows+[('0x4',250,608,2,1500)])


def test_bbox_only_uses_visible_pixels():
    frame = np.zeros((20,30,3), dtype=np.uint8)
    assert bbox(frame) is None
    frame[2:6,10:20,0]=255
    assert bbox(frame)==[10,2,19,5]
