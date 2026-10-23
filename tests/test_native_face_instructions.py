import xml.etree.ElementTree as ET
import pytest
from core.native_face_instructions import face_template
from core.singing_face_discovery import SingingFace
from xlights.xsq_writer import add_effect


@pytest.mark.parametrize("shape,expected", [("A", "AI"), ("I", "AI"), ("O", "O"), ("MBP", "MBP")])
def test_existing_mapping_writes_actual_faces_with_source_clock(shape, expected):
    face = SingingFace("Backup", "Owner face", "NodeRange", {"Mouth-AI": "1-3", "Mouth-O": "4", "Mouth-MBP": "5"}, "layout")
    cue = {"target_model": "Backup", "mouth_shape": "mouth_" + shape}
    template = face_template(cue, [face], "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1")
    assert template is not None and f"Faces_Phoneme={expected}" in template.settings
    layer = ET.Element("EffectLayer")
    add_effect(layer, 113, 137, "Faces", template)
    effect = layer.find("Effect")
    assert effect.get("name") == "Faces" and effect.get("startTime") == "113" and effect.get("endTime") == "137"
    assert "Faces_FaceDefinition=Owner face" in effect.get("settings", "")


def test_missing_mapping_cannot_become_a_body_strobe_or_invented_phoneme():
    face = SingingFace("Backup", "Owner face", "NodeRange", {"Eyes-Open": "1-3"}, "layout")
    assert face_template({"target_model": "Backup", "mouth_shape": "mouth_A"}, [face], None) is None
    assert face_template({"target_model": "Lead", "mouth_shape": "mouth_A"}, [face], None) is None


def test_unsupported_phoneme_is_reported_unresolved():
    face = SingingFace("Backup", "Owner face", "NodeRange", {"Mouth-O": "4"}, "layout")
    assert face_template({"target_model": "Backup", "mouth_shape": "mouth_FV"}, [face], None) is None


def test_explicit_face_definition_never_falls_back_to_another_mouth():
    lead = SingingFace("Backup", "Lead face", "NodeRange", {"Mouth-AI": "1"}, "layout")
    harmony = SingingFace("Backup", "Harmony face", "NodeRange", {"Mouth-O": "2"}, "layout")
    cue = {"target_model": "Backup", "mouth_shape": "mouth_A", "face_definition": "Harmony face"}
    assert face_template(cue, [lead, harmony], None) is None
    cue["face_definition"] = "Lead face"
    template = face_template(cue, [lead, harmony], None)
    assert template is not None
    assert "FaceDefinition=Lead face," in template.settings
    cue["face_definition"] = "Nonexistent face"
    assert face_template(cue, [lead, harmony], None) is None


def test_generated_style_hint_binds_only_one_real_definition_on_same_singer():
    face = SingingFace('HX_SNOW_HARMONY', 'Helix independent phonemes', 'NodeRange', {'Mouth-AI': '1-3'}, 'layout')
    cue = {'target_model': face.model, 'mouth_shape': 'mouth_A',
           'face_definition': 'helixville4_harmony_singer_full',
           'face_definition_origin': 'generated_style_hint'}
    template = face_template(cue, [face], None)
    assert template is not None
    assert 'FaceDefinition=Helix independent phonemes,' in template.settings
    assert face_template({**cue, 'target_model': 'HX_SNOW_LEAD'}, [face], None) is None
    alternative = SingingFace(face.model, 'Other face', face.type, face.mappings, face.source)
    assert face_template(cue, [face, alternative], None) is None
    assert face_template({**cue, 'face_definition_origin': 'explicit'}, [face], None) is None


def test_native_rest_alias_is_the_actual_xlights_choice():
    face = SingingFace('Lead', 'Source face', 'NodeRange', {'Mouth-rest': '1'}, 'layout')
    template = face_template({'target_model': 'Lead', 'mouth_shape': 'mouth_closed'}, [face], None)
    assert template is not None and 'Faces_Phoneme=rest,' in template.settings


def test_opted_in_mouths_and_containing_groups_exclude_decorative_effects():
    from types import SimpleNamespace as S
    from core.native_face_instructions import exclusive_face_targets
    layout = S(models={
        'Lead': S(raw_attrs={'HelixPhonemeOwnership': 'exclusive'}),
        'Lead/MOUTH_AI': S(parent_name='Lead', is_submodel=True),
        'Lead/BODY': S(parent_name='Lead', is_submodel=True),
        'Other': S(raw_attrs={}),
    }, groups={'All': S(models=['Lead', 'Other']), 'Nested': S(models=['All']),
               'Body only': S(models=['Lead/BODY'])})
    assert exclusive_face_targets(layout) == {'Lead', 'Lead/MOUTH_AI', 'All', 'Nested'}
    assert exclusive_face_targets(None) == set()
