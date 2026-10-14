from copy import deepcopy

import numpy as np
import pytest
from PIL import Image

from tools.drummer_v3_visual_masks import load_spec, strike_transform, exact_geometry
from tools.render_drummer_shoulder_preview import score_schedule, pulse_scores


def test_every_ready_and_strike_arm_uses_torso_roots_with_fixed_wrists():
    spec=load_spec();anchors=spec['shoulder_anchors']
    for hand,point in anchors['revised'].items():
        old=anchors['source'][hand]
        assert point[1]>old[1]+.03
        assert point[0]<old[0]-.02 if hand=='left' else point[0]>old[0]+.03
    count=0
    for zone in spec['zones']:
        strike=zone.get('strike',{});transform=strike.get('arm_transform',zone.get('arm_transform'))
        if not transform: continue
        hand=strike.get('striking_arm','left' if zone['id']=='LEFT_ARM_STICK' else 'right')
        assert transform['grip']==anchors['revised'][hand]
        inverse=np.array(strike_transform(transform,(592,504))).reshape(2,3)
        for source_key,dest_key in [('source_grip','grip'),('source_tip','contact')]:
            dest=np.array(transform[dest_key])*[591,503]
            actual=inverse[:,:2]@dest+inverse[:,2]
            assert np.allclose(actual,np.array(transform[source_key])*[591,503])
        if strike: assert transform['contact']==strike['grip']
        count+=1
    assert count==9


def test_unresolved_polyphonic_hit_is_scored_without_inventing_a_tom():
    report={'analysis':{'audio_sha256':'same'},'event_audit':[
        {'scheduled':True,'type':'snare','timestamp':34.56,'physical_component':'snare'}]}
    raw={'audio_sha256':'same','events':[
        {'timestamp':34.56,'drum_family':'snare','confidence':.8,'source_onset_index':1},
        {'timestamp':34.56,'drum_family':'tom','confidence':.6,'source_onset_index':2},
        {'timestamp':35.03,'drum_family':'tom','confidence':.7,'source_onset_index':3}]}
    scores=score_schedule(report,raw,[{'timestamp':35.04,'novelty':16},
                                     {'timestamp':35.20,'novelty':7}])
    assert len(scores)==4
    assert [e['target'] for e in scores]==['snare',None,None,None]
    assert len(pulse_scores(scores,34.55))==0
    assert len(pulse_scores(scores,34.5667))==2
    assert len(pulse_scores(scores,35.20))==1
    assert not pulse_scores(scores,35.50)
    bad=deepcopy(raw);bad['audio_sha256']='different'
    with pytest.raises(AssertionError): score_schedule(report,bad,[])


def test_arm_reposition_leaves_all_instrument_surfaces_and_foot_unchanged():
    spec=load_spec();legacy=deepcopy(spec)
    legacy.pop('torso_shoulders')
    for zone in legacy['zones']:
        zone.pop('arm_transform',None)
        zone.get('strike',{}).pop('arm_transform',None)
    source=Image.open('fixtures/band_geometry/source/drummerbg.png').convert('RGBA')
    revised,old=exact_geometry(source,spec),exact_geometry(source,legacy)
    for name,mask in revised['surfaces'].items():
        assert np.array_equal(mask,old['surfaces'][name])
    assert np.array_equal(revised['actuators']['HI_HAT_FOOT'],old['actuators']['HI_HAT_FOOT'])
