from types import SimpleNamespace
import numpy as np
import pytest
from tools.build_spatial_review import band_curves


def test_singer_visibility_preserves_source_vocal_and_arm_cues():
    model = SimpleNamespace(details={'review_role': 'lead'},
        submodels={'BODY':[1], 'EYES':[2], 'MOUTH_AI':[3], 'ARM_ACTIVE':[4]})
    p = SimpleNamespace(n=8, keyboard_events=[], voice_lanes=np.ones((8,2)),
                        voice_energy=np.arange(16).reshape(8,2)/20)
    original = band_curves(model,p)
    revised = band_curves(model,p,body_level=.55)
    np.testing.assert_allclose(revised['BODY'],.55)
    for part in original:
        if part!='BODY':np.testing.assert_array_equal(revised[part],original[part])


def test_drummer_visibility_preserves_all_hit_cues(monkeypatch):
    monkeypatch.setattr('tools.render_refined_helix_band.physical_hits',
        lambda _: [dict(component='SNARE',side='left',time=.1,velocity=.8)])
    m=SimpleNamespace(details={'review_role':'drummer'},
        submodels={'BASE_DIM':[1], 'SNARE_LEFT':[2]})
    p=SimpleNamespace(n=8,keyboard_events=[],row={'drummer_xsq':'fixture'})
    original=band_curves(m,p); revised=band_curves(m,p,body_level=.55)
    np.testing.assert_array_equal(original['SNARE_LEFT'],revised['SNARE_LEFT'])
    assert np.count_nonzero(revised['SNARE_LEFT'])==1


@pytest.mark.parametrize('level',[float('nan'),float('inf'),-1,1.1])
def test_invalid_levels_reject(level):
    with pytest.raises(ValueError):band_curves(None,None,body_level=level)
