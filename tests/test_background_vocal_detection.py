import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from core import audio_intelligence as ai
from core import snowman_band
from core import vocal_timeline as vt


def event(**kwargs):
    return ai.BackgroundVocalEvent(
        start_ms=2000, end_ms=2500, confidence=kwargs.get('confidence', 0.7),
        energy=kwargs.get('energy', 0.6), role='harmony',
        source_reason='test_classifier', performer_hint='bassist',
    )


@pytest.fixture
def timeline():
    return vt.LyricTimeline(lines=[], words=[], phoneme_events=[], confidence_summary={})


@pytest.fixture
def song_parts():
    return [vt.SongPart('chorus', 0, 5, 0.9, 0.8, ['vocals'], 'test')]


@pytest.mark.parametrize('events', [None, [], [event(confidence=0.1)], [event(energy=0.1)]])
def test_default_never_invents_background_windows_from_peaks(timeline, song_parts, events):
    assert vt.detect_background_vocal_windows(timeline, song_parts, [1000, 1500], classifier_events=events) == []


def test_peak_fallback_requires_explicit_opt_in(timeline, song_parts):
    config = vt.VocalRoutingConfig(allow_peak_fallback=True)
    windows = vt.detect_background_vocal_windows(timeline, song_parts, [1000], config)
    assert len(windows) == 1
    assert windows[0]['start_time'] == 1
    assert windows[0]['source_reason'] == 'chorus_vocal_energy_not_explained_by_lead'


def test_classifier_windows_take_precedence_even_with_fallback(timeline, song_parts):
    windows = vt.detect_background_vocal_windows(
        timeline, song_parts, [1000], vt.VocalRoutingConfig(allow_peak_fallback=True),
        classifier_events=[event()],
    )
    assert len(windows) == 1
    assert windows[0]['start_time'] == 2
    assert windows[0]['performer'] == 'bassist'


@pytest.fixture
def plan_args():
    return dict(
        parsed_layout=None, parts=[SimpleNamespace(label='CHORUS', start_ms=0, end_ms=5000)],
        lyric_events=[], note_events=[], beat_ms=[], kicks=[], snares=[], hats=[],
        bass_peaks=[], vocal_peaks=[1000], build_lifts=[], releases=[], enable_lyrics=False,
    )


def test_band_cues_use_classifier_window_times_and_provenance(plan_args):
    plan = snowman_band.build_snowman_band_plan(**plan_args, background_vocal_events=[event()])
    cues = plan['cues']['background_vocals']
    assert len(cues) == 1
    assert (cues[0]['start_ms'], cues[0]['end_ms']) == (2000, 2500)
    assert cues[0]['performer'] == 'bassist'
    assert cues[0]['source_reason'] == 'test_classifier'
    assert cues[0]['section'] == 'chorus'


def test_band_default_has_no_peak_only_cues(plan_args):
    plan = snowman_band.build_snowman_band_plan(**plan_args)
    assert plan['cues']['background_vocals'] == []
    assert plan['vocal_routing']['background_windows'] == []


def test_band_uses_old_peak_builder_only_when_opted_in_without_windows(plan_args, monkeypatch):
    monkeypatch.setattr(vt, 'detect_background_vocal_windows', lambda *a, **k: [])
    old = Mock(return_value=[{'start_ms': 1000, 'end_ms': 1120, 'performer': 'bassist'}])
    monkeypatch.setattr(snowman_band, '_build_background_vocals', old)
    assert snowman_band.build_snowman_band_plan(**plan_args)['cues']['background_vocals'] == []
    old.assert_not_called()
    plan = snowman_band.build_snowman_band_plan(
        **plan_args, routing_config=vt.VocalRoutingConfig(allow_peak_fallback=True),
    )
    assert plan['cues']['background_vocals'] == old.return_value
    old.assert_called_once_with(plan_args['vocal_peaks'], plan_args['parts'])


def test_band_opted_in_peak_windows_are_used_directly(plan_args):
    plan = snowman_band.build_snowman_band_plan(
        **plan_args, routing_config=vt.VocalRoutingConfig(allow_peak_fallback=True),
    )
    window = plan['vocal_routing']['background_windows'][0]
    cue = plan['cues']['background_vocals'][0]
    assert cue['start_ms'] == round(window['start_time'] * 1000)
    assert cue['end_ms'] == round(window['end_time'] * 1000)


def test_config_threshold_defaults_match_runtime_gates():
    config = ai.load_audio_analysis_config()
    routing = vt.load_vocal_routing_config()
    assert config.background_vocal_score_threshold == 0.56
    assert config.background_vocal_confidence_min == routing.background_vocal_confidence_min == 0.42
    assert config.background_vocal_energy_min == routing.background_vocal_energy_min == 0.35
    assert not routing.allow_peak_fallback


@pytest.fixture
def frame_features():
    return {'times_ms': np.array([0, 100, 200, 300]), 'score': np.full(4, 0.65),
            'rms01': np.full(4, 0.6)}


def test_config_score_threshold_changes_classifier_decision(tmp_path, monkeypatch, frame_features):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'background_vocal_score_threshold': 0.7,
                                'background_vocal_confidence_min': 0.75,
                                'background_vocal_energy_min': 0.8}))
    config = ai.load_audio_analysis_config(path)
    routing = vt.load_vocal_routing_config(path)
    assert config.background_vocal_score_threshold == 0.7
    assert routing.background_vocal_confidence_min == config.background_vocal_confidence_min == 0.75
    assert routing.background_vocal_energy_min == config.background_vocal_energy_min == 0.8
    monkeypatch.setattr(ai, '_background_vocal_frame_features', lambda p: frame_features)
    assert ai._classify_background_vocals(path, config=config) == []
    assert ai._classify_background_vocals(path, config=replace(config, background_vocal_score_threshold=0.6))


def test_routing_threshold_overrides_filter_events(timeline, song_parts, tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'background_vocal_confidence_min': 0.7, 'background_vocal_energy_min': 0.6}))
    config = vt.load_vocal_routing_config(path)
    assert vt.detect_background_vocal_windows(timeline, song_parts, [], config, [event()])
    assert not vt.detect_background_vocal_windows(timeline, song_parts, [], config, [event(confidence=0.699)])
    assert not vt.detect_background_vocal_windows(timeline, song_parts, [], config, [event(energy=0.599)])


@pytest.mark.parametrize('payload', ['{', 'null', '[]', '{"background_vocal_energy_min": "invalid"}'])
def test_bad_routing_config_uses_defaults(tmp_path, payload):
    path = tmp_path / 'settings.json'
    path.write_text(payload)
    assert vt.load_vocal_routing_config(path) == vt.VocalRoutingConfig()


def test_classifier_logs_exceptions_without_callback_and_reports_status(tmp_path, monkeypatch, caplog):
    def fail(path):
        raise RuntimeError('DSP unavailable')
    monkeypatch.setattr(ai, '_background_vocal_frame_features', fail)
    status = {}
    assert ai._classify_background_vocals(tmp_path / 'vocals.wav', status=status) == []
    assert status['status'] == 'error'
    assert status['error_type'] == 'RuntimeError'
    assert status['error'] == 'DSP unavailable'
    assert any(record.exc_info for record in caplog.records)
    assert 'Background vocal classifier failed' in caplog.text


def test_classifier_distinguishes_success_without_events_from_no_features(tmp_path, monkeypatch, frame_features):
    status = {}
    monkeypatch.setattr(ai, '_background_vocal_frame_features', lambda p: frame_features)
    ai._classify_background_vocals(tmp_path, config=ai.AudioAnalysisConfig(background_vocal_score_threshold=0.9), status=status)
    assert status['status'] == 'ok' and status['event_count'] == 0 and status['frame_count'] == 4
    monkeypatch.setattr(ai, '_background_vocal_frame_features', lambda p: {})
    ai._classify_background_vocals(tmp_path, status=status)
    assert status['status'] == 'no_features'


def test_analysis_debug_metadata_records_classifier_failure(tmp_path, monkeypatch):
    import soundfile
    path = tmp_path / 'audio.wav'
    soundfile.write(path, np.random.default_rng(1).normal(0, 0.1, 22050), 22050)
    monkeypatch.setattr(ai, '_background_vocal_frame_features', Mock(side_effect=ValueError('test failure')))
    result = ai.analyze_audio_file(path, cache_dir=tmp_path / 'cache', enable_lyrics=False)
    diagnostics = result.to_dict()['debug_summaries']['background_vocal_classifier']
    assert diagnostics['status'] == 'error'
    assert diagnostics['error_type'] == 'ValueError'
    assert diagnostics['stem_source'] == 'local'


def test_independent_pitch_count_rejects_weak_peaks_and_harmonics():
    # One harmonic series, two voices, four independent peaks, silence.
    hz = np.array([[220, 220, 220, 0], [440, 440, 310, 0], [660, 311, 371, 0],
                   [880, 880, 479, 0], [311, 371, 880, 0]], dtype=float)
    mag = np.array([[1, 1, 1, 0], [.7, .7, .7, 0], [.6, .6, .6, 0],
                    [.5, .3, .5, 0], [.19, .19, .4, 0]])
    counts = ai._independent_pitch_counts(hz, mag)
    np.testing.assert_array_equal(counts, [1, 2, 4, 0])
    np.testing.assert_allclose(np.clip((counts - 1) / 3, 0, 1), [0, 1 / 3, 1, 0])


def test_harmonic_tolerance_and_empty_pitch_frames():
    hz = np.array([[220, 220], [440 * 1.029, 440 * 1.031]])
    mag = np.array([[1, 1], [.7, .7]])
    np.testing.assert_array_equal(ai._independent_pitch_counts(hz, mag), [1, 2])
    assert ai._independent_pitch_counts(np.empty((0, 0)), np.empty((0, 0))).size == 0
