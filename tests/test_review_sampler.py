import hashlib
import json
from pathlib import Path
from math import gcd
import numpy as np
from scipy.signal import resample_poly
import soundfile as sf
import pytest
from tools.build_review_sampler import build

ROOT = Path(__file__).resolve().parents[1]


def test_actual_audio_excerpts_reconstruct_from_recorded_source_ranges(tmp_path):
    rows = []
    for index, source in enumerate([ROOT/'fixtures/audio/Phoneme_Test_Hook.mp3', ROOT/'Tinsel Sawtooth (1).mp3']):
        audio, sr = sf.read(source, dtype='float32', always_2d=True)
        path = tmp_path/f'source{index}.wav'
        sf.write(path, audio[:sr*8], sr, subtype='FLOAT')
        rows.append(dict(local_path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         title=source.name, drive_id='test-source-'+str(index)))
    config = tmp_path/'sources.json'; config.write_text(json.dumps(rows))
    report = build(config, tmp_path/'sampler', seconds=2)
    actual, sr = sf.read(tmp_path/'sampler'/report['audio'], dtype='float32', always_2d=True)
    assert sr == 44100 and len(actual) == 44100*4
    assert report['duration_seconds'] == 4
    for index, row in enumerate(report['clips']):
        source, rate = sf.read(row['local_path'], dtype='float32', always_2d=True)
        cut = source[row['source_start_sample']:row['source_end_sample']]
        common = gcd(rate, sr)
        expected = resample_poly(cut, sr//common, rate//common, axis=0)
        start = index*2*sr
        # Edit fades are confined to the documented20ms edges.
        np.testing.assert_allclose(actual[start+882:start+2*sr-882], expected[882:-882]*report['output_gain'], atol=1/32768)
        assert hashlib.sha256(Path(row['local_path']).read_bytes()).hexdigest() == row['sha256']


def test_sampler_rejects_source_substitution(tmp_path):
    source = ROOT/'fixtures/audio/Phoneme_Test_Hook.mp3'
    config = tmp_path/'sources.json'
    config.write_text(json.dumps([dict(local_path=str(source), sha256='0'*64, title='owner source')]))
    with pytest.raises(ValueError, match='checksum'):
        build(config, tmp_path/'sampler')
    assert not list((tmp_path/'sampler').glob('*.wav'))


def test_duplicate_audio_with_different_headers_is_omitted_but_alternate_is_kept(tmp_path):
    wave,sr=sf.read(ROOT/'fixtures/audio/Phoneme_Test_Hook.mp3',dtype='float32',always_2d=True)
    wave=wave[:sr*4]
    rows=[]
    for i in range(3):
        path=tmp_path/f'{i}.wav'
        sf.write(path,wave if i<2 else wave*.5,sr,subtype='FLOAT')
        if i==1:
            # Ancillary bytes change the file hash without changing decoded audio.
            with path.open('ab') as stream:stream.write(b'different container metadata')
        rows.append(dict(local_path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),title=str(i)))
    config=tmp_path/'sources.json';config.write_text(json.dumps(rows))
    report=build(config,tmp_path/'sampler',seconds=2)
    assert [r['title'] for r in report['clips']]==['0','2']
    assert report['duplicates_omitted']==[dict(title='1',sha256=rows[1]['sha256'],duplicate_of='0')]
    assert report['duration_seconds']==4


def test_hot_decoded_audio_is_attenuated_without_pcm_clipping(tmp_path):
    wave,sr=sf.read(ROOT/'fixtures/audio/Phoneme_Test_Hook.mp3',dtype='float32',always_2d=True)
    wave=wave[:sr*4];wave*=1.3/max(float(np.max(np.abs(wave))),1e-8)
    path=tmp_path/'hot.wav';sf.write(path,wave,sr,subtype='FLOAT')
    before=path.read_bytes();config=tmp_path/'sources.json'
    config.write_text(json.dumps([dict(local_path=str(path),sha256=hashlib.sha256(before).hexdigest(),title='hot')]))
    report=build(config,tmp_path/'sampler',seconds=2)
    result,_=sf.read(tmp_path/'sampler'/report['audio'],dtype='float32')
    assert report['output_gain']<1 and report['peak_before_encoding']>1
    assert np.max(np.abs(result))<.981
    assert path.read_bytes()==before


def test_source_screened_interval_keeps_its_original_clock(tmp_path):
    source=ROOT/'fixtures/audio/Phoneme_Test_Hook.mp3'
    config=tmp_path/'screened.json'
    config.write_text(json.dumps([dict(local_path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        title='actual source',start_seconds=1.25)]))
    report=build(config,tmp_path/'sampler',seconds=2)
    row=report['clips'][0]
    assert row['source_start_seconds']==1.25
    wave,sr=sf.read(source,dtype='float32',always_2d=True)
    assert row['source_start_sample']==round(sr*1.25)
    assert row['source_end_sample']==round(sr*3.25)
    config.write_text(json.dumps([dict(local_path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        title='actual source',start_seconds=-1)]))
    with pytest.raises(ValueError,match='outside'):
        build(config,tmp_path/'invalid',seconds=2)
