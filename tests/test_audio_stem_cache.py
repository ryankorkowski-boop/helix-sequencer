"""Cache validation uses fake files; DSP checks use a short synthetic signal."""
import json
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from core import audio_intelligence as ai


@pytest.fixture
def cache_case(tmp_path, monkeypatch):
    audio = tmp_path / 'song.mp3'
    audio.write_bytes(b'audio one')
    cache = tmp_path / 'cache'

    def separate(audio_path, out_dir, log_fn, mix=None):
        stems = {name: out_dir / f'{name}.wav' for name in ('vocals', 'bass', 'drums', 'other')}
        for path in stems.values():
            path.write_bytes(b'stem')
        return stems

    local = Mock(side_effect=separate)
    monkeypatch.setattr(ai, 'librosa', Mock())
    monkeypatch.setattr(ai.shutil, 'which', Mock(return_value=None))
    monkeypatch.setattr(ai, '_local_stem_separation', local)
    monkeypatch.setattr(ai, '_try_demucs_stem_separation', Mock(return_value=None))
    monkeypatch.setattr(ai, '_try_moises_stem_separation', Mock(return_value=None))
    monkeypatch.setattr(ai, '_analyze_drum_events', Mock(return_value=([], [], [])))
    monkeypatch.setattr(ai.drum_intel, 'detect_drum_event_streams_from_file', Mock(return_value={}))
    monkeypatch.setattr(ai, '_analyze_peak_events', Mock(return_value=[]))
    monkeypatch.setattr(ai, '_classify_background_vocals', Mock(return_value=[]))
    monkeypatch.setattr(ai, '_summarize_stem_file', Mock(return_value={'confidence': 0.5}))
    return SimpleNamespace(
        audio=audio, cache=cache, local=local,
        manifest=cache / 'song' / 'stems_manifest.json',
        run=lambda **kw: ai.build_stem_analysis(audio, kw.pop('use_moises', False), None, cache, **kw),
    )


def test_cache_round_trip_and_separation_once_per_file(cache_case):
    c = cache_case
    first = c.run()
    second = c.run()
    assert first == second
    assert first.source == 'local'
    assert c.local.call_count == 1
    manifest = json.loads(c.manifest.read_text())
    assert manifest['fingerprint']['audio_sha256']
    # Timing analysis is still refreshed on a hit.
    assert ai._summarize_stem_file.call_count == 8
    other = c.audio.with_name('other.mp3')
    other.write_bytes(b'other audio')
    for _ in range(2):
        ai.build_stem_analysis(other, False, None, c.cache)
    assert c.local.call_count == 2


def test_relative_cache_paths_preserve_round_trip_metadata(cache_case, monkeypatch):
    c = cache_case
    monkeypatch.chdir(c.audio.parent)
    from pathlib import Path
    kwargs = dict(audio_path=Path('song.mp3'), use_moises=False, api_key=None, cache_dir=Path('relative_cache'))
    first = ai.build_stem_analysis(**kwargs)
    second = ai.build_stem_analysis(**kwargs)
    assert first == second
    assert c.local.call_count == 1


@pytest.mark.parametrize('change', ['content', 'moises', 'demucs', 'missing'])
def test_cache_invalidation(cache_case, change):
    c = cache_case
    first = c.run()
    kwargs = {}
    if change == 'content':
        c.audio.write_bytes(b'audio two')  # Same size; timestamps are not the key.
    elif change == 'moises':
        kwargs['use_moises'] = True
    elif change == 'demucs':
        ai.shutil.which.return_value = '/bin/demucs'
    else:
        first.stems['other'].unlink()
    c.run(**kwargs)
    assert c.local.call_count == 2


@pytest.mark.parametrize('escape', ['relative', 'absolute', 'symlink'])
def test_cache_rejects_path_escape(cache_case, escape):
    c = cache_case
    c.run()
    outside = c.cache / 'outside.wav'
    outside.write_bytes(b'outside')
    value = '../outside.wav' if escape == 'relative' else str(outside)
    if escape == 'symlink':
        link = c.manifest.parent / 'escaped.wav'
        link.symlink_to(outside)
        value = link.name
    manifest = json.loads(c.manifest.read_text())
    manifest['stems']['vocals'] = value
    c.manifest.write_text(json.dumps(manifest))
    c.run()
    assert c.local.call_count == 2


@pytest.mark.parametrize('bad', ['{', 'null', '[]', '{}', '{"fingerprint": []}',
                                  '{"stems": {"vocals": null}}'])
def test_corrupt_manifest_is_a_miss(cache_case, bad):
    c = cache_case
    c.run()
    c.manifest.write_text(bad)
    c.run()
    assert c.local.call_count == 2


def test_direct_fallback_is_not_cached(cache_case):
    c = cache_case
    c.local.side_effect = RuntimeError('cannot separate')
    for _ in range(2):
        assert c.run().source == 'direct'
    assert c.local.call_count == 2
    assert not c.manifest.exists()


def test_build_forwards_mix_to_local_separation(cache_case):
    mix = (np.ones(16), 22050, np.ones(16), np.zeros(16))
    cache_case.run(mix=mix)
    assert cache_case.local.call_args.kwargs['mix'] is mix


def test_local_mix_reuse_matches_original_without_load_or_hpss(tmp_path, monkeypatch):
    import librosa
    y = np.random.default_rng(5).normal(0, 0.1, 4096).astype(np.float32)
    harm, perc = librosa.effects.hpss(y)
    load = Mock(return_value=(y, 22050))
    hpss = Mock(return_value=(harm, perc))
    monkeypatch.setattr(librosa, 'load', load)
    monkeypatch.setattr(librosa.effects, 'hpss', hpss)
    monkeypatch.setattr(ai, 'librosa', librosa)
    written = []
    monkeypatch.setattr(ai, '_write_audio', lambda path, data, sr: written.append((data.copy(), sr)))
    ai._local_stem_separation(tmp_path / 'song.wav', tmp_path, None)
    assert load.call_count == hpss.call_count == 1
    original = list(written)
    written.clear()
    ai._local_stem_separation(tmp_path / 'song.wav', tmp_path, None, mix=(y, 22050, harm, perc))
    assert load.call_count == hpss.call_count == 1
    for (before, sr_before), (after, sr_after) in zip(original, written):
        np.testing.assert_array_equal(before, after)
        assert sr_before == sr_after


def test_analyze_passes_its_computed_mix(tmp_path, monkeypatch):
    import librosa
    import soundfile
    path = tmp_path / 'mix.wav'
    soundfile.write(path, np.random.default_rng(8).normal(0, 0.1, 22050), 22050)
    load, hpss = Mock(wraps=librosa.load), Mock(wraps=librosa.effects.hpss)
    monkeypatch.setattr(librosa, 'load', load)
    monkeypatch.setattr(librosa.effects, 'hpss', hpss)
    monkeypatch.setattr(ai, 'librosa', librosa)

    class MixReceived(Exception):
        pass

    def receive(*args, mix, **kwargs):
        y, sr, harm, perc = mix
        assert sr == 22050 and len(y) == len(harm) == len(perc) == 22050
        assert load.call_count == hpss.call_count == 1
        raise MixReceived

    monkeypatch.setattr(ai, 'build_stem_analysis', receive)
    with pytest.raises(MixReceived):
        ai.analyze_audio_file(path, enable_lyrics=False)


def test_stem_summary_uses_one_stft_with_same_band_totals(tmp_path, monkeypatch):
    path = tmp_path / 'stem.wav'
    path.touch()
    spectrum = np.array([[1, 2], [3, 4], [5, 6]], dtype=complex)
    fake = SimpleNamespace(
        load=Mock(return_value=(np.ones(2048), 22050)),
        feature=SimpleNamespace(rms=Mock(return_value=np.array([[0.5, 1.0]]))),
        onset=SimpleNamespace(onset_strength=Mock(return_value=np.zeros(2))),
        util=SimpleNamespace(peak_pick=Mock(return_value=np.array([], dtype=int))),
        frames_to_time=lambda frames, **kw: np.asarray(frames) * 512 / 22050,
        stft=Mock(return_value=spectrum),
        fft_frequencies=Mock(return_value=np.array([100, 1000, 4000])),
    )
    monkeypatch.setattr(ai, 'librosa', fake)
    result = ai._summarize_stem_file(path, stem_name='bass', sensitivity=0.72, max_events_per_second=18)
    assert fake.stft.call_count == 1
    assert result['dominant_frequency_bands'] == {
        'low': round(3 / 21, 4), 'mid': round(7 / 21, 4), 'high': round(11 / 21, 4),
    }
