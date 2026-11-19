"""Source-grounded missed-note coverage, without treating ML labels as truth."""
import json
from pathlib import Path

import pytest

from audio.drum_source_calibration import apply_source_calibration
from audio.drum_transcription import load_drum_transcription
from tools.integrate_drummer_v3_into_xsq import inject_drummer_v3
from tools.render_drummer_v3_preview import parse_effects, _active_targets_for_frame

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / 'evidence/drummer/dry_drum_test.wav'
TRANSCRIPT = ROOT / 'evidence/drummer/dry_drum_test_adtof.json'
REVIEW = ROOT / 'evidence/drummer/dry_drum_test_tom_review.json'
CALIBRATION = ROOT / 'evidence/drummer/dry_drum_test_source_calibration.json'


def calibrated(tmp_path, **changes):
    data = json.loads(CALIBRATION.read_text())
    data.update(changes)
    path = tmp_path / 'calibration.json'
    path.write_text(json.dumps(data))
    return path


def test_foreign_audio_and_invalid_exemplar_calibrations_fail_closed(tmp_path):
    raw = json.loads(TRANSCRIPT.read_text())['events']
    with pytest.raises(ValueError, match='this song'):
        apply_source_calibration(raw, AUDIO, calibrated(tmp_path, audio_sha256='other source'))
    with pytest.raises(ValueError, match='scope'):
        apply_source_calibration(raw, AUDIO, calibrated(tmp_path, scope_seconds=[35, 32]))
    data = json.loads(CALIBRATION.read_text())
    data['exemplars'][0]['tom_class'] = 'unknown'
    with pytest.raises(ValueError, match='identity'):
        apply_source_calibration(raw, AUDIO, calibrated(tmp_path, exemplars=data['exemplars']))
    with pytest.raises(ValueError, match='three tom alternatives'):
        apply_source_calibration(raw, AUDIO, calibrated(tmp_path, exemplars=data['exemplars'][3:]))


def test_correction_preserves_accepted_events_reviewed_toms_timing_dynamics_and_original_evidence():
    raw = json.loads(TRANSCRIPT.read_text())['events']
    before, _ = load_drum_transcription(TRANSCRIPT, AUDIO, REVIEW)
    after, analysis = load_drum_transcription(TRANSCRIPT, AUDIO, REVIEW, CALIBRATION)
    assert [e for e in before if e.drum_type != 'tom'] == [e for e in after if not e.frequency_band_info.get('source_calibration') and e.drum_type != 'tom']
    assert [e for e in before if e.drum_type == 'tom'] == [e for e in after if e.frequency_band_info.get('tom_review')]
    for original, row in zip(raw, analysis['onset_audit']):
        decision = row['primary'].get('source_calibration')
        assert row['timestamp'] == original['timestamp'] and row['velocity'] == original['velocity']
        assert row['confidence'] == original['confidence']
        assert row['drum_family'] == original['drum_family']
        if decision:
            assert original['drum_family'] == decision['original_family'] == 'tom'
            assert original['confidence'] == decision['original_confidence']
            assert decision['original_rejection_reason'] == 'unresolved_tom_identity'
        elif not row['primary'].get('tom_review'):
            assert row['drum_family'] == original['drum_family']
            assert row['confidence'] == original['confidence']
    assert analysis['source_calibration']['review_status'] == 'source_inspected_inference_pending_user_listening'
    assert analysis['review_status'] == 'model_inferred_pending_human_listening'


def test_nearly_identical_high_mid_timbres_abstain_instead_of_cycling(tmp_path):
    # This recording's high and mid body modes are only about 4 Hz apart.
    raw = [r for r in json.loads(TRANSCRIPT.read_text())['events'] if r['drum_family'] == 'tom' and r['timestamp'] in {9.69, 10.01}]
    out, _ = apply_source_calibration(raw, AUDIO, calibrated(tmp_path, scope_seconds=[9.5, 10.2]))
    assert all(r['tom_class'] is None and r['rejection_reason'] == 'unresolved_tom_identity' for r in out)
    assert all(not r['evidence']['source_calibration']['accepted'] for r in out)


def test_calibration_cannot_bypass_other_rejections_or_launder_invalid_original_confidence(tmp_path):
    payload = json.loads(TRANSCRIPT.read_text())
    row = next(r for r in payload['events'] if r['timestamp'] == 32.36)
    blocked = dict(row, rejection_reason='unsupported_attack')
    out, _ = apply_source_calibration([blocked], AUDIO, CALIBRATION)
    assert out == [blocked] and out[0] is blocked
    row['confidence'] = float('nan')
    path = tmp_path / 'invalid.json'
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='confidence'):
        load_drum_transcription(path, AUDIO, REVIEW, CALIBRATION)


def test_user_reported_ending_waveform_attacks_reach_scheduler_xsq_and_preview(tmp_path):
    anchors = json.loads((ROOT / 'tests/fixtures/drummer/dry_ending_signal_anchors.json').read_text())
    output = tmp_path / 'ending.xsq'
    report = inject_drummer_v3(ROOT / 'template.xsq', output, AUDIO, transcription_path=TRANSCRIPT,
                              review_path=REVIEW, calibration_path=CALIBRATION)
    effects = parse_effects(output)
    for anchor in anchors['anchors']:
        # Times are independently measured source rises. The high-tom passage
        # label is the user's listening judgment, not a model-generated fixture.
        matches = [r for r in report['event_audit'] if r['scheduled'] and
                   abs(r['timestamp'] - anchor['timestamp']) * 1000 <= anchor['tolerance_ms']]
        assert matches, f"Source attack lost: {anchor}"
        assert any(r['physical_component'] == 'HX_SNOWMAN_DRUMMER_V3_' + anchor['physical_target'] for r in matches)
        assert 'HX_SNOWMAN_DRUMMER_V3_' + anchor['physical_target'] in _active_targets_for_frame(effects, anchor['timestamp'] * 1000, 60)
    ending = [r for r in report['event_audit'] if r['scheduled'] and 32.35 <= r['timestamp'] <= 33.8]
    assert all(r['type'] == 'tom' and r['tom_class'] == 'high' for r in ending)
    assert all(r['source_onset_index'] is not None for r in ending)
    # There must be separate short strikes with idle gaps, not one sustained
    # tom flash covering the roll or multiple hits invented on every frame.
    toms = [e for e in effects if e[2].endswith('_TOM_HIGH') and 32350 <= e[0] <= 33800]
    assert len(toms) > 1
    assert all(b[0] - a[1] >= 50 for a, b in zip(toms, toms[1:]))


def test_repeated_tom_rest_does_not_change_other_targets_or_isolated_holds():
    from audio.drum_classification import DrumEvent
    from mapping.drum_mapper import map_events_to_drummer_v3_poses
    events = [DrumEvent(t, .8, .8, {'tom_class': identity}, i, 'tom')
              for i, (t, identity) in enumerate(((1., 'high'), (1.156, 'high'), (1.2, 'mid'), (1.468, 'high')))]
    mapped = map_events_to_drummer_v3_poses(events)
    assert [r['timestamp_ms'] for r in mapped] == [1000, 1156, 1200, 1468]
    assert mapped[0]['end_ms'] == 1106
    assert [r['end_ms']-r['timestamp_ms'] for r in mapped[1:]] == [165, 165, 165]
