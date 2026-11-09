from types import SimpleNamespace
import numpy as np
import pytest
from music.review_score import vocal_clock,pitched_roles,spatial_score
from music.note_events import NoteEvent
from models.review_snowman_scene import ReviewSnowmanScene,MOUTHS


def test_vocal_clock_closes_in_silence_without_a_release_tail():
    t=np.arange(32000)/16000;y=np.zeros_like(t);mask=(t>=.5)&(t<1.0)
    y[mask]=.20*np.sin(2*np.pi*200*t[mask])
    track=vocal_clock(y)
    assert np.count_nonzero(track['energy'][:48])==0
    assert np.count_nonzero(track['energy'][103:])==0
    assert np.count_nonzero(track['energy'][53:98])==45
    assert track['shapes'][70] in (2,3,4)
    assert not vocal_clock(y,False)['energy'].any()
    with pytest.raises(ValueError):vocal_clock(np.array([float('nan')]))


def test_pitched_roles_do_not_send_the_same_ringing_attack_to_both_players():
    sustained=NoteEvent(.2,.8,60,.8,source='other_stem_screened_harmonic_estimate',confidence=.8)
    ringing=NoteEvent(1.,1.2,72,.9,source='other_stem_screened_harmonic_estimate',confidence=.8)
    gate=np.zeros(40);gate[20]=.8
    candidate=dict(start_ms=1000,midi=72,concentration=.6,decay_ratio=2.,vocal_similarity=.1)
    keys,mallets,corrections=pitched_roles([], [sustained,ringing],[candidate],gate,[.18,1.])
    assert [(e.pitch,e.start) for e in keys]==[(60,.18)]
    assert [(e.pitch,e.start) for e in mallets]==[(72,1.)]
    assert abs(corrections[0][1]-corrections[0][0])<.075
    assert pitched_roles([],[],[dict(candidate,vocal_similarity=.95)],gate,[])[1]==[]


def test_review_cast_is_seven_snowmen_with_two_distinct_pitched_rigs():
    s=ReviewSnowmanScene()
    assert len(s.visible_roles)==7 and {'piano','xylophone'}<=set(s.visible_roles)
    for role in ('bass','guitar','piano','xylophone','lead','harmony'):
        assert next(o for o in s.instances if o['name']==role+'_torso')['kind']=='sphere'
        assert next(o for o in s.instances if o['name']==role+'_head')['kind']=='sphere'
    assert any(o['name'].startswith('piano_key_') and o['kind']=='box' for o in s.instances)
    assert not any('_rock_' in o['name'] for o in s.instances)
    for shape in MOUTHS:
        s.update_singer_mouth('lead',shape,.8)
        mouth=next(o for o in s.instances if o.get('mouth_role')=='lead')
        assert 0<mouth['matrix'][1,1]<=.071
        np.testing.assert_allclose(mouth['matrix'][:3,3],s.centers['lead'])


def test_spatial_score_keeps_silent_roles_dark_and_obeys_shared_budget():
    n=120;zero=np.zeros(n);bass=np.ones(n)*.8
    p=SimpleNamespace(n=n,curves={'bass_energy':bass,'guitar_energy':zero,'piano_energy':zero,
        'bass_attack':np.r_[.8,np.zeros(n-1)],'guitar_attack':zero,'piano_attack':zero},
        voice_energy=np.zeros((n,2)),strikes=np.zeros((n,8)))
    positions=np.c_[np.arange(24),np.zeros((24,2))];roles=np.arange(24)%6
    actual,proof=spatial_score(p,positions,roles)
    assert actual.any() and not actual[roles!=0].any()
    assert (np.count_nonzero(actual,axis=0)<=12).all()
    np.testing.assert_array_equal(actual,spatial_score(p,positions,roles)[0])
    assert not proof['overall_volume_broadcast']


def test_melodic_props_use_actual_keys_when_the_recording_has_no_guitar():
    n=100;zero=np.zeros(n);keys=np.ones(n)*.8
    p=SimpleNamespace(n=n,curves={'bass_energy':zero,'guitar_energy':zero,'piano_energy':keys,
        'bass_attack':zero,'guitar_attack':zero,'piano_attack':np.r_[.8,np.zeros(n-1)]},
        voice_energy=np.zeros((n,2)),strikes=np.zeros((n,8)))
    roles=np.arange(30)%6;positions=np.c_[np.arange(30),np.zeros((30,2))]
    out,proof=spatial_score(p,positions,roles)
    assert proof['melodic_prop_source']=='piano' and out[roles==1].any()
    assert not out[np.isin(roles,[0,3,4,5])].any()
