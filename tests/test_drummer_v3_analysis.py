import numpy as np
from core.drummer_v3_analysis import DrumType, analyze_drummer_features

def _pulse(n=400, idx=(50,150,250)):
    x=np.zeros(n)
    for i in idx:x[i]=1.0
    return x

def test_typed_events_require_isolated_drum_evidence():
    low=_pulse(); mid=_pulse(idx=(75,175,275)); high=_pulse(idx=(25,125,225))
    events=analyze_drummer_features(low=low,mid=mid,high=high,drum_low=low,drum_mid=mid,drum_high=high,frame_rate=100)
    kinds={e.kind for e in events}
    assert DrumType.KICK in kinds and DrumType.SNARE in kinds and DrumType.HI_HAT in kinds

def test_guitar_like_full_mix_transients_do_not_create_drums():
    n=600; guitar=np.zeros(n); guitar[[100,180,260,340,420]]=1.0; silent=np.zeros(n)
    events=analyze_drummer_features(low=guitar,mid=guitar,high=guitar,rms=guitar,drum_low=silent,drum_mid=silent,drum_high=silent,frame_rate=100)
    assert events == []

def test_harmonic_guitar_transients_are_rejected_even_after_hpss():
    n=500; guitar=_pulse(n,(80,160,240,320)); low=guitar.copy(); mid=guitar.copy(); high=guitar.copy(); rms=guitar.copy()
    # A harmonic-dominant source can still leak into HPSS. Give it enough apparent
    # percussive energy to reach the old gate, but very low spectral flatness.
    p_low=guitar.copy(); p_mid=guitar.copy(); p_high=guitar.copy(); quality=np.full(n,0.42); flatness=np.full(n,0.008)
    events=analyze_drummer_features(low=low,mid=mid,high=high,rms=rms,drum_low=p_low,drum_mid=p_mid,drum_high=p_high,drum_percussive_ratio=quality,percussive_flatness=flatness,frame_rate=100)
    assert events == []

def test_drum_stem_adds_three_tom_targets():
    n=500; low=np.zeros(n); mid=np.zeros(n); high=np.zeros(n); drum_low=np.zeros(n); drum_mid=np.zeros(n); drum_high=np.zeros(n)
    drum_mid[100]=1.0; drum_low[100]=1.0; drum_mid[200]=1.0; drum_low[200]=0.5; drum_mid[300]=1.0; drum_low[300]=0.1
    events=analyze_drummer_features(low=low,mid=mid,high=high,drum_low=drum_low,drum_mid=drum_mid,drum_high=drum_high,frame_rate=100)
    kinds={e.kind for e in events}
    assert DrumType.TOM_HIGH in kinds and DrumType.TOM_MID in kinds and DrumType.TOM_FLOOR in kinds

def test_rms_alone_cannot_create_snare():
    n=300; low=np.zeros(n); mid=np.zeros(n); high=np.zeros(n); rms=np.zeros(n); mid[100]=1.0; rms[100]=1.0
    events=analyze_drummer_features(low=low,mid=mid,high=high,rms=rms,frame_rate=100)
    assert events == []

def test_analyzer_never_emits_bus_fallback():
    events=analyze_drummer_features(low=_pulse(),mid=_pulse(),high=_pulse(),drum_low=_pulse(),drum_mid=_pulse(),drum_high=_pulse(),frame_rate=100)
    assert all(e.kind != "drum_bus" for e in events)
