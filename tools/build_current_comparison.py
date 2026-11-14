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
from models.band_sampler_logic import NATIVE_SHAPE_NAMES, SHAPE_NAMES

NAMES=('Original 256-channel AC Christmas','Canonical 3D snowman band',
       'Simple RGB house','RGB arches and roofline','RGB mega trees and spirals',
       'RGB house with singing faces','Pixel rock-band stage',
       'Double helix with keyboard rungs','Advanced RGB house and matrices',
       'Multi-house neighborhood','Advanced 3D spatial showcase','Ultimate Helix showcase')


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


def native_band(g,plan,*,rock=True,duration=36,showcase_source=False,overview=False,native_extended_mouths=False):
    from models.final_band_native import add_final_native_band,SurfaceParts
    from models.final_band_scene import FinalBandScene
    from models.source_drummer_3d import SourceDrummer3D
    from tools.render_owner_band_review import drum_hits
    from tools.native_source_pose_band import select_states
    first=len(g.models)
    add_final_native_band(g,'HX_SNOW',(0,0,0),rock=rock,include_stage=not showcase_source,
                          full_keyboard=True,surface_spacing=.12 if showcase_source and not overview else .18,
                          mouth_scale=.42,keyboard_contacts=showcase_source,
                          native_extended_mouths=native_extended_mouths, string_contacts=showcase_source)
    cast=g.models[first:]
    for model in cast:
        if model.details.get('final_band_role'):
            model.details['review_role']=model.details['final_band_role']
    scene=FinalBandScene('ember_amphitheatre',rock=rock,full_keyboard=True)
    hits,unresolved=drum_hits(plan.get('cues',{}).get('drummer',[]))
    rig=SourceDrummer3D(scene,hits,width=5.1 if showcase_source else 4.5,
                        center=(0,4.3,-1.4) if showcase_source else (0,2.26,-1.4))
    parts=SurfaceParts((0,0,0),scale=5)
    for item in rig.meshes:
        name=item['name'];part=name+'_SURFACE' if name.startswith('HX_SNOWMAN_') else 'BASE_DIM'
        # A bounded source-material palette retains front colors without
        # creating one native effect lane for every antialiased image value.
        color=np.clip(np.rint(item['mesh'].visual.vertex_colors[:,:3]/32)*32,0,255).astype('u1')
        colors=['#'+''.join(f'{int(c):02X}' for c in row) for row in color]
        if showcase_source:
            # Sample both front and rear; the previous stride selected half
            # the front and discarded its authored materials during export.
            stride=2 if overview else 1
            points=item['mesh'].vertices[::stride]
            material=colors[::stride]
            parts.add('BASE_DIM',points,material)
            if part!='BASE_DIM':parts.add(part,points,material)
        else:
            parts.add(part,item['mesh'].vertices[::2],colors[::2])
    for i in rig.connector_ids:parts.primitive('BASE_DIM',scene.instances[i])
    ids=[i for values in rig.rigs.values() for i in values]+[rig.foot,rig.pedal,rig.beater]
    pose_times = np.arange(math.ceil(duration*20)) / 20
    contacts = {}
    pose_lanes = {}
    if showcase_source:
        for side, lane in rig.player.lanes.items():
            target_ids = rig.rigs[side]
            times = pose_times.copy()
            contact_frames = {}
            for hit in lane.events:
                frame = min(len(times)-1, round(hit['time']*20))
                previous = contact_frames.get(frame)
                if previous is None or hit['velocity'] > previous['velocity']:
                    contact_frames[frame] = hit
            for frame, hit in contact_frames.items():
                times[frame] = hit['time']
            samples = []
            for time in times:
                rig.pose_arm(side, time)
                samples.append([scene.instances[i]['matrix'][:3,3] for i in target_ids])
            # Contact poses are assigned from exact targets. Quantize only transit.
            selected, states, error = select_states(samples, limit=18 if overview else 30)
            names = []
            for number, frame in enumerate(selected):
                part = f'SOURCE_POSE_{side.upper()}_{number:02}'
                rig.pose_arm(side, times[frame])
                for i in target_ids:
                    parts.primitive(part, scene.instances[i])
                names.append(part)
            sequence_parts = np.asarray(names, dtype=object)[states]
            for frame, hit in contact_frames.items():
                part = f'SOURCE_POSE_{side.upper()}_{hit["target"].rsplit("_V3_",1)[-1]}'
                if part not in parts.parts:
                    rig.pose_arm(side, hit['time'])
                    for i in target_ids:
                        parts.primitive(part, scene.instances[i])
                sequence_parts[frame] = part
            contacts[side] = len(contact_frames)
            pose_lanes[side] = (sequence_parts, error)
        for part, target_ids, source_hits in (
            ('HAT', (rig.foot, rig.pedal), rig.player.foot_hits),
            ('KICK', (rig.beater,), rig.player.kick_hits),
        ):
            clock = np.full(len(pose_times), f'SOURCE_POSE_{part}_REST', dtype=object)
            for hit in source_hits:
                frame = min(len(clock)-1, round(hit['time']*20))
                clock[frame:frame+2] = f'SOURCE_POSE_{part}_CONTACT'
            rig.pose_feet(False, False)
            for i in target_ids:
                parts.primitive(f'SOURCE_POSE_{part}_REST', scene.instances[i])
            if source_hits:
                rig.pose_feet(part=='HAT', part=='KICK')
                for i in target_ids:
                    parts.primitive(f'SOURCE_POSE_{part}_CONTACT', scene.instances[i])
            pose_lanes[part] = (clock, 0)
        states = {lane: clock for lane,(clock,_) in pose_lanes.items()}
        error = max(error for _,error in pose_lanes.values())
        pose_count = sum(name.startswith('SOURCE_POSE_') for name in parts.parts)
    else:
        samples = []
        for time in pose_times:
            rig.pose(time)
            samples.append([scene.instances[i]['matrix'][:3,3] for i in ids])
        selected, states, error = select_states(samples, limit=24)
        for number, frame in enumerate(selected):
            rig.pose(pose_times[frame])
            for i in ids:
                parts.primitive(f'SOURCE_POSE_{number:02}', scene.instances[i])
        pose_count = len(selected)
    old=next(m for m in g.models if m.details.get('review_role')=='drummer')
    g.models.remove(old)
    model=g.custom('HX_SNOW_DRUMMER',parts.points,'BAND','Source-front closed dimensional V3',
        parts.colors,{k:sorted(set(v)) for k,v in parts.parts.items()},
        details=dict(review_role='drummer',final_band_role='drummer',source_front_volume=True,
                     source_pose_error=error,pose_method='source-clock selected real 3D poses'))
    for m in (*cast,model):
        m.attrs.pop('StartChannel',None)
        m.attrs.update(PixelSize='7',Antialias='1',BlackTransparency='100')
    if showcase_source:
        model.attrs['HelixReferenceImage']='assets/drummerbg.png'
        model.details['showcase_source_drummer']=True
    return model,states,dict(rig.proof(),resolved_strikes=len(hits),unresolved_strikes=unresolved,
                             pose_states=pose_count,max_pose_error=float(error),
                             contact_sample_frames=sum(contacts.values()),
                             independent_native_pose_lanes=list(pose_lanes),
                             physically_rejected_arm_strikes=len(rig.player.motion_rejections))


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
    else:
        g=build_layout(12);g.models=[m for m in g.models if not m.details.get('review_role')]
    for model in g.models:
        model.attrs.pop('StartChannel',None)
        model.details.setdefault('source_display_floor',.50)
        model.attrs.setdefault('PixelSize','18')
    arches=[m for m in g.models if m.zone=='ARCHES']
    for index,model in enumerate(sorted(arches,key=lambda m:float(np.mean(m.points[:,0])))):
        model.details['percussion_component']=('kick','snare','hihat','cymbal')[index%4]
    return allocate(g),None


def build(source,vocals,output,*,numbers=None,names=NAMES,layout_builder=layout,
          preserve_addresses=(1,),instrumental=False,expected_sha256=None,
          band_source_plan=None, align_band_frames=False):
    source,output=map(Path,(source,output));output.mkdir(parents=True,exist_ok=True)
    source_manifest=json.loads((source/'run_manifest.json').read_text())
    audio=source/'media'/source_manifest.get('audio_name','Helix_Starred_New_Review.wav');sha=digest(audio)
    full_song=expected_sha256 is not None
    if full_song and (sha!=expected_sha256 or source_manifest.get('audio_sha256')!=sha):
        raise ValueError('Production analysis does not belong to the verified original')
    if instrumental != (vocals is None):
        raise ValueError('Supply source vocal evidence or explicitly select instrumental input')
    import soundfile as sf
    duration=sf.info(audio).duration;duration_ms=round(duration*1000)
    plans=(source/'sequence').rglob('*.snowman_band.json') if full_song else (source/'sequence').glob('*.snowman_band.json')
    plan_path,=plans
    plan=json.loads(plan_path.read_text())
    if band_source_plan is not None:
        from tools.band_source_evidence import apply_evidence
        plan = apply_evidence(plan, audio, band_source_plan)
    cache={}
    shape_names=SHAPE_NAMES
    if vocals is not None:
        vocals=Path(vocals)
        receipt=json.loads((vocals/'diagnostic.json').read_text())
        if receipt['audio_sha256']!=sha or receipt['clock_sha256']!=digest(vocals/'acoustic_vocal_clocks.npz'):
            raise ValueError('Foreign vocal analysis')
        with np.load(vocals/'acoustic_vocal_clocks.npz') as z:cache={k:z[k].copy() for k in z.files}
        if full_song and receipt.get('verification_state')=='VERIFIED':
            from tools.vocal_analysis_fixture import verify_fixture
            verify_fixture(audio,vocals,receipt)
            shape_names=NATIVE_SHAPE_NAMES
        elif full_song:
            from tools.phoneme_vocal_export import screened_lanes
            lanes,_=screened_lanes(cache)
            for lane,(energy,shapes) in lanes.items():
                cache[lane+'_energy'],cache[lane+'_shapes']=energy,shapes
    numbers=tuple(range(1,len(names)+1)) if numbers is None else tuple(numbers)
    if not numbers or len(set(numbers))!=len(numbers) or any(type(n) is not int or not 1<=n<=len(names) for n in numbers):
        raise ValueError(f'Choose unique layout numbers in 1..{len(names)}')
    manifest=json.loads((output/'Layout_Manifest.json').read_text()) if (output/'Layout_Manifest.json').exists() else []
    if any(item['source_audio_sha256']!=sha for item in manifest):raise ValueError('Foreign retained layout source')
    manifest=[item for item in manifest if item['number'] not in numbers]
    for number in numbers:
        name=names[number-1]
        folder=output/f'{number:02}'
        if folder.exists():raise FileExistsError(folder)
        layout_options = {'native_extended_mouths': True} if shape_names == NATIVE_SHAPE_NAMES else {}
        g,band=layout_builder(number,plan,duration=duration,**layout_options);g.title=name
        if number not in preserve_addresses:allocate(g)
        for m in g.models:
            if not m.submodels:m.submodels['ALL']=list(range(1,len(m.points)+1))
        sequence=NativeSequence(g,duration,'media/'+audio.name,name);reports=[]
        if full_song:
            sequence.duration=duration_ms
            sequence.root.find('head/sequenceDuration').text=f'{duration:.3f}'
            sequence.root.find('head/comment').text='Helix production analysis on the verified full recording.'
        for m in g.models:
            if m.details.get('review_role'):continue
            if m.details.get('generic_singer'):
                lane=m.details['generic_singer']
                if instrumental:
                    if m.submodels.get('MOUTH_REST'):
                        sequence.effect(m,'MOUTH_REST',0,duration_ms,g.palette[2],75 if m.details.get('showcase_face') else 50)
                else:
                    values=np.where(cache[lane+'_energy']>0,cache[lane+'_shapes'],0)
                    cuts=np.r_[0,np.flatnonzero(np.diff(values))+1,len(values)]
                    for a,b in zip(cuts[:-1],cuts[1:]):
                        part='MOUTH_'+shape_names[int(values[a])]
                        if m.submodels.get(part):sequence.effect(m,part,int(a)*10,int(b)*10,g.palette[2],95)
                face_parts=('OUTLINE','BASE','BODY','EYES')
                primary_faces=full_song and (number in (8,9) or m.details.get('showcase_face'))
                if primary_faces:
                    face_parts+=tuple(part for part in m.submodels if part.startswith('EYE_'))
                for part in face_parts:
                    if m.submodels.get(part):
                        color=m.colors[m.submodels[part][0]-1] if primary_faces else g.palette[0]
                        sequence.effect(m,part,0,duration_ms,color,75 if primary_faces else 40)
                if m.details.get('showcase_face'):
                    for lane, part, color in (
                        ('bassist', 'HELIX_A', g.palette[0]),
                        ('guitarist', 'HELIX_B', g.palette[1]),
                    ):
                        if m.submodels.get(part):
                            for cue in plan['cues'].get(lane, ()):
                                if cue['kind'] not in ('chord_change', 'transition'):
                                    sequence.effect(m, part, cue['start_ms'], cue['end_ms'], color, 45, 12)
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
            from tools.phoneme_vocal_export import export_static_materials, static_materials, export as export_vocals
            from tools.canonical_band_cues import export_instruments
            from models.canonical_native_band import EXTENDED_VISEMES, VISEMES
            performers=[m for m in g.models if m.details.get('review_role')]
            for m in performers:
                if m.details['review_role'] in ('lead','harmony'):
                    if 'MOUTH_AI' not in m.submodels:
                        original=dict(m.submodels)
                        visemes = EXTENDED_VISEMES if 'MOUTH_U' in original else VISEMES
                        for viseme,shape in visemes.items():m.submodels['MOUTH_'+viseme]=list(original['MOUTH_'+shape])
                        m.children.append(('faceInfo',dict(Name='Helix independent phonemes',Type='NodeRange',
                            **{'Mouth-'+v:','.join(map(str,m.submodels['MOUTH_'+v])) for v in visemes},
                            **{'Eyes-Open':'','Eyes-Closed':'','FaceOutline':''})))
                        m.attrs['HelixPhonemeOwnership']='exclusive'
            static_materials(SimpleNamespace(models=performers));write_layout(g,folder,include_demo=False,export_all_custom=True)
            instrument_report=export_instruments(sequence.root,SimpleNamespace(models=performers),plan,
                                                 qualified_keyboard=full_song,
                                                 native_frame_ms=50 if align_band_frames else None)
            from tools.canonical_band_cues import refresh_models
            refresh_models(g, folder/'xlights_rgbeffects.xml')
            if full_song:
                (folder/'Band_Instrument_Provenance.json').write_text(json.dumps(instrument_report,indent=2)+'\n')
            if instrumental:
                export_static_materials(sequence.root,SimpleNamespace(models=performers),duration_ms)
                for m in performers:
                    if m.submodels.get('MOUTH_rest'):
                        sequence.effect(m,'MOUTH_rest',0,duration_ms,'#F1C383',55)
            else:
                vocal_report=export_vocals(sequence.root,folder/'xlights_rgbeffects.xml',SimpleNamespace(models=performers),
                                           fixture=vocals,expected_sha256=sha,source_audio=audio,
                                           native_frame_ms=50 if align_band_frames else None)
                if full_song:
                    (folder/'Band_Vocal_Provenance.json').write_text(json.dumps(vocal_report,indent=2)+'\n')
            drummer,states,proof=band
            if states is None:
                # An owner-reviewed V3 kit has real source component IDs.
                # Never discard it and replace it with a guessed pose bank.
                from tools.canonical_band_cues import export_drums
                source_report=export_drums(sequence.root,SimpleNamespace(models=performers),plan)
                (folder/'Canonical_Drummer.json').write_text(json.dumps(
                    dict(geometry=proof,event_mapping=source_report),indent=2)+'\n')
            else:
                colors=('#DC2D1C','#D65CBE','#DCA416','#2CB242','#2CB242','#2CB242','#DCA416','#DCA416')
                from tools.render_owner_band_review import drum_hits
                from tools.render_drummer_v3_preview import TARGETS
                hits,_=drum_hits(plan['cues']['drummer'])
                for target,color in zip(TARGETS,colors):
                    part=target+'_SURFACE'
                    if not drummer.details.get('showcase_source_drummer'):
                        sequence.effect(drummer,part,0,duration_ms,color,22)
                    for hit in hits:
                        if hit['target']==target:
                            start=round(hit['time']*1000)
                            tail=95 if target in TARGETS[:3] else 150 if target in TARGETS[3:6] else 220
                            intensity=round(25+75*hit['velocity'])
                            sequence.effect(drummer,part,start,min(duration_ms,start+tail),color,intensity,18)
                clocks = states.values() if isinstance(states, dict) else (
                    np.asarray([f'SOURCE_POSE_{state:02}' for state in states]),)
                for clock in clocks:
                    cuts=np.r_[0,np.flatnonzero(clock[1:] != clock[:-1])+1,len(clock)]
                    for a,b in zip(cuts[:-1],cuts[1:]):
                        part=clock[a]
                        if part in drummer.submodels:
                            sequence.effect(drummer,part,int(a)*50,int(b)*50,'#C5D6DD',80)
                (folder/'Dimensional_Drummer.json').write_text(json.dumps(proof,indent=2)+'\n')
        else:write_layout(g,folder,include_demo=False,export_all_custom=True)
        (folder/'media').mkdir(exist_ok=True);shutil.copyfile(audio,folder/'media'/audio.name)
        from xlights.xml_io import materialize_native_effect_tables
        materialize_native_effect_tables(sequence.root)
        path=folder/'Performance.xsq';sequence.write(path)
        camera_models=performers if full_song and band and number != 16 else g.models
        points=np.concatenate([m.points for m in camera_models]);lo,hi=points.min(0),points.max(0);center=(lo+hi)/2;span=hi-lo
        if full_song:
            distance=max(span[0]*.88,span[1]*1.75,42)+span[2]*.40
            pitch=5 if band else 14 if number in (13,15) else 5
            yaw=17 if number==15 else 7 if number==13 else 0
        else:
            distance=max(span[0]*.82,span[1]*1.75,45)+(span[2]/2 if number==11 else 0)
            if number==1:distance*=.85
            if number in (3,4,6,9):distance*=1.18
            if number==7:distance*=.80
            pitch=8 if number in (2,7,10) else 5
            yaw=0
        camera=ET.parse(folder/'xlights_rgbeffects.xml')
        for view in camera.findall('Viewpoints/*'):
            for key,value in dict(angleX=pitch,angleY=yaw,distance=-distance,
                                  panx=-center[0],pany=-center[1],panz=-center[2]).items():view.set(key,str(value))
        camera.write(folder/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
        if not full_song:
            residential_preview(folder,number)
        else:
            from tools.native_residential_context import add_showcase_context
            add_showcase_context(folder, g)
        item=dict(number=number,name=name,folder=str(folder.resolve()),xsq='Performance.xsq',source_audio_sha256=sha,
                  source_analysis_sha256=digest(plan_path),source_duration_seconds=duration,audio_name=audio.name,models=len(g.models),
                  channels=max(m.start+m.channels-1 for m in g.models),warnings=[],native_render_status='pending',
                  renderer_for_comparison='Helix solid 3D' if number==2 and not full_song else 'native xLights',
                  owner_approved=False)
        if full_song:
            item.update(layout_sha256=digest(folder/'xlights_rgbeffects.xml'),xsq_sha256=digest(path),
                        vocal_mode='instrumental_rest' if instrumental else receipt.get('verification_state','estimate'),
                        canonical_cast_count=len(performers) if band else 0)
        if band_source_plan is not None:
            item['band_source_plan_sha256'] = digest(Path(band_source_plan))
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
    parser.add_argument('--expected-audio-sha256')
    parser.add_argument('--band-source-plan',type=Path)
    parser.add_argument('--align-band-frames',action='store_true')
    parser.add_argument('--canonical-band',action='store_true',help='Build the six-member full-song layout only')
    args=parser.parse_args()
    options = dict(numbers=args.layouts, expected_sha256=args.expected_audio_sha256,
                   band_source_plan=args.band_source_plan, align_band_frames=args.align_band_frames)
    if args.canonical_band:
        if args.layouts is not None or args.expected_audio_sha256 is None:
            parser.error('--canonical-band requires --expected-audio-sha256 and selects the layout itself')
        from models.full_song_layouts import build as band_layout, NAMES as full_song_names
        options.update(numbers=(11,), names=full_song_names, layout_builder=band_layout,
                       preserve_addresses=())
    build(args.source, args.vocals, args.output, **options)
