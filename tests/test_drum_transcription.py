"""Protect imported polyphonic evidence, without blessing model output as truth."""
import hashlib
import json
import numpy as np
import pytest
from audio.drum_transcription import load_drum_transcription, SCHEMA
from mapping.drum_mapper import schedule_drum_events, map_events_to_drummer_v3_poses, DrumMappingConfig
from tools.transcribe_drummer_adtof import resolve_tom_pitch


def write_transcript(tmp_path, events):
    audio=tmp_path/'song.wav';audio.write_bytes(b'identity fixture')
    path=tmp_path/'events.json'
    path.write_text(json.dumps(dict(schema=SCHEMA,audio_sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),
                                   provenance=dict(engine='external_audited_transcription'),events=events)))
    return path,audio


def row(family,tom=None,timestamp=1):
    return dict(timestamp=timestamp,drum_family=family,tom_class=tom,confidence=.8,velocity=.7)


def test_simultaneous_families_survive_import_scheduling_and_physical_mapping(tmp_path):
    path,audio=write_transcript(tmp_path,[row('kick'),row('snare'),row('hihat'),row('cymbal')])
    events,diag=load_drum_transcription(path,audio)
    mapped=map_events_to_drummer_v3_poses(schedule_drum_events(events,DrumMappingConfig(intro_gate_enabled=False)))
    assert len(mapped)==4
    assert {r['drum_type'] for r in mapped}=={'kick','snare','hihat','cymbal'}
    assert {r['timestamp_ms'] for r in mapped}=={1000}
    assert len({r['component'] for r in mapped})==4
    assert all(r['rejection_reason'] is None for r in diag['onset_audit'])


def test_foreign_song_cannot_consume_cached_transcription(tmp_path):
    path,audio=write_transcript(tmp_path,[row('kick')]);audio.write_bytes(b'other recording')
    with pytest.raises(ValueError,match='this song'):load_drum_transcription(path,audio)


def test_unknown_toms_and_auxiliary_percussion_never_fabricate_kit_hits(tmp_path):
    path,audio=write_transcript(tmp_path,[row('tom'),row('tom','unknown'),row('cowbell'),row('drum_bus')])
    events,diag=load_drum_transcription(path,audio)
    assert not events
    assert [r['rejection_reason'] for r in diag['onset_audit']]==['unresolved_tom_identity']*2+['unsupported_instrument']*2


def test_three_explicit_toms_map_deterministically(tmp_path):
    path,audio=write_transcript(tmp_path,[row('tom','high',1),row('tom','mid',2),row('tom','floor',3)])
    mapped=map_events_to_drummer_v3_poses(load_drum_transcription(path,audio)[0])
    assert [r['component'].split('_V3_')[1] for r in mapped]==['TOM_HIGH','TOM_MID','TOM_FLOOR']


@pytest.mark.parametrize('field,value',[('timestamp',-1),('timestamp',float('nan')),('confidence',2),('velocity',float('inf'))])
def test_invalid_transcription_values_fail_closed(tmp_path,field,value):
    event=row('kick');event[field]=value;path,audio=write_transcript(tmp_path,[event])
    with pytest.raises(ValueError):load_drum_transcription(path,audio)


def test_recording_calibration_uses_resonance_not_event_order():
    sr=44100;t=np.arange(round(.1*sr))/sr;refs=[137.3,94.2,78.1]
    for hz,expected in zip(refs,['high','mid','floor']):
        identity,evidence=resolve_tom_pitch(np.sin(2*np.pi*hz*t)*np.exp(-t*10),sr,refs)
        assert identity==expected
        assert abs(evidence['tom_peak_hz']-hz)<3
    assert resolve_tom_pitch(np.sin(2*np.pi*94.2*t),sr,None)[0] is None
    assert resolve_tom_pitch(np.random.default_rng(1).normal(size=len(t)),sr,refs)[0] is None
    assert resolve_tom_pitch(np.sin(2*np.pi*300*t),sr,refs)[0] is None


def test_transcription_engine_is_recorded_in_xsq_without_geometry_change(tmp_path):
    from pathlib import Path
    import xml.etree.ElementTree as ET
    from tools.integrate_drummer_v3_into_xsq import inject_drummer_v3
    path,audio=write_transcript(tmp_path,[row('kick'),row('hihat'),row('snare')])
    root=Path(__file__).resolve().parents[1]
    output=tmp_path/'result.xsq'
    report=inject_drummer_v3(root/'template.xsq',output,audio,transcription_path=path)
    assert report['detector']=='external_audited_transcription'
    assert report['event_count']==3
    effects=ET.parse(output).getroot().findall('.//Effect')
    generated=[e for e in effects if e.get('source')=='HelixDrummerV3']
    assert generated and {e.get('sourceDetector') for e in generated}=={'external_audited_transcription'}
    assert all(e.get('sourceRole')!='visual_geometry' or 'HI_HAT_ARM' not in e.get('sourceComponent','') for e in generated)
