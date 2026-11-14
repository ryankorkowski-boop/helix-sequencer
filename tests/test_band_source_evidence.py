import json

import numpy as np
import pytest
import soundfile as sf

from models.band_performance_scene import string_assignment
from tools.band_source_evidence import apply_evidence
from tools.phoneme_source import digest


def test_source_instrument_export_preserves_other_lanes_and_requires_exact_audio(tmp_path):
    audio = tmp_path/'song.wav'
    sf.write(audio, np.zeros(800), 8000)
    cue = {'performer': 'bassist', 'pitch_midi': 24, 'start_ms': 10, 'end_ms': 90}
    payload = {'audio_sha256': digest(audio), 'bass_tuning_midi': [24, 31, 36, 41],
               'cues': {'drummer': [], 'bassist': [cue], 'guitarist': [], 'keyboardist': []}}
    evidence = tmp_path/'evidence.json'
    evidence.write_text(json.dumps(payload))
    plan = {'cues': {'bassist': [], 'lead': [{'start_ms': 20, 'end_ms': 70}]}}
    updated = apply_evidence(plan, audio, evidence)
    assert updated['cues']['lead'] == plan['cues']['lead']
    assert updated['cues']['bassist'] == [cue] and plan['cues']['bassist'] == []
    assert string_assignment(24, 'bass', tuning=updated['bass_tuning_midi']) == (0, 0)
    assert string_assignment(24, 'bass') is None
    sf.write(audio, np.ones(800), 8000)
    with pytest.raises(ValueError, match='soundtrack'):
        apply_evidence(plan, audio, evidence)
