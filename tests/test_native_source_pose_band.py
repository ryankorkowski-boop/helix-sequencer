import numpy as np
import pytest
from tools.native_source_pose_band import select_states,vertices
from models.band_performance_scene import line_matrix


def test_states_are_actual_source_frames_and_preserve_frame_clock():
    poses=np.zeros((720,3,3),'f4')
    poses[120:240,:,0]=1;poses[240:360,:,1]=2;poses[360:,:,2]=3
    selected,states,error=select_states(poses,8)
    assert len(states)==720 and len(selected)==4 and error==0
    np.testing.assert_array_equal(poses[selected][states],poses)
    assert np.flatnonzero(np.diff(states)).tolist()==[119,239,359]


def test_more_states_reduce_measured_geometry_error_deterministically():
    t=np.linspace(0,2*np.pi,720)
    p=np.stack((np.sin(t),np.cos(t),t/10),axis=1)[:,None,:]
    a=select_states(p,8);b=select_states(p,24);c=select_states(p,24)
    assert b[2]<=a[2]
    np.testing.assert_array_equal(b[0],c[0]);np.testing.assert_array_equal(b[1],c[1])


def test_source_rod_endpoints_reach_the_authored_contact_plane():
    a=np.array([1.,2.,3.]);b=np.array([4.,6.,8.])
    pts=vertices(dict(kind='cylinder',matrix=line_matrix(a,b,.04)))
    direction=(b-a)/np.linalg.norm(b-a)
    projection=(pts-a)@direction
    assert projection.min()==pytest.approx(0,abs=1e-5)
    assert projection.max()==pytest.approx(np.linalg.norm(b-a),abs=1e-5)


@pytest.mark.parametrize('poses,limit',[(np.zeros((0,3,3)),8),
    (np.ones((5,3)),8),(np.full((5,3,3),np.nan),8),
    (np.zeros((5,3,3)),0),(np.zeros((5,3,3)),129)])
def test_invalid_pose_input_rejects(poses,limit):
    with pytest.raises(ValueError):select_states(poses,limit)
