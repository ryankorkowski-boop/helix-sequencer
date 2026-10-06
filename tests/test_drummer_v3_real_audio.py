"""Song-specific regression gates, not a substitute for auditory annotation."""
from pathlib import Path
import pytest
from collections import Counter
from audio.drummer_v3 import analyze_drummer_audio
from mapping.drum_mapper import map_events_to_drummer_v3_poses, schedule_drum_events, DrumMappingConfig

@pytest.fixture(scope='module')
def song_events():
    path=Path(__file__).resolve().parents[1]/'Helix Audiolights.mp3'
    if not path.exists():
        pytest.skip('Real-song fixture not available')
    return analyze_drummer_audio(path)[0]


def test_known_non_drum_intro_and_first_real_entrance(song_events):
    assert song_events
    assert not [e for e in song_events if e.timestamp < 10]
    first = min(song_events, key=lambda event: event.timestamp)
    assert 10.7 <= first.timestamp <= 11.3
    assert first.drum_type == "kick"


def test_real_song_has_no_impossible_dense_snare_or_crash_burst(song_events):
    # Generous sanity ceilings; these do not validate individual classifications.
    for kind, ceiling in [('snare',8),('cymbal',6)]:
        times=[e.timestamp for e in song_events if e.drum_type==kind]
        assert max(sum(t<=u<t+1 for u in times) for t in times)<=ceiling


def test_real_song_retains_body_metal_coincidences_and_tom_evidence(song_events):
    assert all(e.drum_type!='drum_bus' for e in song_events)
    scheduled=schedule_drum_events(song_events,DrumMappingConfig(intro_gate_enabled=False))
    poses=map_events_to_drummer_v3_poses(scheduled)
    assert any(n>=2 for n in Counter(p['timestamp_ms'] for p in poses).values())
    by_key={(e.timestamp_ms,e.drum_type):e for e in song_events}
    for p in poses:
        e=by_key[p['timestamp_ms'],p['drum_type']]
        if e.drum_type=='tom':
            assert p['tom_class']==e.frequency_band_info['tom_class']
            assert p['tom_class_source']=='detected_tom_class'
        assert e.frequency_band_info['percussive_ratio']>=.36
