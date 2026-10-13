import numpy as np
from models.refined_band_scene import RefinedBandScene
from models.distinct_band_stages import DistinctBandScene,TwinBandGarden,STAGES
from models.musical_band_response import cast_source_voice
from models.intricate_band_scene import LAYOUTS


def test_neutral_faces_remove_gender_accessories_without_changing_other_musicians():
    original=RefinedBandScene('prismatic_orrery')
    neutral=RefinedBandScene('prismatic_orrery',neutral_performers=True)
    for role in ('lead','harmony','xylophone'):
        objects=[o for o in neutral.instances if o.get('performer_role')==role]
        assert not any('bow' in o['name'] or 'eyelash' in o['name'] for o in objects)
        cap=next(o for o in objects if o['name']==role+'_hat_crown')
        assert cap['kind']=='sphere'
    for role in ('bass','guitar','piano'):
        a=[o for o in original.instances if o.get('performer_role')==role]
        b=[o for o in neutral.instances if o.get('performer_role')==role]
        assert len(a)==len(b)
        assert all(np.array_equal(x['matrix'],y['matrix']) for x,y in zip(a,b))


def test_six_stages_have_different_features_and_floors_with_stable_rig_indices():
    signatures=[]
    for name in STAGES:
        s=DistinctBandScene(name)
        signatures.append(tuple(s.feature_names))
        assert not any(o['kind']!='hidden' and o['name'] in ('expanded_stage','stage','constellation_pixel') for o in s.instances)
        assert all(s.instances[i]['kind']!='hidden' for r in s.rigs for i in r['ids'])
        assert all(s.instances[i]['name'].startswith('piano_key_') for i in s.key_rest)
    assert len(set(signatures))==6


def test_twin_stage_sync_keeps_local_contacts_and_isolates_slot_banks():
    a=DistinctBandScene('ember_amphitheatre');b=DistinctBandScene('glacier_pier',True)
    g=TwinBandGarden(a,b)
    item,src,world=g.sources[0]
    old=src['matrix'].copy();src['matrix'][1,3]+=.3;g.sync()
    assert np.allclose(item['matrix'],world@src['matrix'])
    assert np.isclose(src['matrix'][0,3],old[0,3])
    first,second=[],[]
    for dst,src,world in g.sources:
        if src['slot']<0:continue
        (first if world[0,3]<0 else second).append(dst['slot'])
    assert max(first)<192 and min(second)>=192 and max(second)<384
    assert not set(first)&set(second)
    assert np.isclose(g.second_drummer_corners[0,0]-g.dry_drummer_corners[0,0],20)


def test_super_garden_includes_all_six_stage_sources_and_native_model_gallery():
    g=TwinBandGarden(DistinctBandScene('ember_amphitheatre'),DistinctBandScene('circuit_garage',True),True)
    assert set(g.inherited_layouts)==set(LAYOUTS)
    assert {'WHALE','MANTA','DNA','MATRIX','STAR','CUBES'}<=set(g.technical_models)
    assert 'Tree 360' in g.technical_models and 'Sphere' in g.technical_models
    assert all(np.isfinite(o['matrix']).all() for o in g.instances)
    assert all(np.isfinite(o['mesh'].vertices).all() for o in g.custom)


def test_neutral_lane_names_do_not_require_voice_gender_assignment():
    mouths=np.array([2,3,4,0]);energy=np.ones(4)
    a=cast_source_voice(mouths,energy,'first');b=cast_source_voice(mouths,energy,'second')
    assert np.array_equal(a[:,0],mouths) and not a[:,1].any()
    assert np.array_equal(b[:,1],mouths) and not b[:,0].any()
