import numpy as np
import pytest
from models.musical_band_response import ringing_candidates,cast_source_voice,choose_solo_windows
from animation.articulated_source_drummer import ArticulatedDrummer
from tools.render_drummer_v3_preview import TARGETS
from models.refined_band_scene import RefinedBandScene
from models.band_motion_refinement import EventLane,transition_targets


def test_indexed_events_keep_exact_frame_boundaries_ties_and_random_access():
    events=[dict(time=t,label=i) for i,t in enumerate((.1,.2,.2,.5,1.1))]
    lane=EventLane(events)
    for time in (0,.2,1.4,.199,.5,.1,.201,1.1):
        before=next((e for e in reversed(events) if e['time']<=time),None)
        after=next((e for e in events if e['time']>time),None)
        assert lane.neighbors(time)==(before,after)
    assert EventLane([]).neighbors(1)==(None,None)


def test_keyboard_anticipation_cannot_overwrite_adjacent_note_contacts():
    targets=np.array([[0,0,0],[0,0,0],[1,2,3],[4,5,6],[7,8,9],[7,8,9]],float)
    actual=transition_targets(targets,seconds=.10,preserve_changes=True)
    np.testing.assert_array_equal(actual[[2,3,4]],targets[[2,3,4]])
    assert not np.array_equal(transition_targets(targets)[2],targets[2])


def test_mallets_accept_soft_marimba_high_bells_but_not_voice_or_noise():
    cues=[dict(start_ms=100,midi=55,concentration=.14,decay_ratio=1.08,vocal_similarity=.2),
          dict(start_ms=200,midi=94,concentration=.3,decay_ratio=2,vocal_similarity=.1),
          dict(start_ms=300,midi=72,concentration=.2,decay_ratio=2,vocal_similarity=.9),
          dict(start_ms=400,midi=72,concentration=.02,decay_ratio=2,vocal_similarity=.1)]
    accepted,rejected=ringing_candidates(cues)
    assert [x['midi'] for x in accepted]==[55,94]
    assert [x['reason'] for x in rejected]==['vocal leakage','broadband attack']


def test_solo_voice_never_changes_avatar_on_repeated_lyrics_or_refrain():
    mouth=np.array([2,3,4,0,2,3,4,0],np.int8);energy=np.ones(8)
    lanes=cast_source_voice(mouth,energy,'female')
    assert not lanes[:,0].any() and np.array_equal(lanes[:,1],mouth)
    both=cast_source_voice(mouth,energy,'male',[dict(start=.2,end=.3,role='both')])
    assert np.array_equal(both[4:6,0],both[4:6,1])
    assert not both[:4,1].any() and not both[6:,1].any()


def test_voice_preserves_consonants_but_closes_during_measured_silence():
    mouths=np.full(8,2,np.int8);mouths[2]=1
    energy=np.array([1,1,.01,1,0,0,0,0])
    lanes=cast_source_voice(mouths,energy)
    assert lanes[2,0]==1 and not lanes[4:].any()


def test_window_ranking_prefers_actual_guitar_and_less_vocals():
    g=np.zeros(200);g[40:80]=.9;g[120:160]=.9
    v=np.zeros(200);v[120:160]=1
    chosen=choose_solo_windows(g,v,seconds=2,count=2)
    assert chosen[0]['start']==2 and chosen[1]['start']==6


def test_expanded_bars_have_unique_noncolliding_channels_and_literal_register():
    scene=RefinedBandScene('woven_aurora',(48,96))
    assert len(scene.bars)==49
    assert {scene.mallet_slot(p) for p in scene.bars}==set(range(128,177))
    assert scene.bars[48][0]<scene.bars[96][0]
    assert len(scene.technical_proof['band_members'])==7


@pytest.mark.parametrize('target,side',[(TARGETS[1],'left'),(TARGETS[1],'right'),(TARGETS[2],'right'),
    (TARGETS[3],'right'),(TARGETS[4],'left'),(TARGETS[5],'left'),(TARGETS[6],'left'),(TARGETS[7],'right')])
def test_natural_arms_keep_exact_contact_and_two_fixed_limbs(target,side):
    p=ArticulatedDrummer([dict(time=1,target=target,side=side,velocity=.7)],natural_arms=True)
    for t in (.88,.96,1,1.06,1.2,1.4):
        p.frame(t,[target] if t==1 else [])
        for hand,j in p.last_joints.items():
            assert np.linalg.norm(j['shoulder']-j['elbow'])==pytest.approx(p.lengths[hand][0])
            assert np.linalg.norm(j['elbow']-j['wrist'])==pytest.approx(p.lengths[hand][1])
            assert np.linalg.norm(j['tip']-j['wrist'])==pytest.approx(55)
        if t==1:assert np.allclose(p.last_joints[side]['tip'],p.targets[target,side][0])
    assert np.allclose(p.last_joints[side]['wrist'],p.rest[side])


def test_explicit_voice_cues_reject_unknown_roles():
    with pytest.raises(ValueError):cast_source_voice(np.ones(10),np.ones(10),'automatic')
    with pytest.raises(ValueError):cast_source_voice(np.ones(10),np.ones(10),'male',[dict(start=0,end=.2,role='guess')])
