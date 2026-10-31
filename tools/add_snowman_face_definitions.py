"""Add reusable native Faces metadata without changing existing performances.

Every upgraded native show is rerendered and must match every old FSEQ byte.
Existing MP4s then remain exact previews of the upgraded source shows.
"""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import numpy as np

from models.snowman_ensemble import build_ensemble
from models.snowman_face_contract import face_definition,FACE_NAME,VISEME_TO_SHAPE,SHAPE_TO_VISEME
from tools.build_helpers.ultimate_showcase import _write_xml,write_layout
from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.build_snowman_ensemble import NativeSequence
from tools.analyze_snowman_ensemble import sha


def native_faces_probe(root,xlights):
    evidence=[]
    for variant in ('band','faces'):
        g=build_ensemble(variant);folder=root/'native_faces_probe'/variant;write_layout(g,folder)
        seq=NativeSequence(g,2,'','Native Faces definition probe')
        seq.root.find('head/sequenceType').text='Animation'
        palette=ET.SubElement(seq.root.find('ColorPalettes'),'ColorPalette');palette.text='C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1'
        track='Helix xLights Visemes'
        ET.SubElement(seq.root.find('DisplayElements'),'Element',{'type':'timing','name':track,'visible':'1','collapsed':'0'})
        timing=ET.SubElement(seq.root.find('ElementEffects'),'Element',{'type':'timing','name':track,'fixed':'0'})
        for label in ('Wiring probe','Recognized phoneme aliases'):
            layer=ET.SubElement(timing,'EffectLayer');ET.SubElement(layer,'Effect',{'label':label,'startTime':'0','endTime':'2000'})
        phone_layer=ET.SubElement(timing,'EffectLayer')
        for i,(viseme,shape) in enumerate(VISEME_TO_SHAPE.items()):
            ET.SubElement(phone_layer,'Effect',{'label':viseme,'startTime':str(i*200),'endTime':str((i+1)*200)})
        ET.SubElement(seq.root.find('EffectDB'),'Effect').text=f'E_CHOICE_Faces_FaceDefinition={FACE_NAME},E_CHOICE_Faces_TimingTrack={track},E_CHOICE_Faces_Eyes=Off,E_CHECKBOX_Faces_Outline=0,E_CHECKBOX_Faces_SuppressShimmer=1'
        for model in g.models:
            if face_definition(model):
                layer=seq.elements[model.name].find('EffectLayer')
                ET.SubElement(layer,'Effect',{'name':'Faces','ref':'0','palette':'0','startTime':'0','endTime':'2000','id':'1'})
        xsq=folder/'Native_Faces_Probe.xsq';seq.write(xsq)
        with (folder/'render.log').open('w') as log:
            subprocess.run([str(xlights),'--headless','-q','-s',str(folder),'-od',str(folder),str(xsq)],stdout=log,stderr=log,check=True,timeout=120)
        frames,step=read_fseq(xsq.with_suffix('.fseq'))
        for model in g.models:
            if not face_definition(model):continue
            pixels=frames[:,model.start-1:model.start-1+model.channels].reshape(len(frames),-1,3)
            for i,(viseme,shape) in enumerate(VISEME_TO_SHAPE.items()):
                expected=set(model.submodels['MOUTH_'+shape])
                actual=set((np.flatnonzero(pixels[i*4+1].max(axis=1)>0)+1).tolist())
                if actual!=expected:raise ValueError(f'Native Faces mismatch {model.name}/{viseme}: {len(actual)} vs {len(expected)}')
            evidence.append(dict(model=model.name,standard_native_visemes=10,physical_mouth_shapes=7,all_visemes_exact_native_nodes=True,native_three_layer_track_drives_faces=True))
    return evidence


def upgrade(root,xlights):
    evidence=[]
    for p in sorted((root/'shows').glob('*/verification.json')):
        folder=p.parent;report=json.loads(p.read_text());variant=report['variant'];g=build_ensemble(variant)
        if report.get('native_faces_three_layer_track'):
            if any(sha(folder/name)!=digest for name,digest in report['hashes'].items()):raise ValueError('Verified native show changed')
            evidence.append(dict(show=folder.name,already_verified=True));continue
        definitions={m.name:face_definition(m) for m in g.models if face_definition(m)}
        layout=folder/'xlights_rgbeffects.xml';tree=ET.parse(layout)
        for model in tree.findall('./models/model'):
            if model.get('name') not in definitions:continue
            for child in list(model.findall('faceInfo')):model.remove(child)
            ET.SubElement(model,'faceInfo',definitions[model.get('name')])
            xmodel=folder/'models'/(model.get('name')+'.xmodel');xt=ET.parse(xmodel)
            for child in list(xt.getroot().findall('faceInfo')):xt.getroot().remove(child)
            ET.SubElement(xt.getroot(),'faceInfo',definitions[model.get('name')]);_write_xml(xt.getroot(),xmodel)
        _write_xml(tree.getroot(),layout)
        xsq=folder/('Snowman_Band.xsq' if variant=='band' else 'Helix_Singing_Faces.xsq');tree=ET.parse(xsq)
        name='Helix xLights Visemes';root_xml=tree.getroot()
        for element in list(root_xml.findall('./ElementEffects/Element')):
            if element.get('name')==name:root_xml.find('ElementEffects').remove(element)
        if not any(e.get('name')==name for e in root_xml.findall('./DisplayElements/Element')):
            ET.SubElement(root_xml.find('DisplayElements'),'Element',{'type':'timing','name':name,'visible':'1','collapsed':'0'})
        e=ET.SubElement(root_xml.find('ElementEffects'),'Element',{'type':'timing','name':name,'fixed':'0'})
        for track in ('Helix Lyrics','Helix Words','Helix Phonemes'):
            layer=ET.SubElement(e,'EffectLayer')
            for event in root_xml.findall(f'./ElementEffects/Element[@name="{track}"]/EffectLayer/Effect'):
                attrs=dict(event.attrib)
                if track=='Helix Phonemes':attrs['label']=SHAPE_TO_VISEME[attrs['label']]
                ET.SubElement(layer,'Effect',attrs)
        _write_xml(root_xml,xsq)
        before,_=read_fseq(xsq.with_suffix('.fseq'))
        with (folder/'native_face_metadata_render.log').open('w') as log:
            subprocess.run([str(xlights),'--headless','-q','-s',str(folder),'-od',str(folder),str(xsq)],stdout=log,stderr=log,check=True,timeout=300)
        after,_=read_fseq(xsq.with_suffix('.fseq'))
        if not np.array_equal(before,after):raise ValueError('Native metadata upgrade changed the performance')
        report['native_faces_definition_reusable']=True;report['native_faces_metadata_preserves_every_fseq_frame']=True
        report['native_faces_three_layer_track']=True
        for file in (layout,xsq,xsq.with_suffix('.fseq')):report['hashes'][file.name]=sha(file)
        p.write_text(json.dumps(report,indent=2)+'\n');evidence.append(dict(show=folder.name,frames_identical=len(after),face_definitions=len(definitions)))
        print('FACE_METADATA_READY',folder.name,flush=True)
    return evidence


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--xlights',type=Path,required=True);p.add_argument('--probe-only',action='store_true')
    a=p.parse_args();proof=native_faces_probe(a.root.resolve(),a.xlights.resolve())
    if not a.probe_only:proof+=upgrade(a.root.resolve(),a.xlights.resolve())
    (a.root/'native_faces_definitions_verification.json').write_text(json.dumps(proof,indent=2)+'\n')
