from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import ImageFilter
from animation.cymbal_lighting import DECAY_MS, cymbal_level, decay_intervals, peak_level
from tools.render_drummer_v3_preview import TARGETS, compose_lighting, load_component_masks, parse_effects, parse_cymbal_hits
from tools.drummer_v3_visual_masks import target_surface_key
from audio.drum_classification import DrumEvent


def test_cymbal_attack_decay_and_soft_shimmer_never_invent_an_attack():
    hits = [(1000,.8)]
    assert cymbal_level(hits,999)==0
    assert cymbal_level(hits,1000)==peak_level(.8)
    assert cymbal_level(hits,1050)>0
    assert cymbal_level(hits,1050)/cymbal_level(hits,1000)<.86
    assert cymbal_level(hits,2000)<cymbal_level(hits,1400)<cymbal_level(hits,1000)
    assert cymbal_level(hits,1000+DECAY_MS)==0
    assert cymbal_level(hits,7000)==0
    assert cymbal_level([],1000)==0


def test_retrigger_resets_only_its_own_cymbal_and_keeps_fade_slope():
    intervals=decay_intervals([(1000,.8),(1500,.8)])
    assert intervals[0][1]==1500 and intervals[0][3]>0
    assert cymbal_level([(1000,.8),(1500,.8)],1500)==peak_level(.8)
    assert intervals[1][1]==1500+DECAY_MS
    assert cymbal_level([(1000,.8)],1500)<cymbal_level([(1000,.8),(1500,.8)],1500)


def test_surface_rings_after_arm_has_finished_and_body_other_targets_stay_idle():
    source,masks=load_component_masks();target=TARGETS[6]
    idle=np.asarray(compose_lighting(source,masks,[])).astype(int)
    tail=np.asarray(compose_lighting(source,masks,[],cymbal_levels={target:.6})).astype(int)
    surface=np.asarray(masks[target_surface_key(target)])>0
    near=np.asarray(masks[target_surface_key(target)].filter(ImageFilter.MaxFilter(31)))>0
    actuator=(np.asarray(masks[target])>0)&~near
    assert tail[surface,:3].mean()>idle[surface,:3].mean()+20
    assert np.max(np.abs(tail[actuator]-idle[actuator]))<=2
    assert np.max(np.abs(tail[~near]-idle[~near]))<=2
    ended=np.asarray(compose_lighting(source,masks,[],cymbal_levels={target:0})).astype(int)
    assert np.array_equal(idle,ended)


def test_native_fade_and_preview_keep_same_hits_and_short_strikes(tmp_path,monkeypatch):
    import tools.integrate_drummer_v3_into_xsq as integration
    base=tmp_path/'base.xsq';base.write_text('<xsequence><head><sequenceTiming>50 ms</sequenceTiming></head><ElementEffects/></xsequence>')
    audio=tmp_path/'stub.wav';audio.touch()
    events=[DrumEvent(t,.8,.8,{},i,'cymbal') for i,t in enumerate([1.,1.3,1.6])]
    monkeypatch.setattr(integration,'_analyze_real_audio',lambda p:(events,{}))
    out=tmp_path/'out.xsq';r=integration.inject_drummer_v3(base,out,audio)
    assert r['event_count']==3
    assert parse_effects(out)==[(1000,1320,TARGETS[6]),(1300,1620,TARGETS[7]),(1600,1920,TARGETS[6])]
    hits,frame_ms=parse_cymbal_hits(out);assert frame_ms==50
    assert hits[TARGETS[6]]==[(1000,.8),(1600,.8)]
    tree=ET.parse(out).getroot()
    left=tree.findall(f'./ElementEffects/Element[@name="{TARGETS[6]}_SURFACE"]/EffectLayer/Effect')
    assert [(int(e.get('startTime')),int(e.get('endTime'))) for e in left]==[(1000,1600),(1600,3400)]
    settings=dict(s.split('=',1) for s in left[0].get('settings').split(','))
    assert settings['E_CHECKBOX_On_Shimmer']=='1'
    assert 0<int(settings['E_TEXTCTRL_Eff_On_End'])<int(settings['E_TEXTCTRL_Eff_On_Start'])
    assert 'C_CHECKBOX_Palette2=1' in left[0].get('palette')
    assert '#000000' not in left[0].get('palette')
    arms=tree.findall(f'./ElementEffects/Element[@name="{TARGETS[6]}_ARM_STICK_WOOD"]/EffectLayer/Effect')
    assert [(int(e.get('startTime')),int(e.get('endTime'))) for e in arms]==[(1000,1320),(1600,1920)]
