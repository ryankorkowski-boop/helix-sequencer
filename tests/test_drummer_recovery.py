"""Historical behavior and independent sparse signal anchors, not acceptance."""
import hashlib
import json
from pathlib import Path
from collections import Counter
import numpy as np
import pytest
from audio.drummer_v3 import analyze_drummer_audio, analyze_drummer_samples, DrumDetectionConfig
from mapping.drum_mapper import schedule_drum_events, DrumMappingConfig

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope="module")
def song():
    p=ROOT/'Helix Audiolights.mp3'
    if not p.exists():pytest.skip('song fixture unavailable')
    events,diagnostics=analyze_drummer_audio(p)
    return schedule_drum_events(events,DrumMappingConfig(intro_gate_enabled=False)),diagnostics


def test_independent_sparse_signal_anchors_and_false_bursts(song):
    events,_=song
    fixture=json.loads((ROOT/'tests/fixtures/drummer/helix_audio_anchors.json').read_text())
    assert hashlib.sha256((ROOT/fixture['audio']).read_bytes()).hexdigest()==fixture['audio_sha256']
    for anchor in fixture['anchors']:
        nearby=[e for e in events if abs(e.timestamp-anchor['timestamp'])<=anchor['tolerance_ms']/1000]
        assert any(e.drum_type==anchor['family'] for e in nearby), (anchor,[(e.timestamp,e.drum_type) for e in nearby])
    for region in fixture['excluded_regions']:
        assert not any(region['start']<=e.timestamp<region['end'] for e in events)
    for family,limit in fixture['burst_limits_per_second'].items():
        times=[e.timestamp for e in events if e.drum_type==family]
        assert all(sum(t<=v<t+1 for v in times)<=limit for t in times)


def test_historical_missing_attacks_survive_at_original_grid(song):
    events,diagnostics=song
    # From the b27e8d77 historical stream, not labels derived from new output.
    for t in [11.9893,14.5813,15.5733,16.224,19.1573,19.808]:
        assert any(e.drum_type=='kick' and abs(e.timestamp-t)<.001 for e in events), t
    assert diagnostics['source_sample_rate']==48000
    assert diagnostics['analysis_sample_rate']==48000
    assert diagnostics['hpss_margin']==1
    assert diagnostics['onset_delta']==.045
    assert diagnostics['onset_wait']==1
    assert all(e.frequency_band_info['timing_refinement_ms']==0 for e in events)


def test_every_candidate_has_a_traceable_decision(song):
    events,diag=song
    audit=diag['onset_audit']
    assert len(audit)==diag['onset_candidate_count']
    assert len({r['source_onset_index'] for r in audit})==len(audit)
    for r in audit:
        assert r['primary']['event_frame']>=0
        assert r['rejection_reason'] is not None or r['scheduler_decision']=='pending'
    assert all(e.frequency_band_info['onset_index'] in {r['source_onset_index'] for r in audit} for e in events)
    assert 'drum_bus' not in Counter(e.drum_type for e in events)


def test_silence_and_sustained_harmonics_do_not_drive_drummer():
    sr=48000
    assert analyze_drummer_samples(np.zeros(sr),sr)[0]==[]
    t=np.arange(sr*2)/sr
    # Sustained guitar-like partials with a slow onset, not a fabricated drum stem.
    y=(np.sin(2*np.pi*196*t)+.5*np.sin(2*np.pi*392*t)+.25*np.sin(2*np.pi*588*t))*np.minimum(t/.15,1)*np.exp(-t*1.5)
    events,_=analyze_drummer_samples(y.astype(np.float32),sr)
    assert events==[]


def test_tom_pitch_abstention_is_not_a_target_quota():
    from audio.drummer_v3 import _tom_class_from_spectrum
    f=np.linspace(0,1000,1001)
    assert _tom_class_from_spectrum(np.ones_like(f),f)[0] is None
    assert _tom_class_from_spectrum(np.exp(-((f-90)/8)**2),f)[0] is None


def test_principal_candidate_stream_matches_archived_approved_run(song):
    _,diag=song
    fixture=json.loads((ROOT/'tests/fixtures/drummer/b27_archived_timeline.json').read_text())
    actual={(round(r['timestamp']*1000),r['drum_family']) for r in diag['onset_audit']}
    # Compare raw principal classifications before documented safety rejection.
    # This does not require the obsolete intro/bus/tom fallbacks to emit.
    assert len(fixture['events'])==400
    assert all((r['timestamp_ms'],r['family']) in actual for r in fixture['events'])
