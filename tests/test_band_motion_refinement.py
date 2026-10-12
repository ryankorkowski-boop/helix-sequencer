"""Counterexamples for connected motion, silence, pitch ownership and contact."""
import numpy as np
import pytest
from music.note_events import NoteEvent
from models.band_motion_refinement import elbow_2d,signed_gestures,transition_targets,mallet_events
from animation.articulated_source_drummer import ArticulatedDrummer,BandLighting
from tools.render_drummer_v3_preview import TARGETS
from models.refined_band_scene import RefinedBandScene


def test_ik_preserves_both_lengths_and_rejects_impossible_reach():
    shoulder=np.array([5.,8.]);wrist=np.array([30.,15.])
    elbow=elbow_2d(shoulder,wrist,22,19,-1)
    assert np.linalg.norm(elbow-shoulder)==pytest.approx(22)
    assert np.linalg.norm(wrist-elbow)==pytest.approx(19)
    with pytest.raises(ValueError):elbow_2d(shoulder,[100,100],22,19)


def test_alternating_gestures_have_no_beat_or_sustain_fallback():
    a=np.zeros(20);a[2]=.8;a[10]=.3
    g=signed_gestures(a)
    assert not g[:2].any() and not g[6:10].any() and not g[14:].any()
    assert g[2]>0 and g[10]<0 and abs(g[10])==pytest.approx(.3)
    assert not signed_gestures(np.zeros(30)).any()


def test_fretting_transition_keeps_holds_and_reaches_supported_note():
    targets=np.array([[2.]]*6+[[3.]]*6)
    smooth=transition_targets(targets)
    assert np.array_equal(smooth[:4],targets[:4])
    assert 2<smooth[4,0]<smooth[5,0]<3
    assert np.array_equal(smooth[6:],targets[6:])


def test_mallets_exclude_piano_and_abstain_outside_real_bars():
    data=[NoteEvent(0,.2,60,source='piano_stem_harmonic_estimate'),
          NoteEvent(0,.2,72,source='other_stem_screened_mallet_estimate'),
          NoteEvent(1,1.2,91,source='other_stem_screened_mallet_estimate')]
    accepted,omitted=mallet_events(data)
    assert [e.pitch for e in accepted]==[72] and [e.pitch for e in omitted]==[91]


@pytest.mark.parametrize('target,side',[(TARGETS[1],'left'),(TARGETS[1],'right'),(TARGETS[2],'right'),
    (TARGETS[3],'right'),(TARGETS[4],'left'),(TARGETS[5],'left'),(TARGETS[6],'left'),(TARGETS[7],'right')])
def test_every_drum_contact_has_two_connected_fixed_links_and_fixed_stick(target,side):
    player=ArticulatedDrummer([dict(time=1,target=target,side=side,velocity=.7)])
    for time in (.93,.97,1,1.05,1.14,1.25):
        player.frame(time,[target] if time==1 else [])
        for hand,j in player.last_joints.items():
            upper,lower=player.lengths[hand]
            assert np.linalg.norm(j['shoulder']-j['elbow'])==pytest.approx(upper)
            assert np.linalg.norm(j['elbow']-j['wrist'])==pytest.approx(lower)
            assert np.linalg.norm(j['tip']-j['wrist'])==pytest.approx(55)
        if time==1:assert np.allclose(player.last_joints[side]['tip'],player.targets[target,side][0])
    assert np.allclose(player.last_joints[side]['wrist'],player.rest[side])


def test_ring_does_not_raise_sticks_and_two_hits_do_not_create_extra_arms():
    p=ArticulatedDrummer([dict(time=1,target=TARGETS[6],side='left'),dict(time=1,target=TARGETS[1],side='left')])
    p.frame(1,[TARGETS[6],TARGETS[1]])
    assert len(p.last_joints)==2
    p.frame(2,[],{TARGETS[6]:.6})
    assert all(np.allclose(j['wrist'],p.rest[side]) for side,j in p.last_joints.items())


def test_brightness_is_adjustable_and_idle_remains_localized():
    p=ArticulatedDrummer([],BandLighting(idle_body=.8,idle_instrument=.3,strike=1.4))
    idle=np.asarray(p.frame(0).convert('RGB'))
    assert idle[180:245,265:340].max()>80
    assert idle[300:350,270:310].mean()<idle[180:225,270:310].mean()
    with pytest.raises(ValueError):BandLighting(idle_body=-.1)


def test_distinct_literal_bars_and_non_neon_strings():
    scene=RefinedBandScene('prismatic_orrery')
    assert set(scene.bars)==set(range(60,85))
    assert all(scene.bars[p+1][0]>scene.bars[p][0] for p in range(60,84))
    bars=[o for o in scene.instances if o['name'].startswith('xylophone_bar_') and 128<=o['slot']<153]
    assert len({o['slot'] for o in bars})==25
    strings=[o for o in scene.instances if '_live_string_' in o['name']]
    assert all(max(o['color'])-min(o['color'])<.2 for o in strings)

@pytest.fixture
def refined_performance(tmp_path,monkeypatch):
    import json
    import tools.readable_band_performance as module
    from tools.refined_band_performance import RefinedPerformance
    from models.band_instrument_logic import chord_route,event_curves
    n=20;arrays={};events={}
    for kind,cols,pitches in [('bass',1,[40]),('guitar',6,[52,59]),('piano',6,[60,64])]:
        ev=[NoteEvent(0,.8,p,.8,source='piano_stem_harmonic_estimate' if kind=='piano' and p==60 else 'other_stem_screened_mallet_estimate' if kind=='piano' else kind+'_stem_harmonic_estimate') for p in pitches]
        notes,levels,attacks,phase=event_curves(ev,n,cols,.1)
        events[kind]=[e.to_dict() for e in ev]
        arrays.update({kind+'_notes':notes,kind+'_note_levels':levels,kind+'_attack':attacks,kind+'_phase':phase,kind+'_energy':levels.max(axis=1)})
        if kind!='piano':
            routes=np.full((n,cols,3),-1,np.int16)
            for i,grid in enumerate(notes):
                route=chord_route(tuple(int(p) for p in grid if p>=0),kind)
                if route:routes[i,:len(route)]=route
            arrays[kind+'_routes']=routes
    arrays.update(mouth_lanes=np.zeros((n,2),np.int16),vocal_energy=np.zeros(n),vocal_route=np.zeros(n,np.int16),bass_height=np.ones(n)*2.5,keyboard_mallet_energy=np.ones(n)*.6)
    folder=tmp_path/'analysis/test';folder.mkdir(parents=True);np.savez(folder/'performance_curves.npz',**arrays)
    (folder/'note_events.json').write_text(json.dumps(events));(folder/'vocals.json').write_text(json.dumps({'lines':[]}))
    proof_folder=tmp_path/'outputs/Intricate_Band_Samplers/analysis/test';proof_folder.mkdir(parents=True)
    (proof_folder/'verification.json').write_text(json.dumps(dict(source_sha256='song',mallet_attacks=[
        dict(start_ms=200,midi=72,concentration=.6,decay_ratio=3,vocal_similarity=.1),
        dict(start_ms=500,midi=64,concentration=.12,decay_ratio=1.1,vocal_similarity=.9),
        dict(start_ms=700,midi=91,concentration=.6,decay_ratio=3,vocal_similarity=.1)])))
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'native_drummer',lambda row:(np.zeros((n,8)),np.zeros((n,8)),np.zeros(n),{}))
    return RefinedPerformance({'id':'test','sha256':'song'},RefinedBandScene('prismatic_orrery'),tmp_path/'analysis')


def test_mallet_gate_uses_own_pitch_excludes_piano_and_rejects_weak_candidate(refined_performance):
    p=refined_performance
    assert p.mallet_proof['accepted']==1 and p.mallet_proof['out_of_range_omissions']==1
    assert p.mallet_proof['rejected_weak_or_vocal_candidates']==1
    assert {n for n in p.curves['piano_notes'].ravel() if n>=0}=={60}
    assert [e['pitch'] for e in p.mallet_schedule]==[72]


def test_exact_mallet_contact_connected_forearm_and_fixed_shaft(refined_performance):
    p=refined_performance;p.pose(4)
    contact=p.contact_audit[-1];side=contact['side'];hand,tip=p.mallet_targets[side]
    assert np.allclose(tip,p.scene.bars[72]+(0,.0275+.057,0))
    assert np.linalg.norm(tip-hand)==pytest.approx(.3,abs=1e-8)
    rig=next(r for r in p.scene.rigs if r['role']=='xylophone' and r['side']==side)
    a,b,c=(p.scene.instances[j]['matrix'] for j in rig['ids'])
    assert np.allclose(a[:3,3]+a[:3,2]/2,b[:3,3]-b[:3,2]/2)
    assert np.allclose(b[:3,3]+b[:3,2]/2,c[:3,3])
    before=[o['matrix'].copy() for o in p.scene.instances];p.pose(4)
    assert all(np.allclose(m,o['matrix']) for m,o in zip(before,p.scene.instances))


def test_kick_activity_does_not_invent_bass_or_guitar_gestures(refined_performance):
    p=refined_performance;p.pose(3)
    hands={k:v.copy() for k,v in p.hand_targets.items()}
    p.drums[:]=1;p.strikes[:]=1;p.pose(3)
    assert all(np.allclose(v,p.hand_targets[k]) for k,v in hands.items())
