from core.band_vocal_face_export import BandVocalFaceExportCompiler, VocalPhonemeTiming
import pytest


def test_existing_default_mouth_contract_is_unchanged():
    compiler = BandVocalFaceExportCompiler()
    effect = compiler.compile_timing(VocalPhonemeTiming("singer", "AH", 1.0, 0.2))
    assert effect.mouth_shape == "wide_open"


def test_lead_and_harmony_can_use_different_face_styles():
    compiler = BandVocalFaceExportCompiler({
        "singer": "singing_tree",
        "female_singer": "snowman_harmony",
    })
    lead = compiler.compile_timing(VocalPhonemeTiming("singer", "AH", 1.0, 0.2))
    harmony = compiler.compile_timing(VocalPhonemeTiming("female_singer", "AH", 1.1, 0.3))
    assert lead.mouth_shape == "TREE_MOUTH_AH"
    assert harmony.mouth_shape == "HX_SNOWMAN_SINGER_FEMALE_MOUTH_AH"
    assert (lead.start, lead.end) == (1.0, 1.2)
    assert (harmony.start, harmony.end) == (1.1, 1.4)


def test_invalid_face_style_fails_before_export():
    with pytest.raises(ValueError):
        BandVocalFaceExportCompiler({"singer": "not_a_style"})
