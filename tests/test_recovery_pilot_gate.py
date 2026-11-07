import json
import pytest
from tools.verify_recovery_pilot_gate import check


def test_successful_download_or_native_export_cannot_unlock_rejected_collection(tmp_path):
    (tmp_path/'run_manifest.json').write_text(json.dumps({'native_preview':{'status':'success'}}))
    with pytest.raises(ValueError,match='do not scale'):check(tmp_path)


def test_unbound_acceptance_receipt_cannot_unlock_collection(tmp_path):
    (tmp_path/'run_manifest.json').write_text(json.dumps({'native_preview':{'status':'success','mp4':str(tmp_path/'old.mp4')}}))
    (tmp_path/'old.mp4').write_bytes(b'rendered candidate')
    (tmp_path/'Phoneme_Test_Hook_Helix.xsq').write_text('<xsequence/>')
    (tmp_path/'xlights_rgbeffects.xml').write_text('<xrgb/>')
    (tmp_path/'pilot_acceptance.json').write_text(json.dumps({'phantom_opening_count':0}))
    with pytest.raises(ValueError,match='stale'):check(tmp_path)


def test_alternate_owner_source_uses_its_own_sequence_and_all_existing_gates(tmp_path):
    from tools.phoneme_source import digest
    for name in ('New_Song_Helix.xsq','xlights_rgbeffects.xml','movie.mp4'):
        (tmp_path/name).write_text(name)
    source='a'*64
    (tmp_path/'run_manifest.json').write_text(json.dumps(dict(
        audio_sha256=source,sequence_file='New_Song_Helix.xsq',
        native_preview=dict(status='success',mp4=str(tmp_path/'movie.mp4'),audio_sha256=source))))
    receipt=dict(audio_sha256=source,xsq_sha256=digest(tmp_path/'New_Song_Helix.xsq'),
        layout_sha256=digest(tmp_path/'xlights_rgbeffects.xml'),native_movie_sha256=digest(tmp_path/'movie.mp4'),
        approved_reference_sha256='b'*64,reference_frame_comparison_passed=True,
        full_recording_vocal_presence_verified=True,phantom_opening_count=0,independent_singer_routes_preserved=True)
    path=tmp_path/'pilot_acceptance.json';path.write_text(json.dumps(receipt))
    assert check(tmp_path)==receipt
    receipt['full_recording_vocal_presence_verified']=False;path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='vocal acceptance failed'):check(tmp_path)


def test_pilot_rejects_a_sequence_outside_its_show_folder(tmp_path):
    (tmp_path/'movie.mp4').write_text('movie')
    (tmp_path/'run_manifest.json').write_text(json.dumps(dict(sequence_file='../other.xsq',
        native_preview=dict(status='success',mp4=str(tmp_path/'movie.mp4')))))
    (tmp_path/'pilot_acceptance.json').write_text('{}')
    with pytest.raises(ValueError,match='local XSQ filename'):check(tmp_path)
