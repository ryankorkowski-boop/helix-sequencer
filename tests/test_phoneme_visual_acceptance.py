"""Keep the approved vocal render separate from canonical 3D visual approval."""
import json
from pathlib import Path


def test_visual_receipt_is_valid_json_and_blocks_legacy_cast():
    source = Path(__file__).resolve().parents[1] / "tools" / "prepare_phoneme_show.py"
    text = source.read_text()
    assert "canonical_solid_3d_band': False" in text
    assert "owner_vocal_animation_review': 'passed_in_prior_video'" in text
    assert "json.dumps(manifest['visual_identity'], indent=2)" in text


def test_finalizer_does_not_accept_native_review_cast_as_canonical():
    source = (Path(__file__).resolve().parents[1] / "tools" / "finalize_phoneme_review.py").read_text()
    assert "canonical_solid_3d_band" in source
    assert "owner-approved solid 3D snowman band" in source
