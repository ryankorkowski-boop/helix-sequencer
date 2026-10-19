import numpy as np
from models.review_3d_scene import Review3DScene


def test_hihat_uses_foot_without_stick_or_kick():
    scene=Review3DScene()
    scene.configure_drummer([dict(target='HX_SNOWMAN_DRUMMER_V3_HI_HAT',time=0.1,side='left',velocity=1)])
    scene.update_drummer(0.0)
    idle=[scene.instances[scene.hihat_foot]['matrix'].copy(),scene.instances[scene.hihat_pedal]['matrix'].copy()]
    sticks=[scene.instances[scene.drummer_rigs[side]['ids'][-1]]['matrix'].copy() for side in ('left','right')]
    kick=scene.instances[scene.kick_beater]['matrix'].copy()
    scene.update_drummer(0.1)
    assert not np.allclose(idle[0],scene.instances[scene.hihat_foot]['matrix'])
    assert not np.allclose(idle[1],scene.instances[scene.hihat_pedal]['matrix'])
    for side,expected in zip(('left','right'),sticks):
        np.testing.assert_allclose(scene.instances[scene.drummer_rigs[side]['ids'][-1]]['matrix'],expected)
    np.testing.assert_allclose(scene.instances[scene.kick_beater]['matrix'],kick)
    assert not scene.drum_contact_proof
    scene.update_drummer(0.25)
    np.testing.assert_allclose(scene.instances[scene.hihat_foot]['matrix'],idle[0])
