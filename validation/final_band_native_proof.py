"""Authored native output diagnostic, explicitly not real-song detection proof."""
from pathlib import Path
from types import SimpleNamespace
import json
import numpy as np

from models.final_band_scene import FinalBandScene
from models.infinite_symphony_showcase import build_megagarden
from models.snowman_ensemble import build_ensemble
from tools.build_snowman_ensemble import NativeSequence
from core.final_band_export import add_final_band_events
from tools.build_helpers.ultimate_showcase import write_layout


def build_fixture(folder):
    folder.mkdir(parents=True,exist_ok=True)
    garden=build_megagarden(); write_layout(garden,folder)
    scene=FinalBandScene();n=48
    curves={}
    for role,count in [('bass',1),('guitar',6)]:
        curves[role+'_routes']=np.full((n,count,3),-1,np.int16)
        curves[role+'_notes']=np.full((n,count),-1,np.int16)
        curves[role+'_note_levels']=np.zeros((n,count))
        curves[role+'_routes'][4:8,0]=[0,0,40 if role=='bass' else 64]
        curves[role+'_notes'][4:8,0]=40 if role=='bass' else 64
        curves[role+'_note_levels'][4:8,0]=.8
    bars=np.zeros((n,len(scene.bars)),np.float32);bars[4:8,60-min(scene.bars)]=.8
    mouths=np.zeros((n,2),np.int8);mouths[4:8,0]=2;mouths[6:10,1]=4
    perf=SimpleNamespace(n=n,scene=scene,curves=curves,voice_lanes=mouths,_bar_levels=bars,
        mallet_schedule=[dict(time=.2,side='left',pitch=60,velocity=.8)])
    source=NativeSequence(build_ensemble(),2.4,'','Authored output diagnostic')
    drummer=source.g.models[0]
    source.effect(drummer,'HX_SNOWMAN_DRUMMER_V3_KICK',200,250,'#FF3300',90,
        provenance=dict(sourceComponent='HX_SNOWMAN_DRUMMER_V3_KICK',sourceRole='visual_geometry'))
    source_path=folder/'Authored_Drum_Source.xsq';source.write(source_path)
    seq=NativeSequence(garden,2.4,'','Authored native final-band connectivity diagnostic')
    seq.root.find('head/sequenceType').text='Animation'
    report=add_final_band_events(seq,perf,source_path)
    path=folder/'Final_Band_Output_Diagnostic.xsq';seq.write(path)
    return garden,path,report


def verify_output(garden,frames,step):
    assert len(frames)==48 and step==50
    checks=[]
    for model in garden.models:
        role=model.details.get('final_band_role')
        if not role:continue
        rgb=frames[:,model.start-1:model.start-1+model.channels].reshape(48,-1,3)
        if role=='xylophone':
            ids=np.array(model.submodels['NOTE_MIDI_60'])-1
            assert rgb[4:8,ids].max()>0
            assert not rgb[:4,ids].any() and not rgb[8:,ids].any()
            arm=np.array(model.submodels['ARM_LEFT_NOTE_60'])-1
            assert rgb[4,arm].max()>0
        if role=='drummer':
            ids=np.array(model.submodels['HX_SNOWMAN_DRUMMER_V3_KICK'])-1
            assert rgb[4,ids].max()>rgb[0,ids].max()
        checks.append(dict(model=model.name,role=role,active_frames=int(np.any(rgb,axis=(1,2)).sum())))
    assert len(checks)==12 and all(c['active_frames']>0 for c in checks)
    return dict(native_performers_verified=12,two_stages_verified=True,
        note_and_contact_output_verified=True,source='authored fixture; not original-song transcription',checks=checks)


def probe(out,executable,render):
    folder=out/'Final_Band_Output_Diagnostic'
    garden,sequence,report=build_fixture(folder)
    frames,step=render(executable,folder,sequence)
    report.update(verify_output(garden,frames,step))
    (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
