import json
import numpy as np
import pytest
from music.note_events import NoteEvent
from models.band_instrument_logic import event_curves,attack_gestures,chord_route
from models.readable_band_scene import ReadableBandScene
from tools.readable_band_performance import ReadablePerformance


def test_quiet_new_bass_note_outranks_loud_old_release():
    notes,levels,attacks,phase=event_curves([NoteEvent(0,.2,40,.9),NoteEvent(.2,.3,52,.2)],12,1,.22)
    assert notes[4,0]==52 and levels[4,0]==pytest.approx(.2)
    assert attacks[4]==pytest.approx(.2) and phase[4]==0


def test_same_pitch_quiet_retrigger_does_not_inherit_old_velocity():
    notes,levels,attacks,phase=event_curves([NoteEvent(0,.2,60,.9),NoteEvent(.2,.3,60,.2)],12,1,.22)
    assert levels[4:6,0]==pytest.approx([.2,.2])
    assert attacks[4]==pytest.approx(.2)
    assert np.all(notes[11:]==-1) and not levels[11:].any()


def test_released_note_at_exact_end_does_not_mask_new_hold():
    notes,levels,attacks,phase=event_curves([NoteEvent(0,.2,40,.9),NoteEvent(.2,.3,52,.2)],12,1,0)
    assert notes[4,0]==52 and np.all(notes[6:]==-1)


def test_unselected_notes_cannot_move_hand_and_quiet_attack_resets_gain():
    _,_,attacks,_=event_curves([NoteEvent(0,.6,60,.9),NoteEvent(.2,.3,64,.1)],12,1,.2)
    assert attacks[4]==0
    attacks=np.zeros(12);attacks[0]=.9;attacks[2]=.1
    gestures=attack_gestures(attacks)
    assert gestures[0]==pytest.approx(.9) and gestures[2]==pytest.approx(.1)
    assert gestures[3]<.1 and not gestures[6:].any()


@pytest.fixture
def performance(tmp_path,monkeypatch):
    import tools.readable_band_performance as module
    n=12;arrays={}
    for kind,cols,pitches in [('bass',1,[40]),('guitar',6,[52,59,64]),('piano',6,[60,72])]:
        notes=np.full((n,cols),-1,np.int16);notes[:8,:len(pitches)]=pitches
        levels=np.where(notes>=0,.8,0).astype(np.float32)
        attack=np.zeros(n);attack[0]=.8
        arrays.update({kind+'_notes':notes,kind+'_note_levels':levels,kind+'_energy':levels.max(axis=1),
                       kind+'_attack':attack,kind+'_phase':np.minimum(np.arange(n)/4,1)})
        if kind!='piano':
            routes=np.full((n,cols,3),-1,np.int16)
            chosen=chord_route(tuple(pitches),kind);routes[:8,:len(chosen)]=chosen
            arrays[kind+'_routes']=routes
    arrays.update(mouth_lanes=np.full((n,2),2),vocal_energy=np.ones(n)*.6,vocal_route=np.zeros(n),bass_height=np.ones(n)*2.8)
    folder=tmp_path/'test';folder.mkdir()
    np.savez(folder/'performance_curves.npz',**arrays)
    (folder/'vocals.json').write_text(json.dumps({'lines':[]}))
    monkeypatch.setattr(module,'native_drummer',lambda row:(np.zeros((n,8)),np.zeros((n,8)),np.zeros(n),{}))
    return ReadablePerformance({'id':'test'},ReadableBandScene('prismatic_orrery'),tmp_path)


def test_all_face_details_share_head_transform_without_accumulation(performance):
    p=performance;p.pose(2)
    for role in ('bass','guitar','piano'):
        entries=[(p.scene.instances[idx],rest) for idx,r,rest in p.scene.groove if r==role]
        head,rest=next((o,m) for o,m in entries if o['name']==role+'_head')
        delta=head['matrix'][:3,3]-rest[:3,3]
        assert np.linalg.norm(delta)>0
        for o,m in entries:assert np.allclose(o['matrix'][:3,3]-m[:3,3],delta,atol=1e-6)
        rig=next(r for r in p.scene.rigs if r['role']==role)
        arm=p.scene.instances[rig['ids'][0]]['matrix']
        assert np.allclose(arm[:3,3]-arm[:3,2]*.5,rig['shoulder']+delta,atol=1e-6)
    before=[o['matrix'].copy() for o in p.scene.instances];p.pose(2)
    assert all(np.allclose(m,o['matrix']) for m,o in zip(before,p.scene.instances))
    assert next(o for o in p.scene.instances if o['name']=='piano_holly')['matrix'][0,3]>6


def test_guitar_finger_uses_supported_pitch_and_true_fret_spacing(performance):
    p=performance;p.pose(0);string,fret,pitch=p.guitar_contact_route
    assert (string,fret,pitch) in p.active_routes['guitar']
    s=p.scene.strings['guitar'][string]
    hand=p.hand_targets['guitar','finger']-(0,0,.065)
    # Twelfth fret bisects a vibrating string; this tests physical spacing.
    assert np.allclose(p.scene.guitar_contact(string,12),(s['a']+s['b'])/2)
    assert np.linalg.norm(hand-s['a'])/np.linalg.norm(s['b']-s['a'])==pytest.approx(2**(-fret/12))
    frets=[o for o in p.scene.instances if o['name']=='guitar_fret']
    assert len(frets)==24


def test_held_keyboard_hands_contact_depressed_key_tops_and_bass_holds_rest(performance):
    p=performance;p.pose(5)
    for side,pitch in [('left',60),('right',72)]:
        key=next(o for o in p.scene.instances if o['name']==f'piano_key_{pitch}')
        top=key['matrix'][1,3]+.035
        hand=p.hand_targets['piano',side]
        assert hand[1]-.075==pytest.approx(top,abs=1e-6)
    p.pose(10)
    assert p.hand_targets['bass','finger'][1]==pytest.approx(2.8)
    assert not p.key_levels and not p.active_routes['guitar']


def test_empty_legacy_member_states_fail_explicitly_without_invented_motion():
    from tools.export_band_performance_manifest import DEMO_INTENTS
    from core.intent_layer_expander import IntentLayerExpander
    from core.band_intent_adapter import BandIntentAdapter
    from core.band_performance_timeline import BandPerformanceTimelineCompiler
    events=BandIntentAdapter().adapt_many(IntentLayerExpander().expand_many(DEMO_INTENTS))
    event=next(e for e in events if e.performer=='guitarist')
    with pytest.raises(ValueError,match='guitarist has no approved runtime states'):
        BandPerformanceTimelineCompiler().compile_event(event)


def test_quiet_accepted_drum_strike_is_visible_but_decay_does_not_move_arms():
    from tools.render_intricate_band_samplers import ExactDryDrummer
    dry=ExactDryDrummer.__new__(ExactDryDrummer)
    dry.idle=np.full((2,2,3),10.,np.float32)
    dry.poses={(k,hand):dry.idle+100 for k in range(8) for hand in ('left','right')}
    dry.ringing={k:dry.idle+10 for k in (6,7)}
    zero=np.zeros(8);strike=zero.copy();strike[2]=.153
    assert np.max(dry.frame(zero,strike,0)[:,:,:3])==110
    decay=zero.copy();decay[6]=.5
    assert np.max(dry.frame(decay,zero,0)[:,:,:3])==15
