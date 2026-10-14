import numpy as np
from audio.rapid_kick_recovery import recover_kicks


def fixture():
    sr=16000; y=np.zeros(sr*3); times=[.2,.4,.6,.8,1,1.2,1.4,1.6]+[1.8+i*.10 for i in range(8)]
    t=np.arange(round(sr*.085))/sr
    kick=np.sin(2*np.pi*65*t)*np.exp(-t*35)*(1-np.exp(-t*300))
    for time in times:
        a=round(time*sr);y[a:a+len(kick)]+=kick
    refs=[dict(timestamp=time,drum_family='kick',confidence=.8,velocity=.8) for time in times[:7]]
    return sr,y,times,refs


def test_source_calibration_recovers_real_transients_without_count_or_beat_filler():
    sr,y,times,refs=fixture();actual,report=recover_kicks(y,sr,refs,start=.15,end=2.6)
    assert len(actual)==len(times)
    assert all(abs(e['timestamp']-t)<.025 for e,t in zip(actual,times))
    assert len(report['added'])==9
    assert all(a is b for a,b in zip(actual[:7],refs))
    assert all(abs(e['timestamp']-t)<.025 for e,t in zip(actual[-8:],times[-8:]))


def test_recovery_abstains_without_references_and_does_not_turn_silence_into_hits():
    sr,y,times,refs=fixture()
    actual,report=recover_kicks(y,sr,refs[:2],start=.15,end=2.6)
    assert actual==refs[:2] and report['abstention']
    y[sr:]=0
    actual,report=recover_kicks(y,sr,refs[:4],start=.15,end=2.6)
    assert actual==refs[:4] and not report['added']


def test_tiny_review_window_abstains_instead_of_crashing():
    sr, y, _, refs = fixture()
    actual, report = recover_kicks(y, sr, refs[:3], start=.2, end=.2001)
    assert actual == refs[:3]
    assert report['abstention'] == 'fewer than three accepted recording-specific kick references'


def test_silent_accepted_references_do_not_generate_false_kicks():
    sr = 16000
    y = np.zeros(sr)
    refs = [dict(timestamp=t, drum_family='kick', confidence=.8)
            for t in (.2, .4, .6)]
    actual, report = recover_kicks(y, sr, refs, start=.1, end=.9)
    assert actual == refs
    assert report['abstention'] == 'accepted references contain no measurable low-band energy'
