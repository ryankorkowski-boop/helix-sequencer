from pathlib import Path
import xml.etree.ElementTree as ET
from validation.final_band_native_proof import build_fixture


def test_native_final_band_export_has_two_complete_source_timed_bands(tmp_path):
    garden,sequence,report=build_fixture(tmp_path/'show')
    assert len(report['stages'])==2 and all(set(s)=={'drummer','bass','guitar','lead','harmony','xylophone'} for s in report['stages'].values())
    root=ET.parse(sequence).getroot()
    for prefix in ('HX_BETA_STAGE_A','HX_BETA_STAGE_B'):
        parent=root.find(f"ElementEffects/Element[@name='{prefix}_XYLOPHONE']")
        note=parent.find("SubModelEffectLayer[@name='NOTE_MIDI_60']/Effect")
        assert note.get('startTime')=='200' and note.get('endTime')=='400'
        contact=parent.find("SubModelEffectLayer[@name='ARM_LEFT_NOTE_60']/Effect")
        assert contact.get('startTime')=='200' and contact.get('endTime')=='250'
        drummer=root.find(f"ElementEffects/Element[@name='{prefix}_DRUMMER']")
        kick=drummer.find("SubModelEffectLayer[@name='HX_SNOWMAN_DRUMMER_V3_KICK']/Effect")
        assert kick.get('startTime')=='200' and kick.get('sourceRole')=='visual_geometry'
