import numpy as np
from tools.build_current_comparison import pixel_grid_3d,layout


def test_grid_is_a_real_48inch_tall_volume_with_12inch_spacing():
    g=pixel_grid_3d()
    points=np.concatenate([m.points for m in g.models])
    assert len(points)==49*49*5
    assert len(np.unique(points,axis=0))==len(points)
    np.testing.assert_array_equal(np.ptp(points,axis=0),[48,4,48])
    for axis in range(3):
        np.testing.assert_array_equal(np.diff(np.unique(points[:,axis])),1)
    assert {m.details['musical_role'] for m in g.models}=={'keyboardist','guitarist','bassist','drummer'}


def test_grid_uses_contiguous_nonoverlapping_native_channels():
    g,_=layout(13,{},duration=36)
    assert g.models[0].start==1
    for a,b in zip(g.models,g.models[1:]):assert b.start==a.start+a.channels
    assert g.models[-1].start+g.models[-1].channels-1==49*49*5*3
