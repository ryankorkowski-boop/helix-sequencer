import csv
import json
from pathlib import Path
import shutil

import numpy as np
import pytest
import soundfile as sf

from tools.offline_vocal_candidates import load_stereo, run
from tools.phoneme_source import digest
from tools.vocal_diagnostic import export

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT/'fixtures/audio/Phoneme_Test_Hook.mp3'
FIXTURE = ROOT/'fixtures/audio/phoneme_vocal_separation'


def test_actual_source_timeline_preserves_silent_tail_and_independent_clocks(tmp_path):
    report = export(AUDIO, FIXTURE, tmp_path)
    assert report['source_audio_sha256'] == digest(AUDIO)
    assert report['independent_backing_verified'] is False
    rows = list(csv.DictReader((tmp_path/'Vocal_Timeline.csv').open()))
    assert len(rows) == 3488
    assert any(row['lead_active'] != row['backing_active'] for row in rows)
    assert all(row['lead_active'] == row['backing_active'] == '0'
               for row in rows if float(row['time_seconds']) >= 32.82)
    assert all(0 <= float(row['lead_speech_vad_probability']) <= 1 for row in rows)
    assert report['lanes']['lead']['active_seconds'] > report['lanes']['backing']['active_seconds'] > 0


def test_diagnostic_rejects_another_actual_recording(tmp_path):
    other = tmp_path/'other.wav'
    audio, sr = sf.read(AUDIO)
    sf.write(other, audio[:sr], sr)
    with pytest.raises(ValueError, match='checksum'):
        export(other, FIXTURE, tmp_path/'output')


def test_missing_confidence_remains_unavailable(tmp_path):
    fixture = tmp_path/'fixture'
    shutil.copytree(FIXTURE, fixture)
    with np.load(fixture/'acoustic_vocal_clocks.npz', allow_pickle=False) as cached:
        arrays = {key: cached[key] for key in cached.files if not key.endswith('_presence_probability')}
    np.savez_compressed(fixture/'acoustic_vocal_clocks.npz', **arrays)
    receipt = json.loads((fixture/'diagnostic.json').read_text())
    receipt['clock_sha256'] = digest(fixture/'acoustic_vocal_clocks.npz')
    (fixture/'diagnostic.json').write_text(json.dumps(receipt))
    report = export(AUDIO, fixture, tmp_path/'output')
    rows = list(csv.DictReader((tmp_path/'output/Vocal_Timeline.csv').open()))
    assert all(row['lead_speech_vad_probability'] == '' for row in rows)
    assert report['lanes']['lead']['speech_vad_available'] is False


def test_diagnostic_rejects_nonfinite_confidence_even_with_updated_clock_hash(tmp_path):
    fixture = tmp_path/'fixture'
    shutil.copytree(FIXTURE, fixture)
    with np.load(fixture/'acoustic_vocal_clocks.npz', allow_pickle=False) as cached:
        arrays = dict(cached)
    arrays['estimated_lead_presence_probability'] = np.full(3488, np.nan)
    np.savez_compressed(fixture/'acoustic_vocal_clocks.npz', **arrays)
    report = json.loads((fixture/'diagnostic.json').read_text())
    report['clock_sha256'] = digest(fixture/'acoustic_vocal_clocks.npz')
    (fixture/'diagnostic.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='probability'):
        export(AUDIO, fixture, tmp_path/'output')


def test_offline_separator_accepts_an_explicit_different_source_identity_before_model_checks(tmp_path):
    audio, sr = sf.read(AUDIO)
    excerpt = tmp_path/'actual_excerpt.wav'
    sf.write(excerpt, audio[:sr], sr)
    with pytest.raises(ValueError, match='source hash'):
        run(excerpt, tmp_path/'output', tmp_path/'models')
    with pytest.raises(FileNotFoundError):
        run(excerpt, tmp_path/'output', tmp_path/'models', expected_sha256=digest(excerpt))
    assert not (tmp_path/'output').exists()


def test_offline_separator_upmixes_real_mono_without_changing_clock(tmp_path):
    audio, sr = sf.read(AUDIO)
    mono = tmp_path/'mono.wav'
    sf.write(mono, audio[:sr].mean(axis=1), sr, subtype='FLOAT')
    stereo = load_stereo(mono)
    assert stereo.shape == (2, 44100)
    np.testing.assert_array_equal(stereo[0], stereo[1])
    from scipy.signal import resample_poly
    from math import gcd
    common = gcd(sr, 44100)
    expected = resample_poly(audio[:sr].mean(axis=1).astype('f4'), 44100//common, sr//common)
    np.testing.assert_allclose(stereo[0], expected, atol=1e-7)
