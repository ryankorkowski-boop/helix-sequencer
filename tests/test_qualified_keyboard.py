import json
import numpy as np
import pytest
import soundfile as sf
from tools.qualified_keyboard import ROLES, WEIGHT_SHA256, cues, verified_piano
from tools.phoneme_source import digest


def fixture(tmp_path, silent=False):
    source=tmp_path/'source.wav'; sf.write(source,np.zeros((4410,2)),44100)
    tracks={}
    for i,role in enumerate(ROLES):
        p=tmp_path/(role+'.wav');y=np.zeros((4410,2)) if silent and role=='piano' else np.full((4410,2),.01*(i+1))
        sf.write(p,y,44100);tracks[role]={'path':p.name,'sha256':digest(p)}
    manifest=tmp_path/'keyboard_stems.json'
    manifest.write_text(json.dumps(dict(schema='helix.keyboard_stems.v1',model='htdemucs_6s',
        source_sha256=digest(source),weight_sha256=WEIGHT_SHA256,tracks=tracks)))
    return source,manifest


def test_verified_piano_rejects_changed_source_or_track(tmp_path):
    audio,manifest=fixture(tmp_path)
    assert verified_piano(audio,manifest).name=='piano.wav'
    sf.write(tmp_path/'piano.wav',np.zeros((4410,2)),44100)
    with pytest.raises(ValueError,match='changed source stem'):
        verified_piano(audio,manifest)


def test_silent_stem_abstains(tmp_path):
    audio,manifest=fixture(tmp_path,silent=True)
    notes,report=cues(audio,manifest)
    assert not notes and report['status']=='inaudible_stem_abstention'


def test_stem_confidence_gate_preserves_real_note_provenance(tmp_path,monkeypatch):
    from core import audio_intelligence as ai
    audio,manifest=fixture(tmp_path)
    def extract(y,sr,*,source_stem,config):
        assert source_stem=='piano'
        return [ai.NoteEvent(10,50,440,69,'A4',.8,.9,'piano'),
                ai.NoteEvent(10,50,440,69,'A4',.8,.2,'piano'),
                ai.NoteEvent(10,50,440,69,'A4',.8,.99,'guitar')], []
    monkeypatch.setattr(ai,'_extract_note_candidates',extract)
    notes,report=cues(audio,manifest)
    assert len(notes)==1 and notes[0]['source_owner']['source_id']=='piano'
    assert report['accepted']==1 and not report['instrument_identity_verified']
