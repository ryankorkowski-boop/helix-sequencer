import numpy as np
from tools.analyze_residual_keyboard import residual_notes


def test_residual_pitched_lane_is_active_on_music_and_abstains_on_identical_voice():
    sr=16000;t=np.arange(sr*2)/sr
    note=np.where(t<1,261.6256,329.6276)
    phase=np.cumsum(2*np.pi*note/sr)
    wave=.3*np.sin(phase)+.1*np.sin(phase*2)+.06*np.sin(phase*3)
    events,proof=residual_notes(wave,np.zeros_like(wave),40)
    assert events and all(e.confidence>=.75 and e.source=='other_harmonic_pitched_estimate' for e in events)
    duplicate,proof=residual_notes(wave,wave,40)
    assert duplicate==[]
