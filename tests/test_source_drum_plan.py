import json
import hashlib
import soundfile as sf
import numpy as np
import pytest
from tools.source_drum_plan import bind
from audio.drum_transcription import SCHEMA


def test_bound_polyphonic_drums_replace_only_percussion_and_preserve_source_clock(tmp_path):
    audio=tmp_path/'source.wav';sf.write(audio,np.zeros(16000),16000)
    original={'cues':{'drummer':[{'kind':'cymbal','start_ms':0}],
                      'keyboardist':[{'pitch_midi':21,'start_ms':103,'end_ms':207}]},
              'global_timeline':{'song_parts':[{'name':'chorus','start_time':0,'end_time':1}]}}
    rows=[dict(timestamp=t,drum_family=k,tom_class=None,confidence=.9,velocity=.8)
          for t,k in [(0.103,'kick'),(.103,'snare'),(.303,'hihat'),(.703,'cymbal')]]
    transcript=tmp_path/'transcript.json'
    transcript.write_text(json.dumps(dict(schema=SCHEMA,audio_sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),
        provenance={'engine':'source_test_model'},events=rows)))
    actual,receipt=bind(original,transcript,audio)
    assert actual['cues']['keyboardist']==original['cues']['keyboardist']
    assert original['cues']['drummer']==[{'kind':'cymbal','start_ms':0}]
    assert {(c['start_ms'],c['kind']) for c in actual['cues']['drummer']}=={
        (103,'kick'),(103,'snare'),(303,'hihat'),(703,'cymbal')}
    assert all(c['section']=='CHORUS' and c['end_ms']<=1000 for c in actual['cues']['drummer'])
    assert receipt['independent_accuracy_verified'] is False
    sf.write(audio,np.ones(16000)*.1,16000)
    with pytest.raises(ValueError,match='this song'):bind(original,transcript,audio)
