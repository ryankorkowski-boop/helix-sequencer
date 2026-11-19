"""Protect human-reviewed real-audio tom anchors and conservative review import."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from audio.drum_review import SCHEMA, apply_tom_review
from audio.drum_transcription import load_drum_transcription
from tools.integrate_drummer_v3_into_xsq import inject_drummer_v3
from tools.render_drummer_v3_preview import parse_effects, _active_targets_for_frame

ROOT = Path(__file__).resolve().parents[1]


def write_review(tmp_path, annotation=None, digest='source'):
    path=tmp_path/'review.json'
    path.write_text(json.dumps(dict(schema=SCHEMA,audio_sha256=digest,annotations=[annotation or dict(
        timestamp=1.,tolerance_ms=40,drum_family='tom',tom_class='high',label_source='user_listening')])))
    return path


def candidate(timestamp=1.,reason='unresolved_tom_identity'):
    return dict(timestamp=timestamp,drum_family='tom',tom_class=None,confidence=.8,velocity=.7,
                rejection_reason=reason,evidence=dict(tom_identity_method='insufficient_resonance'))


def test_review_preserves_attack_dynamics_and_original_rejection_without_mutating_input(tmp_path):
    row=candidate();path=write_review(tmp_path)
    out,meta=apply_tom_review([row], 'source',path)
    assert row==candidate()
    assert out[0]['tom_class']=='high' and out[0]['rejection_reason'] is None
    assert {k:out[0][k] for k in ('timestamp','confidence','velocity')}=={k:row[k] for k in ('timestamp','confidence','velocity')}
    assert out[0]['evidence']['tom_review']['original_rejection_reason']=='unresolved_tom_identity'
    assert meta['resolved_event_count']==1


@pytest.mark.parametrize('rows,digest',[
    ([candidate()], 'different_audio'),
    ([], 'source'),
    ([candidate(2.)], 'source'),
    ([candidate(),candidate(1.02)], 'source'),
    ([candidate(reason='low_quality_attack')], 'source'),
])
def test_review_cannot_invent_attacks_choose_ambiguous_notes_or_bypass_other_gates(tmp_path,rows,digest):
    with pytest.raises(ValueError):apply_tom_review(rows,digest,write_review(tmp_path))


@pytest.mark.parametrize('field,value',[
    ('tom_class','unknown'),('drum_family','drum_bus'),('tolerance_ms',500),
    ('timestamp',float('nan')),('label_source',''),
])
def test_review_requires_finite_local_timing_explicit_class_and_label_source(tmp_path,field,value):
    annotation=dict(timestamp=1.,tolerance_ms=40,drum_family='tom',tom_class='high',label_source='user_listening')
    annotation[field]=value
    with pytest.raises(ValueError):apply_tom_review([candidate()],'source',write_review(tmp_path,annotation))


def test_real_reviewed_tom_fill_survives_import_scheduler_xsq_and_preview(tmp_path):
    audio=ROOT/'evidence/drummer/dry_drum_test.wav'
    transcript=ROOT/'evidence/drummer/dry_drum_test_adtof.json'
    review=ROOT/'evidence/drummer/dry_drum_test_tom_review.json'
    anchors=json.loads((ROOT/'tests/fixtures/drummer/dry_user_tom_anchors.json').read_text())
    assert hashlib.sha256(audio.read_bytes()).hexdigest()==anchors['audio_sha256']
    before,baseline=load_drum_transcription(transcript,audio)
    after,analysis=load_drum_transcription(transcript,audio,review)
    assert [e for e in before if e.drum_type!='tom']==[e for e in after if e.drum_type!='tom']
    assert all(row['rejection_reason']=='unresolved_tom_identity' for row in baseline['onset_audit'] if row['drum_family']=='tom')
    untouched=[row for row in analysis['onset_audit'] if row['drum_family']=='tom' and not row['primary'].get('tom_review')]
    assert untouched and all(row['rejection_reason']=='unresolved_tom_identity' for row in untouched)
    out=tmp_path/'reviewed.xsq'
    report=inject_drummer_v3(ROOT/'template.xsq',out,audio,transcription_path=transcript,review_path=review)
    effects=parse_effects(out)
    root=ET.parse(out).getroot()
    for anchor in anchors['anchors']:
        matches=[r for r in report['analysis']['onset_audit'] if r['drum_family']=='tom'
                 and abs(r['timestamp']-anchor['timestamp'])*1000<=anchor['tolerance_ms']]
        assert len(matches)==1
        row=matches[0];target='HX_SNOWMAN_DRUMMER_V3_'+anchor['physical_target']
        assert row['primary']['tom_class']==anchor['tom_class']
        assert row['scheduler_decision']=='scheduled' and row['physical_target']==target
        assert target in _active_targets_for_frame(effects,anchor['timestamp']*1000,60)
        assert root.findall(f'./ElementEffects/Element[@name="{target}_SURFACE"]/EffectLayer/Effect')
