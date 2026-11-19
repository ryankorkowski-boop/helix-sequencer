import json
import subprocess
import wave

import numpy as np
import pytest

from tools.audio_excerpt import extract, timestamp


@pytest.fixture
def audio(tmp_path):
    path = tmp_path / 'source.wav'
    t = np.arange(46 * 8000) / 8000
    samples = np.column_stack((np.sin(t * 1382.3), np.sin(t * 1741.9)))
    samples = (samples * 16000).astype('<i2')
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((2, 2, 8000, 0, 'NONE', 'not compressed'))
        stream.writeframes(samples.tobytes())
    return path, samples


@pytest.mark.parametrize('start,end', [(4, 34), (3, 45), (5.123, 41.123)])
def test_exact_original_samples_and_timing(audio, tmp_path, start, end):
    source, samples = audio
    target = tmp_path / 'clip.wav'
    before = source.read_bytes()
    report = extract(source, target, start=start, end=end)
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(target),
                                   '-f', 's16le', '-'])
    actual = np.frombuffer(raw, '<i2').reshape(-1, 2)
    np.testing.assert_array_equal(actual, samples[round(start*8000):round(end*8000)])
    assert report['duration_seconds'] == pytest.approx(end-start, abs=1/8000)
    assert report['sample_rate'] == 8000 and report['channels'] == 2
    assert json.loads(target.with_suffix('.excerpt.json').read_text()) == report
    assert source.read_bytes() == before


@pytest.mark.parametrize('start,end', [(0, 47), (25, 60), (-1, 32),
                                       (0, float('nan')), (0, 29), (0, 43)])
def test_bad_range_never_replaces_existing_excerpt(audio, tmp_path, start, end):
    target = tmp_path / 'clip.wav'
    target.write_bytes(b'previous good artifact')
    with pytest.raises(ValueError):
        extract(audio[0], target, start=start, end=end)
    assert target.read_bytes() == b'previous good artifact'


def test_missing_and_corrupt_fail_without_output(tmp_path):
    target = tmp_path / 'clip.wav'
    with pytest.raises(FileNotFoundError):
        extract(tmp_path / 'missing.wav', target)
    corrupt = tmp_path / 'corrupt.mp3'
    corrupt.write_bytes(b'not audio')
    with pytest.raises(subprocess.CalledProcessError):
        extract(corrupt, target)
    assert not target.exists()


def test_timestamp_formats():
    assert timestamp('1:02.125') == 62.125
    assert timestamp('1:02:03') == 3723
    for bad in ['nan', '-1', '1:60', 'inf', '1:2:3:4']:
        with pytest.raises(ValueError):
            timestamp(bad)
