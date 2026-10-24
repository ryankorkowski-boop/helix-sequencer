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
