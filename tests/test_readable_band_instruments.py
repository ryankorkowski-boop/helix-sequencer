import numpy as np
from music.note_events import NoteEvent
from models.band_instrument_logic import chord_route,compile_note_events,event_curves,sparse_harmonic_notes
from models.band_performance_scene import TUNINGS
from models.readable_band_scene import ReadableBandScene


def test_chord_maximizes_distinct_playable_strings_without_overwrites():
    route=chord_route((40,45,47,52),'guitar')
    assert len(route)==3  # Three bass-register strings can cover this chord.
    assert len({s for s,f,n in route})==3
    for s,f,n in route:assert TUNINGS['guitar'][s]+f==n and 0<=f<=24
    assert len(chord_route((40,45,50,55,59,64),'guitar'))==6


def test_register_folding_is_explicit_and_keeps_pitch_class():
    for kind in ('bass','guitar'):
        for pitch in range(24,85):
            route=chord_route((pitch,),kind);assert len(route)==1
            s,f,n=route[0];assert (n-pitch)%12==0
            assert TUNINGS[kind][s]+f==n


def test_repeated_notes_hold_velocity_rest_and_retrigger_at_source_onset():
    notes=np.array([[60,64]]*6+[[-1,-1]]*8)
    vel=np.tile([.8,.25],(14,1));attack=np.zeros(14);attack[3]=.8
    events=compile_note_events(notes,vel,attack,'test')
    assert len(events)==4
    n,v,a,p=event_curves(events,14,6,.10)
    assert a[0]==.8 and a[3]==.8 and p[0]==0 and p[3]==0
    assert v[1,0]==.8 and v[1,1]==.25
    assert not a[1:3].any() and not v[9:].any() and np.all(n[9:]==-1)


def test_harmonics_do_not_become_false_chord_and_silence_stays_idle():
    spectrum=np.zeros((72,3));x=np.arange(72)
    for j,pitches in enumerate(([40],[48,52,55],[])):
        for pitch in pitches:
            for h in range(1,9):
                spectrum[:,j]+=np.exp(-.5*((x-(pitch-24+12*np.log2(h)))/.42)**2)/h**1.3
    notes,_=sparse_harmonic_notes(spectrum)
    assert list(notes[0])==[40,-1,-1,-1]
    assert set(notes[1])=={48,52,55,-1}
    assert np.all(notes[2]==-1)


def test_strings_are_independent_and_fixed_at_endpoints():
    scene=ReadableBandScene('prismatic_orrery')
    baseline=[scene.instances[i]['matrix'].copy() for i in scene.strings['bass'][1]['ids']]
    scene.vibrate('bass',0,.9,.12)
    assert all(np.array_equal(m,scene.instances[i]['matrix']) for m,i in zip(baseline,scene.strings['bass'][1]['ids']))
    s=scene.strings['bass'][0]
    # Cylinder axis is local Z; endpoints are center +/- half scaled axis.
    first=scene.instances[s['ids'][0]]['matrix'];last=scene.instances[s['ids'][-1]]['matrix']
    assert np.allclose(first[:3,3]-first[:3,2]*.5,s['a'])
    assert np.allclose(last[:3,3]+last[:3,2]*.5,s['b'])
    assert np.linalg.norm(scene.strings['bass'][0]['a']-scene.strings['bass'][1]['a'])>=.05
    # Even at maximum backward shimmer, strings clear the thickened neck.
    assert all(s['a'][2]-.040-s['radius']>.43+.095 for s in scene.strings['guitar'])


def test_detuned_single_note_is_not_two_neighboring_chord_notes():
    x=np.arange(72);spectrum=np.zeros((72,1))
    for h in range(1,9):
        spectrum[:,0]+=np.exp(-.5*((x-(40.4-24+12*np.log2(h)))/.60)**2)/h**1.3
    notes,_=sparse_harmonic_notes(spectrum)
    assert list(notes[0])==[40,-1,-1,-1]
