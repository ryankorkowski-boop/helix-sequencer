import numpy as np
from core.drummer_v3_analysis import DrumType, analyze_drummer_features

def _pulse(n=400, idx=(50,150,250)):
    x=np.zeros(n)
    for i in idx:x[i]=1.0
    return x

def test_typed_events_require_independent_or_stem_evidence():
    low=_pulse(); mid=_pulse(idx=(75,175,275)); high=_pulse(idx=(25,125,225))
    events=analyze_drummer_features(low=low,mid=mid,high=high,drum_low=low,drum_mid=mid,drum_high=high,frame_rate=100)
    kinds={e.kind for e in events}
    assert DrumType.KICK in kinds and DrumType.SNARE in kinds and DrumType.HI_HAT in kinds

def test_drum_stem_adds_three_tom_targets():
    n=500; low=np.zeros(n); mid=np.zeros(n); high=np.zeros(n); drum_low=np.zeros(n); drum_mid=np.zeros(n); drum_high=np.zeros(n)
    drum_mid[100]=1.0; drum_low[100]=1.0; drum_mid[200]=1.0; drum_low[200]=0.5; drum_mid[300]=1.0; drum_low[300]=0.1
    events=analyze_drummer_features(low=low,mid=mid,high=high,drum_low=drum_low,drum_mid=drum_mid,drum_high=drum_high,frame_rate=100)
    kinds={e.kind for e in events}
    assert DrumType.TOM_HIGH in kinds and DrumType.TOM_MID in kinds and DrumType.TOM_FLOOR in kinds

def test_rms_transient_can_confirm_snare():
    n=300; low=np.zeros(n); mid=np.zeros(n); high=np.zeros(n); rms=np.zeros(n); mid[100]=1.0; rms[100]=1.0
    events=analyze_drummer_features(low=low,mid=mid,high=high,rms=rms,frame_rate=100)
    assert any(e.kind==DrumType.SNARE for e in events)

def test_analyzer_never_emits_bus_fallback():
    events=analyze_drummer_features(low=_pulse(),mid=_pulse(),high=_pulse())
    assert all(e.kind not in ("drum_bus",DrumType) for e in events)
