"""Review copies of the owner's 256 AC addresses, with one real circuit per prop.

The original XML is read-only. Virtual bulbs describe geometry, not additional
controller addresses. RGB additions begin after the original address range.
"""
from pathlib import Path
import argparse
import json
import math
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
import soundfile as sf
from core.model_parser import parse_layout
from models.ultimate_showcase import Garden
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_snowman_ensemble import NativeSequence
from tools.phoneme_source import digest
from tools.source_spatial_direction import export_model


def geometry(source, *, include_rgb=False):
    source=Path(source)
    parsed=parse_layout(source)
    original=[m for m in parsed.models.values() if not m.is_submodel]
    if len(original)!=256 or {m.start_channel for m in original}!=set(range(1,257)):
        raise ValueError('Expected the original 256 distinct AC circuit addresses')
    g=Garden(title='Original 256 AC'+(' + RGB' if include_rgb else ''),slug='Original_256_AC')
    original_points={m.name:np.array([(p.x,p.y,p.z) for p in m.virtual_pixel_map()]) for m in original}
    bounds=np.concatenate(list(original_points.values()));origin=np.array([(bounds[:,0].min()+bounds[:,0].max())/2,bounds[:,1].min(),0])
    for old in original:
        points=original_points[old.name]
        match=re.fullmatch(r'Line Tree (Red|Green|White) (\d+)',old.name)
        if match:
            group=[m for m in original if re.fullmatch(r'Line Tree (Red|Green|White) '+match[2],m.name)]
            center=np.mean([[float(m.raw_attrs.get('WorldPosX',0))+float(m.raw_attrs.get('X2',0))/2,
                             float(m.raw_attrs.get('WorldPosZ',0))] for m in group],axis=0)
            base=np.mean([float(m.raw_attrs.get('WorldPosY',0))+float(m.raw_attrs.get('Y2',0)) for m in group])
            height=max(abs(float(m.raw_attrs.get('Y2',0))) for m in group)
            if height<=0:raise ValueError('Spiral tree source has no height')
            t=np.linspace(0,1,max(25,len(points)));phase=('Red','Green','White').index(match[1])*math.tau/3
            angle=t*math.tau*4+phase;radius=height*.20*(1-t)
            points=np.c_[center[0]+radius*np.cos(angle),base+height*t,center[1]+radius*np.sin(angle)]
        points=(points-origin)/10
        # Closed outlines repeat their first bulb, and legacy single-circuit
        # props can contain coincident virtual bulbs. One native cell per
        # occupied position retains the outline and the same AC address.
        _,unique=np.unique(np.round(points,5),axis=0,return_index=True)
        points=points[np.sort(unique)]
        color={'red':'#FF4040','green':'#40FF60','white':'#FFFFFF'}.get(old.color_family,'#FFF1CF')
        kind={'red':'Single Color Red','green':'Single Color Green'}.get(old.color_family,'Single Color White')
        m=g.custom(old.name,points,'SOURCE_AC','Source-address AC preview',[color]*len(points),{'ALL':[1]})
        cells=m.attrs['CustomModelCompressed'].split(';')
        m.attrs['CustomModelCompressed']=';'.join('1,'+c.split(',',1)[1] for c in cells)
        m.kind='ac';m.start=old.start_channel
        name=old.name.lower()
        role=('drummer' if 'arch' in name else 'keyboardist' if any(s in name for s in ('tree','icicle','star'))
              else 'guitarist' if any(s in name for s in ('roof','gutter','window')) else 'bassist')
        m.details.update(circuit_count=1,musical_role=role,source_display_floor=.6,
            original_start_channel=old.start_channel,original_string_type=old.string_type,
            original_model_name=old.name,source_geometry='Helix existing virtual geometry; original XML unchanged')
        if role=='drummer':m.details['percussion_component']=('kick','snare','hihat','cymbal')[(old.start_channel-1)%4]
        m.attrs.update(StringType=kind,PixelSize='10')
    if include_rgb:
        from models.approval_layouts import build_layout
        rgb=build_layout(4);start=257
        for model in rgb.models:
            model.name='EXPERIMENTAL_RGB_'+model.name
            model.start=start;start+=model.channels
            model.attrs.pop('StartChannel',None);model.attrs['PixelSize']='10'
            g.models.append(model)
    return g


def build(source, production, fixture, output, *, include_rgb=False):
    source,production,fixture,output=map(Path,(source,production,fixture,output))
    if output.exists():raise FileExistsError(output)
    before=digest(source);g=geometry(source,include_rgb=include_rgb)
    manifest=json.loads((production/'run_manifest.json').read_text())
    audio=next((production/'media').glob('*.wav'))
    if digest(audio)!=manifest['audio_sha256']:raise ValueError('Source audio identity mismatch')
    receipt=json.loads((fixture/'diagnostic.json').read_text())
    if receipt['audio_sha256']!=digest(audio) or receipt['clock_sha256']!=digest(fixture/'acoustic_vocal_clocks.npz'):
        raise ValueError('Source vocal cache mismatch')
    plan=json.loads(next((production/'sequence').glob('*.snowman_band.json')).read_text())
    write_layout(g,output,include_demo=False,export_all_custom=True)
    (output/'media').mkdir();shutil.copyfile(audio,output/'media'/audio.name)
    duration=sf.info(audio).duration;seq=NativeSequence(g,duration,'media/'+audio.name,g.title)
    with np.load(fixture/'acoustic_vocal_clocks.npz',allow_pickle=False) as cache:
        reports=[export_model(seq,m,plan,cache,g.palette) for m in g.models]
    sequence=output/'Performance.xsq';seq.write(sequence)
    tree=ET.parse(output/'xlights_rgbeffects.xml');points=np.concatenate([m.points for m in g.models])
    low,high=points.min(0),points.max(0);center=(low+high)/2;span=high-low
    for camera in tree.findall('Viewpoints/*'):
        for key,value in dict(angleX=5,angleY=0,distance=-max(span[0]*.85,span[1]*1.7,55),
                              panx=-center[0],pany=-center[1],panz=-center[2]).items():camera.set(key,str(value))
    tree.write(output/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
    (output/'Spatial_Event_Provenance.json').write_text(json.dumps(reports,indent=2)+'\n')
    assert digest(source)==before
    report=dict(schema='helix.source-ac-review.v1',source_layout_sha256=before,original_addresses=list(range(1,257)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        audio_sha256=digest(audio),source_duration_seconds=duration,sequence_file=sequence.name,warnings=[],
        fixed_ac_channels=256,total_channels=max(m.start+m.channels-1 for m in g.models),
        original_source_unchanged=True,virtual_geometry_not_surveyed=True,owner_visual_approval=False)
    (output/'run_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','production','fixture','output'):p.add_argument(name,type=Path)
    p.add_argument('--include-rgb',action='store_true');a=p.parse_args()
    print(json.dumps(build(a.source,a.production,a.fixture,a.output,include_rgb=a.include_rgb),indent=2))
