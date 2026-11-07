from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from tools.drummer_v3_visual_masks import load_spec, exact_geometry, strike_transform, MODEL_NAME
from mapping.drum_mapper import map_events_to_drummer_v3_poses, schedule_drum_events, DrumMappingConfig
from audio.drum_classification import DrumEvent
from animation.drummer_motion import build_drummer_motion

ROOT = Path(__file__).resolve().parents[1]
# Independently measured instrument contact coordinates in the unscaled artwork.
CONTACTS = {'SNARE':(261,264), 'TOM_HIGH':(376,240), 'TOM_MID':(206,244),
            'TOM_FLOOR':(177,260), 'CYMBAL_LEFT':(174,204), 'CYMBAL_RIGHT':(433,216)}

@pytest.mark.parametrize('target', CONTACTS)
def test_actual_distal_shaft_tip_reaches_designated_instrument(target):
    source=Image.open(ROOT/'fixtures/band_geometry/source/drummerbg.png').convert('RGBA')
    spec=load_spec(); zone=next(z for z in spec['zones'] if z['id']==target+'_ARM_STICK')
    strike=zone['strike']; transform=np.array(strike_transform(strike,source.size)).reshape(2,3)
    source_tip=np.array(strike['source_tip'])*(np.array(source.size)-1)
    actual_tip=np.linalg.solve(transform[:,:2], source_tip-transform[:,2])
    expected=np.array(CONTACTS[target])
    assert np.linalg.norm(actual_tip-expected) <= 1.0
    exact=exact_geometry(source,spec)
    ys,xs=np.where(np.asarray(exact['actuators'][zone['id']].getchannel('A'))>40)
    assert np.min(np.hypot(xs-expected[0],ys-expected[1])) <= 4.0
    ys,xs=np.where(np.asarray(exact['surfaces'][target+'_SURFACE'])>0)
    assert np.min(np.hypot(xs-expected[0],ys-expected[1])) <= 6.0


def test_unknown_toms_and_bus_are_non_emitting_in_both_animation_paths():
    events=[DrumEvent(i*.2,.8,.8,{},i,k) for i,k in enumerate(['tom','tom','tom','drum_bus'])]
    assert map_events_to_drummer_v3_poses(events)==[]
    assert build_drummer_motion(events)==[]


def test_simultaneous_snare_and_hat_survive_mapping():
    events=[DrumEvent(11,.8,.8,{},0,k) for k in ['snare','hihat']]
    scheduled=schedule_drum_events(events,DrumMappingConfig(intro_gate_enabled=False))
    mapped=map_events_to_drummer_v3_poses(scheduled)
    assert {e['component'] for e in mapped}=={MODEL_NAME+'_SNARE',MODEL_NAME+'_HI_HAT'}
    assert {e['timestamp_ms'] for e in mapped}=={11000}


def test_pedal_brightness_is_secondary_in_preview_and_native():
    import xml.etree.ElementTree as ET
    from tools.integrate_drummer_v3_into_xsq import _add_on
    spec=load_spec();hat=next(t for t in spec['lighting_targets'] if t['id']=='HI_HAT')
    assert .25<=hat['actuator_intensity']<=.4
    values=[]
    for role in ['visual_geometry','visual_pedal']:
        layer=ET.Element('EffectLayer')
        _add_on(layer,0,100,.5,palette_hex='#FFF0C8',source_component=MODEL_NAME+'_HI_HAT',source_type='hihat',source_pose='hi_hat_pulse',role=role)
        values.append(int(layer[0].get('settings').split('E_SLIDER_Brightness=')[1].split(',')[0]))
    assert .25<=values[1]/values[0]<=.4


def test_legacy_entrypoint_and_export_use_one_canonical_detector(monkeypatch):
    import audio.drum_detection as detection
    import audio.drummer_v3 as canonical
    import tools.integrate_drummer_v3_into_xsq as integration
    assert integration._analyze_real_audio is canonical.analyze_drummer_audio
    assert detection.analyze_drummer_samples is canonical.analyze_drummer_samples
    expected=DrumEvent(.1,.8,.9,{},1,'kick')
    monkeypatch.setattr(detection,'analyze_drummer_samples',lambda *a,**kw:([expected],{}))
    assert detection.detect_drum_event_streams(np.ones(10),22050)['kick_events']==[expected]


def test_native_actuator_colors_partition_source_nodes():
    import xml.etree.ElementTree as ET
    from tools.render_drummer_v3_preview import _expand_ranges
    root=ET.parse(ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel').getroot()
    nodes={s.get('name'):s for s in root.findall('./subModels/subModel')}
    for target in CONTACTS:
        name=f'{MODEL_NAME}_{target}_ARM_STICK'
        arm=nodes[name+'_NEUTRAL'];wood=nodes[name+'_WOOD']
        a=_expand_ranges(arm.get('line0'));b=_expand_ranges(wood.get('line0'))
        assert a and b and not a&b
        assert a|b==_expand_ranges(nodes[name].get('line0'))
        assert arm.get('HelixSourceColor') != wood.get('HelixSourceColor')


def test_reinjection_removes_old_generic_arms_and_preserves_unrelated_effects(tmp_path,monkeypatch):
    import xml.etree.ElementTree as ET
    import tools.integrate_drummer_v3_into_xsq as integration
    audio=tmp_path/'stub.wav';audio.touch()
    base=tmp_path/'base.xsq'
    base.write_text('<xsequence><ElementEffects><Element name="HX_SNOWMAN_DRUMMER_V3_LEFT_ARM_STICK"><EffectLayer name="AUTO_Drummer_V3"><Effect source="HelixDrummerV3"/></EffectLayer><EffectLayer name="Manual"><Effect name="On"/></EffectLayer></Element></ElementEffects></xsequence>')
    events=[DrumEvent(11,.8,.8,{},0,'snare'),DrumEvent(11,.8,.8,{},0,'hihat')]
    monkeypatch.setattr(integration,'_analyze_real_audio',lambda p:(events,{}))
    output=tmp_path/'out.xsq';integration.inject_drummer_v3(base,output,audio)
    root=ET.parse(output).getroot()
    old=root.find('./ElementEffects/Element[@name="HX_SNOWMAN_DRUMMER_V3_LEFT_ARM_STICK"]')
    assert old.find('./EffectLayer[@name="AUTO_Drummer_V3"]') is None
    assert old.find('./EffectLayer[@name="Manual"]/Effect') is not None
    names={e.get('name') for e in root.findall('./ElementEffects/Element') if e.find('./EffectLayer[@name="AUTO_Drummer_V3"]/Effect') is not None}
    assert MODEL_NAME+'_SNARE_ARM_STICK_WOOD' in names
    assert MODEL_NAME+'_SNARE_ARM_STICK_NEUTRAL' in names
