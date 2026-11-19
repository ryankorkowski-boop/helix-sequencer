import numpy as np
from models.native_review_band import add_band,allocate,ac_variant
from models.ultimate_showcase import Garden
from tools.build_spatial_review import band_curves


def test_native_pixel_instruments_have_independent_key_and_string_nodes():
    g=Garden()
    models=add_band(g)
    assert len(models)==7
    for role,prefix in [('bass','STRING_'),('guitar','STRING_'),('piano','NOTE_MIDI_'),('xylophone','NOTE_MIDI_')]:
        m=next(x for x in models if x.details['review_role']==role)
        parts={k:set(v) for k,v in m.submodels.items() if k.startswith(prefix)}
        assert parts and all(parts.values()),role
        assert len(set.union(*parts.values()))==sum(len(x) for x in parts.values()),role
        assert all(1<=i<=m.channels for ids in parts.values() for i in ids),role
        assert m.kind!='ac'
        if role in ('piano','xylophone'):
            pitches=[int(k.rsplit('_',1)[1]) for k in parts]
            assert len(pitches)>16, 'Native pixel output must not collapse to 16 physical circuits'
            ac=ac_variant(m)
            assert ac.details['circuit_count']<=16
            assert 'shared across octaves' in ac.details['pitch_mapping']


def test_allocated_pixel_models_do_not_overlap():
    g=Garden();models=add_band(g);allocate(g)
    for previous,current in zip(models,models[1:]):
        assert current.start>=previous.start+previous.channels
