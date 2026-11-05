"""Build the owner's ordered twelve supported views from one real music plan.

All lighting geometry reuses existing Helix native model generators. The solid
band view and its native pixel companion share the source-front V3 volume rig.
"""
from pathlib import Path
import argparse
import json
import shutil
import xml.etree.ElementTree as ET
import math
from types import SimpleNamespace

import numpy as np

from models.approval_layouts import build_layout,house,tree,arch,structures,allocate
from models.ultimate_showcase import Garden
from tools.build_snowman_ensemble import NativeSequence
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_source_ac_review import geometry as original_ac
from tools.source_spatial_direction import export_model
from tools.phoneme_source import digest
from models.band_sampler_logic import SHAPE_NAMES

NAMES=("Greg's legacy 256-channel AC",'Canonical 3D snowman band',
       'Simple RGB house','RGB arches and roofline','RGB mega trees and spirals',
       'RGB house with singing faces','Pixel rock-band stage',
       'Double helix with keyboard rungs','Advanced RGB house and matrices',
       'Multi-house neighborhood','Advanced 3D spatial showcase','Ultimate Helix showcase',
       '3D pixel grid - 12 inch spacing','3D spiral grove','Moire optical depth','Triple helix cathedral')


def pixel_grid_3d():
    """48 by 48 feet, 48 inches high; actual 12-inch XYZ pixel spacing."""
    g=Garden(title=NAMES[12],slug='13_Pixel_Grid_3D')
    axis=np.arange(-24,25,dtype=float)
    x,z=np.meshgrid(axis,axis,indexing='ij')
    for y,role in enumerate(('keyboardist','guitarist','bassist','drummer','keyboardist')):
        points=np.c_[x.ravel(),np.full(x.size,y),z.ravel()]
        subs={f'ROW_{i:02}':(np.flatnonzero(points[:,2]==value)+1).tolist() for i,value in enumerate(axis)}
        m=g.custom(f'GRID_Y_{y:02}',points,'GRID_3D','One horizontal wiring plane',
                   [g.palette[y%3]]*len(points),subs,
                   details=dict(musical_role=role,physical_units='feet',pixel_spacing_inches=12,
                                height_inches=48,wiring='horizontal plane, X runs with alternating return',
                                spatial_direction=1 if y%2==0 else -1))
        m.attrs['PixelSize']='9'
    return g


def residential_preview(folder,number):
    """Use the existing zero-channel facade and readable, restrained bulbs."""
    if number not in (3,4,6,9,10):return
    from tools.native_residential_context import add_context
    import copy
    folder=Path(folder);add_context(folder)
    path=folder/'xlights_rgbeffects.xml';tree=ET.parse(path)
    for model in tree.findall('./models/model'):
        name=model.get('name','')
        size=5 if 'FACE' in name else 12 if any(k in name for k in ('ROOF','EAVE','RIDGE')) else 8
        model.set('PixelSize',str(size))
    if number==10:
        objects=tree.find('view_objects');base=objects.find('view_object')
        base.set('ScaleX','.85');base.set('ScaleY','.85');base.set('ScaleZ','.85');base.set('WorldPosZ','24.9')
        for index,x in enumerate((-55,55)):
            item=copy.deepcopy(base);item.set('name',f'Residential ambient context {index}');item.set('WorldPosX',str(x));item.set('WorldPosZ','-25.1');objects.append(item)
    tree.write(path,encoding='utf-8',xml_declaration=True)


def native_band(g,plan,*,rock=True,duration=36):
    from models.final_band_native import add_final_native_band,SurfaceParts
    from models.final_band_scene import FinalBandScene
    from models.source_drummer_3d import SourceDrummer3D
    from tools.render_owner_band_review import drum_hits
    from tools.native_source_pose_band import select_states
    add_final_native_band(g,'HX_SNOW',(0,0,0),rock=rock,include_stage=True,
                          full_keyboard=True,surface_spacing=.18,mouth_scale=.42)
    for model in g.models:
        if model.details.get('final_band_role'):
            model.details['review_role']=model.details['final_band_role']
    scene=FinalBandScene('ember_amphitheatre',rock=rock,full_keyboard=True)
    hits,_=drum_hits(plan['cues']['drummer']);rig=SourceDrummer3D(scene,hits)
    parts=SurfaceParts((0,0,0),scale=5)
    for item in rig.meshes:
        name=item['name'];part=name+'_SURFACE' if name.startswith('HX_SNOWMAN_') else 'BASE_DIM'
        # A bounded source-material palette retains front colors without
        # creating one native effect lane for every antialiased image value.
        color=np.clip(np.rint(item['mesh'].visual.vertex_colors[:,:3]/32)*32,0,255).astype('u1')
        colors=['#'+''.join(f'{int(c):02X}' for c in row) for row in color]
        parts.add(part,item['mesh'].vertices[::2],colors[::2])
    for i in rig.connector_ids:parts.primitive('BASE_DIM',scene.instances[i])
    ids=[i for values in rig.rigs.values() for i in values]+[rig.foot,rig.pedal,rig.beater]
    samples=[]
    for frame in range(math.ceil(duration*20)):
        rig.pose(frame/20)
        samples.append(np.array([scene.instances[i]['matrix'][:3,3] for i in ids]))
    selected,states,error=select_states(samples,limit=24)
    for number,frame in enumerate(selected):
        rig.pose(int(frame)/20)
        for i in ids:parts.primitive(f'SOURCE_POSE_{number:02}',scene.instances[i])
    old=next(m for m in g.models if m.details.get('review_role')=='drummer')
    g.models.remove(old)
    model=g.custom('HX_SNOW_DRUMMER',parts.points,'BAND','Source-front closed dimensional V3',
        parts.colors,{k:sorted(set(v)) for k,v in parts.parts.items()},
        details=dict(review_role='drummer',final_band_role='drummer',source_front_volume=True,
                     source_pose_error=error,pose_method='source-clock selected real 3D poses'))
    for m in g.models:
        m.attrs.pop('StartChannel',None)
        m.attrs.update(PixelSize='7',Antialias='1',BlackTransparency='100')
    return model,states,rig.proof()


def layout(number,plan,*,duration=36):
    if number==1:
        g=original_ac(Path(__file__).resolve().parents[1]/'xlights_rgbeffects.xml')
        for m in g.models:m.attrs['PixelSize']='28'
        return g,None
    if number==2:
        g=Garden(title=NAMES[1],slug='02_Canonical_3D')
        # A native companion is retained even though the comparison uses
        # Helix's continuous solid-mesh performance for the canonical view.
        band,state,proof=native_band(g,plan,rock=False,duration=duration);return g,(band,state,proof)
    if number==3:g=build_layout(4)
    elif number==4:
        g=build_layout(4);g.models=[m for m in g.models if m.zone=='ARCHES' or any(k in m.name for k in ('EAVE','ROOF','RIDGE'))]
    elif number==5:
        g=Garden(title=NAMES[4],slug='05_Trees_Spirals')
        for x in (-32,0,32):tree(g,x,-10,32,9)
        for x in (-16,16):structures(g).tree(x,12,22,7,color=int(x>0))
        for x in (-32,0,32):structures(g).starburst((x,35,-10),4)
    elif number==6:g=build_layout(5)
    elif number==7:
        g=Garden(title=NAMES[6],slug='07_Pixel_Rock_Band');band,state,proof=native_band(g,plan,duration=duration)
        return g,(band,state,proof)
    elif number==8:g=build_layout(9)
    elif number==9:
        g=build_layout(6)
        for x in (-58,58):structures(g).tree(x,-12,32,8,color=int(x>0))
    elif number==10:
        g=Garden(title=NAMES[9],slug='10_Neighborhood')
        for index,x in enumerate((-55,0,55)):
            row_z=15 if index==1 else -35
            first=len(g.models)
            house(g,x,z=row_z,scale=.85,prefix=f'HOME_{index+1}')
            for dx in (-20,0,20):arch(g,x+dx,row_z+30,10,7)
            tree(g,x-35,row_z,24,6);structures(g).tree(x+35,row_z+10,22,6,color=index%3)
            structures(g).mesh(f'NEIGHBORHOOD_MATRIX_{index}',(x,7,row_z+1),18,12,'MATRICES',index%3)
            for model in g.models[first:]:model.details['propagation_delay_ms']=index*40
    elif number==11:g=build_layout(11)
    elif number==12:
        g=build_layout(12);g.models=[m for m in g.models if not m.details.get('review_role')]
    elif number==13:g=pixel_grid_3d()
    elif number==14:
        g=Garden(title=NAMES[13],slug='14_Spiral_Grove')
        for row,z in enumerate((-24,0,24)):
            for col,x in enumerate((-30,0,30)):
                m=structures(g).tree(x,z,26+8*(row%2),7,color=(row+col)%3)
                m.details.update(musical_role=('guitarist','keyboardist','bassist')[(row+col)%3],
                                 spatial_direction=1 if col%2==0 else -1)
    elif number==15:g=build_layout(10)
    elif number==16:
        g=Garden(title=NAMES[15],slug='16_Triple_Helix')
        for i,x in enumerate((-32,0,32)):
            g.dna(f'KEYBOARD_HELIX_{i}',x,-10,58 if i==1 else 44,8,8.8,880,'DNA')
            from models.approval_layouts import pitch_rungs
            pitch_rungs(g.models[-1])
        for z in (-28,-8,12):structures(g).arch((0,0,z),100,68,pointed=True,zone='CATHEDRAL')
    else:raise ValueError('Unknown comparison layout')
    for model in g.models:
        model.attrs.pop('StartChannel',None)
        model.details.setdefault('source_display_floor',.50)
        model.attrs.setdefault('PixelSize','18')
    arches=[m for m in g.models if m.zone=='ARCHES']
    for index,model in enumerate(sorted(arches,key=lambda m:float(np.mean(m.points[:,0])))):
        model.details['percussion_component']=('kick','snare','hihat','cymbal')[index%4]
    return allocate(g),None


def build(source,vocals,output,*,numbers=None):
    source,vocals,output=map(Path,(source,vocals,output));output.mkdir(parents=True,exist_ok=True)
    source_manifest=json.loads((source/'run_manifest.json').read_text())
    audio=source/'media'/source_manifest.get('audio_name','Helix_Starred_New_Review.wav');sha=digest(audio)
    import soundfile as sf
    duration=sf.info(audio).duration;duration_ms=round(duration*1000)
    receipt=json.loads((vocals/'diagnostic.json').read_text())
    if receipt['audio_sha256']!=sha or receipt['clock_sha256']!=digest(vocals/'acoustic_vocal_clocks.npz'):
        raise ValueError('Foreign vocal analysis')
    plan_path,=(source/'sequence').glob('*.snowman_band.json');plan=json.loads(plan_path.read_text())
    with np.load(vocals/'acoustic_vocal_clocks.npz') as z:cache={k:z[k].copy() for k in z.files}
    numbers=tuple(range(1,17)) if numbers is None else tuple(numbers)
    if not numbers or len(set(numbers))!=len(numbers) or any(type(n) is not int or not 1<=n<=16 for n in numbers):
        raise ValueError('Choose unique layout numbers in1..16')
    manifest=json.loads((output/'Layout_Manifest.json').read_text()) if (output/'Layout_Manifest.json').exists() else []
    if any(item['source_audio_sha256']!=sha for item in manifest):raise ValueError('Foreign retained layout source')
    manifest=[item for item in manifest if item['number'] not in numbers]
    for number in numbers:
        name=NAMES[number-1]
        folder=output/f'{number:02}'
        if folder.exists():raise FileExistsError(folder)
        g,band=layout(number,plan,duration=duration);g.title=name
        if number!=1:allocate(g)
        for m in g.models:
            if not m.submodels:m.submodels['ALL']=list(range(1,len(m.points)+1))
        sequence=NativeSequence(g,duration,'media/'+audio.name,name);reports=[]
        for m in g.models:
            if m.details.get('review_role'):continue
            if m.details.get('generic_singer'):
                lane=m.details['generic_singer'];values=np.where(cache[lane+'_energy']>0,cache[lane+'_shapes'],0)
                cuts=np.r_[0,np.flatnonzero(np.diff(values))+1,len(values)]
                for a,b in zip(cuts[:-1],cuts[1:]):
                    part='MOUTH_'+SHAPE_NAMES[int(values[a])]
                    if m.submodels.get(part):sequence.effect(m,part,int(a)*10,int(b)*10,g.palette[2],95)
                for part in ('OUTLINE','BASE','BODY','EYES'):
                    if m.submodels.get(part):sequence.effect(m,part,0,duration_ms,g.palette[0],40)
                continue
            if m.details.get('keyboard_pitch_rungs'):
                for role,part,color in [('guitarist','STRAND_A',g.palette[0]),('bassist','STRAND_B',g.palette[1])]:
                    for cue in plan['cues'][role]:sequence.effect(m,part,cue['start_ms'],cue['end_ms'],color,95,20)
                for cue in plan['cues']['keyboardist']:
                    part=f"KEY_MIDI_{round(cue['pitch_midi']):03}"
                    if m.submodels.get(part):sequence.effect(m,part,cue['start_ms'],cue['end_ms'],g.palette[2],100,20)
                continue
            reports.append(export_model(sequence,m,plan,cache,g.palette))
        if band:
            from tools.phoneme_vocal_export import static_materials,export as export_vocals
            from tools.canonical_band_cues import export_instruments
            from models.canonical_native_band import VISEMES
            from tools.build_helpers.ultimate_showcase import model_xml
            performers=[m for m in g.models if m.details.get('review_role')]
            for m in performers:
                if m.details['review_role'] in ('lead','harmony'):
                    original=dict(m.submodels)
                    for viseme,shape in VISEMES.items():m.submodels['MOUTH_'+viseme]=list(original['MOUTH_'+shape])
                    m.children.append(('faceInfo',dict(Name='Helix independent phonemes',Type='NodeRange',
                        **{'Mouth-'+v:','.join(map(str,m.submodels['MOUTH_'+v])) for v in VISEMES},
                        **{'Eyes-Open':'','Eyes-Closed':'','FaceOutline':''})))
                    m.attrs['HelixPhonemeOwnership']='exclusive'
            static_materials(SimpleNamespace(models=performers));write_layout(g,folder,include_demo=False,export_all_custom=True)
            export_instruments(sequence.root,SimpleNamespace(models=performers),plan)
            export_vocals(sequence.root,folder/'xlights_rgbeffects.xml',SimpleNamespace(models=performers),
                          fixture=vocals,expected_sha256=sha)
            drummer,states,proof=band
            colors=('#DC2D1C','#D65CBE','#DCA416','#2CB242','#2CB242','#2CB242','#DCA416','#DCA416')
            from tools.render_owner_band_review import drum_hits
            from tools.render_drummer_v3_preview import TARGETS
            hits,_=drum_hits(plan['cues']['drummer'])
            for target,color in zip(TARGETS,colors):
                part=target+'_SURFACE';sequence.effect(drummer,part,0,duration_ms,color,22)
                for hit in hits:
                    if hit['target']==target:sequence.effect(drummer,part,round(hit['time']*1000),min(duration_ms,round(hit['time']*1000)+250),color,100,22)
            cuts=np.r_[0,np.flatnonzero(np.diff(states))+1,len(states)]
            for a,b in zip(cuts[:-1],cuts[1:]):sequence.effect(drummer,f'SOURCE_POSE_{states[a]:02}',int(a)*50,int(b)*50,'#C5D6DD',80)
            (folder/'Dimensional_Drummer.json').write_text(json.dumps(proof,indent=2)+'\n')
        else:write_layout(g,folder,include_demo=False,export_all_custom=True)
        (folder/'media').mkdir(exist_ok=True);shutil.copyfile(audio,folder/'media'/audio.name)
        from xlights.xml_io import materialize_native_effect_tables
        materialize_native_effect_tables(sequence.root)
        path=folder/'Performance.xsq';sequence.write(path)
        points=np.concatenate([m.points for m in g.models]);lo,hi=points.min(0),points.max(0);center=(lo+hi)/2;span=hi-lo
        distance=max(span[0]*.82,span[1]*1.75,45)+(span[2]/2 if number==11 else 0)
        if number==1:distance*=.85
        if number in (3,4,6,9):distance*=1.18
        if number==7:distance*=.80
        camera=ET.parse(folder/'xlights_rgbeffects.xml')
        for view in camera.findall('Viewpoints/*'):
            for key,value in dict(angleX=30 if number==13 else 8 if number in (2,7,10,14,15,16) else 5,angleY=0,distance=-distance,
                                  panx=-center[0],pany=-center[1],panz=-center[2]).items():view.set(key,str(value))
        camera.write(folder/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
        residential_preview(folder,number)
        item=dict(number=number,name=name,folder=str(folder.resolve()),xsq='Performance.xsq',source_audio_sha256=sha,
                  source_analysis_sha256=digest(plan_path),source_duration_seconds=duration,audio_name=audio.name,models=len(g.models),
                  channels=max(m.start+m.channels-1 for m in g.models),warnings=[],native_render_status='pending',
                  renderer_for_comparison='native xLights',owner_approved=False)
        (folder/'run_manifest.json').write_text(json.dumps(item,indent=2)+'\n')
        (folder/'Spatial_Event_Provenance.json').write_text(json.dumps(reports,indent=2)+'\n')
        manifest.append(item);print('BUILT',number,name,item['models'],item['channels'],flush=True)
    manifest.sort(key=lambda item:item['number'])
    (output/'Layout_Manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','vocals','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--layouts',type=int,nargs='+')
    args=parser.parse_args();build(args.source,args.vocals,args.output,numbers=args.layouts)
