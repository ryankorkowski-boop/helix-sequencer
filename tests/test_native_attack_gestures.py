from types import SimpleNamespace
import xml.etree.ElementTree as ET
from tools.canonical_band_cues import export_instruments


def scene():
    model = SimpleNamespace(name='HX_SNOW_PIANO', details={'review_role':'piano'},
        submodels={'NOTE_MIDI_48':[1], 'NOTE_MIDI_84':[2],
                   'ARM_LEFT_ACTIVE':[3], 'ARM_RIGHT_ACTIVE':[4],
                   'ARM_LEFT_IDLE':[5], 'ARM_RIGHT_IDLE':[6]})
    root = ET.fromstring('<xsequence><head><sequenceDuration>2</sequenceDuration></head><DisplayElements/><ElementEffects/></xsequence>')
    return model, root


def effects(root, part):
    row=root.find(f'./ElementEffects/Element[@name="HX_SNOW_PIANO/{part}"]')
    return [] if row is None else row.findall('./EffectLayer/Effect')


def test_sustained_note_keeps_light_but_releases_source_attack_hand():
    model,root=scene()
    export_instruments(root,SimpleNamespace(models=[model]),{'cues':{'keyboardist':[
        dict(start_ms=100,end_ms=1500,pitch_midi=48)]}})
    key=effects(root,'NOTE_MIDI_48')[0];hand=effects(root,'ARM_LEFT_ACTIVE')[0]
    assert (key.get('startTime'),key.get('endTime'))==('100','1500')
    assert (hand.get('startTime'),hand.get('endTime'))==('100','190')
    assert hand.get('sourceEndMs')=='1500' and hand.get('sourceGesture')=='attack_contact'
    idle=effects(root,'ARM_LEFT_IDLE')
    assert [(e.get('startTime'),e.get('endTime')) for e in idle]==[('0','100'),('190','2000')]
    assert all('E_TEXTCTRL_Eff_On_Start=65,E_TEXTCTRL_Eff_On_End=65' in e.get('settings') for e in idle)


def test_chord_uses_both_regions_without_duplicating_same_hand_gestures():
    model,root=scene()
    report=export_instruments(root,SimpleNamespace(models=[model]),{'cues':{'keyboardist':[
        dict(start_ms=100,end_ms=500,pitch_midi=p) for p in (48,48,84)]}})
    assert len(effects(root,'ARM_LEFT_ACTIVE'))==len(effects(root,'ARM_RIGHT_ACTIVE'))==1
    assert report['models'][model.name]['arm_gestures']==2


def test_short_source_and_real_gaps_never_acquire_extra_contact_time():
    model,root=scene()
    export_instruments(root,SimpleNamespace(models=[model]),{'cues':{'keyboardist':[
        dict(start_ms=100,end_ms=140,pitch_midi=48),dict(start_ms=350,end_ms=700,pitch_midi=48)]}})
    assert [(e.get('startTime'),e.get('endTime')) for e in effects(root,'ARM_LEFT_ACTIVE')]==[('100','140'),('350','440')]
    assert any(e.get('startTime')=='140' and e.get('endTime')=='350' for e in effects(root,'ARM_LEFT_IDLE'))


def test_literal_key_contact_owns_only_its_attack_and_one_hand_per_onset():
    model,root=scene();model.details['native_keyboard_contacts']=True
    model.submodels.update(ARM_LEFT_NOTE_48=[7], ARM_RIGHT_NOTE_84=[8])
    report=export_instruments(root,SimpleNamespace(models=[model]),{'cues':{'keyboardist':[
        dict(start_ms=100,end_ms=1500,pitch_midi=p) for p in (48,48,84)]}})
    assert len(effects(root,'ARM_LEFT_NOTE_48'))==len(effects(root,'ARM_RIGHT_NOTE_84'))==1
    assert not effects(root,'ARM_LEFT_ACTIVE') and not effects(root,'ARM_RIGHT_ACTIVE')
    assert effects(root,'ARM_LEFT_IDLE')[-1].get('startTime')=='190'
    assert report['models'][model.name]['arm_gestures']==2


def test_unreachable_authored_key_still_lights_without_fabricated_contact():
    model,root=scene();model.details['native_keyboard_contacts']=True
    report=export_instruments(root,SimpleNamespace(models=[model]),{'cues':{'keyboardist':[
        dict(start_ms=100,end_ms=1500,pitch_midi=48)]}})
    assert effects(root,'NOTE_MIDI_48')[0].get('endTime')=='1500'
    assert report['models'][model.name]['mapped_events']==1
    assert report['models'][model.name]['arm_gestures']==0
    assert len(report['models'][model.name]['arm_contact_omissions'])==1


def test_fast_adjacent_attacks_never_show_two_simultaneous_hands_on_one_side():
    model,root=scene();model.details['native_keyboard_contacts']=True
    model.submodels.update(NOTE_MIDI_55=[9],ARM_LEFT_NOTE_48=[7],ARM_LEFT_NOTE_55=[8])
    export_instruments(root,SimpleNamespace(models=[model]),{'cues':{'keyboardist':[
        dict(start_ms=130,end_ms=600,pitch_midi=55),
        dict(start_ms=100,end_ms=500,pitch_midi=48)]}})
    assert effects(root,'ARM_LEFT_NOTE_48')[0].get('endTime')=='130'
    assert effects(root,'ARM_LEFT_NOTE_55')[0].get('startTime')=='130'
    assert effects(root,'NOTE_MIDI_48')[0].get('endTime')=='500'
