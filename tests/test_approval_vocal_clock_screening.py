"""Generic native singing faces must use the same singer screening as band Faces."""
import numpy as np
from tools.build_approval_collection import reviewed_vocal_clocks


def make_clocks():
    n=100
    t=np.arange(n,dtype='f8')
    lead=.6+.15*np.sin(t/9)
    backing=lead*(.55+.001*np.cos(t/7))
    shape_a=np.full(n,2,dtype='i1')
    shape_b=shape_a.copy()
    shape_b[29]=3
    return dict(
        estimated_lead_energy=lead,
        estimated_lead_shapes=shape_a,
        estimated_lead_presence_probability=np.full(n,.95),
        estimated_backing_energy=backing,
        estimated_backing_shapes=shape_b,
        estimated_backing_presence_probability=np.full(n,.95))


def test_unverified_generic_face_abstains_from_nearly_copied_harmony():
    raw=make_clocks()
    clocks,report=reviewed_vocal_clocks(raw,{'verification_state':'ESTIMATED'})
    assert clocks['estimated_lead_energy'].any()
    assert not clocks['estimated_backing_energy'].any()
    assert not clocks['estimated_backing_shapes'].any()
    assert raw['estimated_backing_energy'].any()  # read-only source preserved
    assert report['suppression_reason']=='near_mirrored_estimate'


def test_verified_source_tracks_are_preserved_without_guessing_or_rescreening():
    raw=make_clocks()
    clocks,report=reviewed_vocal_clocks(raw,{'verification_state':'VERIFIED'})
    for name in raw:
        np.testing.assert_array_equal(clocks[name],raw[name])
    assert report['state']=='VERIFIED'


def test_unverified_missing_confidence_must_not_reanimate_unscreened_backing():
    import pytest
    raw=make_clocks()
    raw.pop('estimated_backing_presence_probability')
    with pytest.raises(KeyError):
        reviewed_vocal_clocks(raw,{'verification_state':'ESTIMATED'})
