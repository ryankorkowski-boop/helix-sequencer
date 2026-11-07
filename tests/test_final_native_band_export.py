from pathlib import Path
import xml.etree.ElementTree as ET
from validation.final_band_native_proof import build_fixture


def test_native_final_band_export_has_two_complete_source_timed_bands(tmp_path):
    garden,sequence,report=build_fixture(tmp_path/'show')
    assert len(report['stages'])==2 and all(set(s)=={'drummer','bass','guitar','lead','harmony','piano'} for s in report['stages'].values())
    # Check serialized native identity, not only in-memory names. Imported
    # drummer attrs used to override both stage names at XML serialization.
    models=ET.parse(sequence.parent/'xlights_rgbeffects.xml').getroot().findall('models/model')
    assert [m.get('name') for m in models]==[m.name for m in garden.models]
    assert len({m.get('name') for m in models})==len(models)
    assert [int(m.get('StartChannel')) for m in models]==[m.start for m in garden.models]
    for model in garden.models:
        if model.details.get('final_band_role')!='piano':
            continue
        notes=set().union(*(set(v) for k,v in model.submodels.items() if k.startswith('NOTE_MIDI_')))
        for part,nodes in model.submodels.items():
            if not part.startswith('NOTE_MIDI_'):
                assert notes.isdisjoint(nodes),part
    root=ET.parse(sequence).getroot()
    for prefix in ('HX_BETA_STAGE_A','HX_BETA_STAGE_B'):
        parent=root.find(f"ElementEffects/Element[@name='{prefix}_PIANO']")
        note=parent.find("SubModelEffectLayer[@name='NOTE_MIDI_60']/Effect")
        assert note.get('startTime')=='200' and note.get('endTime')=='400'
        assert parent.find("SubModelEffectLayer[@name='ARM_LEFT_NOTE_60']") is None
        drummer=root.find(f"ElementEffects/Element[@name='{prefix}_DRUMMER']")
        kick=drummer.find("SubModelEffectLayer[@name='HX_SNOWMAN_DRUMMER_V3_KICK']/Effect")
        assert kick.get('startTime')=='200' and kick.get('sourceRole')=='visual_geometry'
