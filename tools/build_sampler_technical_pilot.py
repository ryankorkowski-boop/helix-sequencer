"""Build targeted technical native pilots on the authenticated prior sampler.

This is separate from full-original Phoneme validation. Missing isolated sampler
vocals abstain; the 34.88-second vocal cache must never be stretched/reused here.
"""
import argparse
import json
from pathlib import Path
import shutil
from models.approval_layouts import build_layout,NAMES
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_snowman_ensemble import NativeSequence
from tools.source_spatial_direction import export_model
from tools.phoneme_source import digest

MP3_SHA256='ffeaba9b9f8fc253a0356505c2b4147b7576b772db42a1c8ea63094b42545acf'
WAV_SHA256='c69e0a4632a6c67f7ae59d2e1c630ce6de5969ca954d403f094176a1376c6524'


def build(audio,analysis,provenance,output):
    audio,analysis,provenance,output=map(Path,(audio,analysis,provenance,output))
    if digest(audio)!=MP3_SHA256:raise ValueError('Authenticated prior sampler MP3 hash mismatch; substitution refused')
    authority=json.loads(provenance.read_text())
    if authority['audio_sha256']!=WAV_SHA256 or authority['duration_seconds']!=256 or len(authority['clips'])!=16:
        raise ValueError('Prior sampler source-clip provenance mismatch')
    retained=analysis/'Helix_Starred_All_Songs.mp3'
    if digest(retained)!=MP3_SHA256:raise ValueError('Analysis does not retain the authenticated sampler')
    plans=list(analysis.glob('*.snowman_band.json'))
    if len(plans)!=1:raise ValueError('Require one shared sampler production analysis')
    plan=json.loads(plans[0].read_text());manifest=[]
    for number in (9,10,11):
        name=NAMES[number-1];folder=output/f'{number:02}_{name}'
        if folder.exists():raise FileExistsError(folder)
        g=build_layout(number);sequence=NativeSequence(g,256,'media/Helix_Starred_All_Songs.mp3',g.title)
        reports=[]
        for model in g.models:
            if model.name=='HX_CENTER_KEYBOARD_HELIX':
                for cue in plan['cues'].get('keyboardist',[]):
                    pitch=cue.get('pitch_midi');part=f'KEY_MIDI_{round(pitch):03d}'
                    if part in model.submodels:
                        sequence.effect(model,part,cue['start_ms'],cue['end_ms'],g.palette[2],85,15,
                            provenance={'sourceRole':'keyboardist','sourcePitchMIDI':str(pitch),'sourceMethod':'authenticated_sampler_production_plan'})
            reports.append(export_model(sequence,model,plan,{},g.palette))
        write_layout(g,folder,include_demo=False,export_all_custom=True)
        (folder/'media').mkdir();shutil.copyfile(audio,folder/'media/Helix_Starred_All_Songs.mp3')
        sequence.write(folder/(name+'.xsq'))
        # Use the inspected technical camera, not the default garden camera.
        import numpy as np
        import xml.etree.ElementTree as ET
        points=np.concatenate([m.points for m in g.models]);center=(points.min(0)+points.max(0))/2;span=np.ptp(points,axis=0)
        camera=ET.parse(folder/'xlights_rgbeffects.xml')
        for view in camera.findall('./Viewpoints/*'):
            for key,value in dict(angleX=8 if number==9 else 18,angleY=0 if number==9 else 12,
                distance=-max(span[0]*.95,span[1]*2,55),panx=-center[0],pany=-center[1],panz=-center[2]).items():view.set(key,str(value))
        camera.write(folder/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
        report=dict(schema='helix.authenticated-sampler-technical-pilot.v1',number=number,name=name,
            source_audio_sha256=MP3_SHA256,source_analysis_sha256=digest(plans[0]),
            source_provenance_sha256=digest(provenance),source_duration_seconds=256,
            waveform='authenticated retained Starred sampler; same prior timeline; no alternate montage',
            vocals='No independently isolated sampler singers; vocal-driven spatial roles abstain',
            source_estimates_not_ground_truth=True,public_beta_ready=False,owner_approval=False,
            folder=str(folder.resolve()),xsq=name+'.xsq')
        (folder/'run_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        (folder/'Spatial_Event_Provenance.json').write_text(json.dumps(reports,indent=2)+'\n')
        manifest.append(report)
    (output/'Sampler_Pilot_Manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('audio','analysis','provenance','output'):p.add_argument(name,type=Path)
    a=p.parse_args();build(a.audio,a.analysis,a.provenance,a.output)
