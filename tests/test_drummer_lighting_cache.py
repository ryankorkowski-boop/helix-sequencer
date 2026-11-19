import numpy as np
import pytest
from animation.articulated_source_drummer import ArticulatedDrummer,BandLighting
from tools.render_drummer_v3_preview import TARGETS


@pytest.mark.parametrize('natural',[False,True])
def test_cached_static_lighting_preserves_every_pixel_of_moving_arms(natural):
    hits=[dict(time=.2,target=TARGETS[1],side='left',velocity=.6),
          dict(time=.6,target=TARGETS[1],side='right',velocity=.8),
          dict(time=1.,target=TARGETS[6],side='left',velocity=.7)]
    reference=ArticulatedDrummer(hits,lighting=BandLighting(),natural_arms=natural,cache_lighting=False)
    cached=ArticulatedDrummer(hits,lighting=BandLighting(),natural_arms=natural,cache_lighting=True)
    for i in range(18):
        time=i/10;active=(TARGETS[1],) if i%4<2 else ()
        tail={TARGETS[6]:max(0,1-(time-1)) if time>=1 else 0,TARGETS[7]:0}
        expected=np.asarray(reference.frame(time,active,tail))
        assert np.array_equal(expected,np.asarray(cached.frame(time,active,tail)))
        # The same cached kit must still allow new arm poses and torso levels.
        if i==7:
            reference.lighting=BandLighting(idle_body=.9)
            cached.lighting=BandLighting(idle_body=.9)
    assert len(cached._kit_cache)<=24


def test_cache_is_bounded_and_reacts_to_changed_tail_levels():
    player=ArticulatedDrummer([],cache_lighting=True)
    for i in range(28):player.frame(i/20,(),{TARGETS[6]:i/28})
    assert len(player._kit_cache)==24
