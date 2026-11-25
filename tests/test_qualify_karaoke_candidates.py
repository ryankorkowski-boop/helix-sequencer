import json
import numpy as np
import pytest
import soundfile as sf
from tools.phoneme_source import digest
from tools.qualified_keyboard import ROLES, WEIGHT_SHA256
from tools.qualify_karaoke_candidates import qualify


def test_quiet_residual_and_changed_output(tmp_path):
    sr=44100; t=np.arange(sr*3)/sr
    audio=tmp_path/'source.wav'; sf.write(audio,np.stack([.1*np.sin(2*np.pi*220*t)]*2,axis=1),sr)
    tracks={}
    for i,role in enumerate(ROLES):
        p=tmp_path/(role+'.wav'); sf.write(p,np.stack([.01*(i+1)*np.sin(2*np.pi*(220+i)*t)]*2,axis=1),sr)
        tracks[role]={'path':p.name,'sha256':digest(p)}
    manifest=tmp_path/'keyboard_stems.json'
    manifest.write_text(json.dumps(dict(schema='helix.keyboard_stems.v1',model='htdemucs_6s',weight_sha256=WEIGHT_SHA256,source_sha256=digest(audio),tracks=tracks)))
    out=[]
    for name,amplitude,freq in [('candidate_a.wav',.1,220),('candidate_b.wav',.006,330)]:
        p=tmp_path/name; sf.write(p,amplitude*np.sin(2*np.pi*freq*t),sr); out.append({'path':name,'sha256':digest(p)})
    receipt=tmp_path/'candidate_receipt.json'
    receipt.write_text(json.dumps(dict(schema='helix.offline_karaoke_candidates.v1',source_sha256=digest(audio),stem_manifest_sha256=digest(manifest),combined_vocals_sha256=tracks['vocals']['sha256'],outputs=out)))
    report=qualify(audio,manifest,receipt)
    assert report['screened_activity_seconds'][1]==0
    assert not report['estimated_review_activity_pass']
    assert not report['singer_identity_verified']
    sf.write(tmp_path/'candidate_b.wav',np.zeros(sr*3),sr)
    with pytest.raises(ValueError,match='Changed karaoke output'):
        qualify(audio,manifest,receipt)


def test_estimated_fixture_and_excerpt_share_absolute_floor(tmp_path):
    from tools.roformer_review_fixture import build
    from tools.select_vocal_review_excerpt import choose
    from music.review_score import vocal_clock
    sr=16000; t=np.arange(sr*30)/sr
    source=tmp_path/'source.wav'; sf.write(source,.1*np.sin(2*np.pi*220*t),sr)
    tracks={}
    for role,amp,freq in [('lead',.1,220),('backing',.006,330)]:
        p=tmp_path/(role+'.wav'); sf.write(p,amp*np.sin(2*np.pi*freq*t),sr)
        tracks[role]={'path':p.name,'sha256':digest(p)}
    # Prior relative-only detector really does see this weak periodic residual.
    assert np.any(vocal_clock(sf.read(tmp_path/'backing.wav')[0])['energy']>0)
    manifest=tmp_path/'vocal_manifest.json'; manifest.write_text(json.dumps(dict(source_sha256=digest(source),**tracks)))
    out=tmp_path/'fixture'; build(source,manifest,out)
    with np.load(out/'acoustic_vocal_clocks.npz') as z:
        assert np.any(z['estimated_lead_energy']>0)
        assert not np.any(z['estimated_backing_energy'])
        assert not np.any(z['estimated_backing_shapes'])
    with pytest.raises(ValueError,match='No 30-second passage'):
        choose(source,manifest,tmp_path/'excerpt.wav',tmp_path/'selected')
