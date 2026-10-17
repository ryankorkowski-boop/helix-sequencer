"""Opt-in RGB pose-bank export of Helix's actual source-timed arm geometry.

Every visible arm state comes from ReviewBandPerformance.pose(), never from
post-production animation. Existing AC16 exports/default models stay unchanged.
"""
from __future__ import annotations
import argparse,copy,json,shutil
from pathlib import Path
import numpy as np
import trimesh
from models.native_review_band import add_band,allocate
from models.ultimate_showcase import Garden
from models.review_3d_scene import Review3DScene
from models.final_band_native import SurfaceParts
from tools.render_approval_revision import setup
from tools.render_refined_helix_band import physical_hits
from tools.build_spatial_review import band_curves
from tools.build_snowman_ensemble import NativeSequence
from tools.build_helpers.ultimate_showcase import write_layout
from tools.audio_excerpt import digest


def select_states(samples,limit=32):
    """Deterministic farthest-point medoids; retain real source poses only."""
    values=np.asarray(samples,dtype='f4')
    if not 1<=limit<=128 or values.ndim!=3 or values.shape[-1]!=3 or not values.size or not np.isfinite(values).all():
        raise ValueError('Expected finite nonempty frame/point/XYZ samples and 1–128 poses')
    flat=values.reshape(len(values),-1)
    selected=[0];distance=np.sum((flat-flat[0])**2,axis=1)
    while len(selected)<min(limit,len(flat)) and float(distance.max())>1e-10:
        index=int(distance.argmax());selected.append(index)
        distance=np.minimum(distance,np.sum((flat-flat[index])**2,axis=1))
    errors=np.stack([np.mean((flat-flat[i])**2,axis=1) for i in selected],axis=1)
    states=errors.argmin(axis=1)
    return np.array(selected),states,float(np.sqrt(errors[np.arange(len(flat)),states]).max())


def vertices(item):
    if item['kind']=='cylinder':
        angle=np.linspace(0,2*np.pi,6,endpoint=False)
        points=np.concatenate([np.c_[np.zeros(25),np.zeros(25),np.linspace(-.5,.5,25)]]+[np.c_[np.cos(angle),np.sin(angle),np.full(6,z)] for z in (-.5,.5)])
    elif item['kind']=='sphere':points=trimesh.creation.icosphere(subdivisions=0).vertices
    elif item['kind']=='box':points=trimesh.creation.box().vertices
    else:raise ValueError(item['kind'])
    return (np.c_[points,np.ones(len(points))]@item['matrix'].T)[:,:3]


def cells(points):return [tuple(v) for v in np.rint(np.asarray(points)*16).astype(int)]


def prepare(source_root:Path,output:Path,eid='E14',limit=32,frame_ms=50):
    if frame_ms not in (25,50):raise ValueError('Native interval must be 25 or 50 ms')
    if output.exists():raise FileExistsError('Use a fresh directory')
    row,audio,scene,p=setup(source_root,eid,scene_factory=Review3DScene)
    g=Garden(title='Helix source-timed native RGB pose band',slug='Native_Source_Poses');add_band(g)
    p.row={'drummer_xsq':str(source_root/'sources'/eid/'drummer.xsq')}
    cues={m.name:band_curves(m,p,body_level=.85) for m in g.models}
    rigs=[dict(role=r['role'],side=r['side'],ids=tuple(r['ids'])+tuple(r.get('mallet_ids',()))) for r in scene.rigs]
    rigs += [dict(role='drummer',side=side,ids=tuple(r['ids'])) for side,r in scene.drummer_rigs.items()]
    rigs.append(dict(role='drummer',side='kick_beater',ids=(scene.kick_beater,)))
    trajectories=[[] for r in rigs]
    for i in range(p.n):
        p.pose(i)
        for j,rig in enumerate(rigs):trajectories[j].append(np.vstack([vertices(scene.instances[k]) for k in rig['ids']]))
    # Identify the original static drummer's idle and contact arms only.
    # Use the full original surface sampler to remove old arm outlines exactly.
    oldpoints=SurfaceParts((0,0,75),scale=5)
    def full_gather():
        for rig in oldscene.drummer_rigs.values():
            for idx in rig['ids']:oldpoints.primitive('OLD',oldscene.instances[idx])
        oldpoints.primitive('OLD',oldscene.instances[oldscene.kick_beater])
    oldscene=Review3DScene();full_gather()
    for target in ('CYMBAL_LEFT','TOM_FLOOR','TOM_MID','SNARE_LEFT','SNARE_RIGHT','TOM_HIGH','HI_HAT','CYMBAL_RIGHT'):
        side='left' if target in ('CYMBAL_LEFT','TOM_MID','SNARE_LEFT') else 'right'
        oldscene.configure_drummer([dict(target='HX_SNOWMAN_DRUMMER_V3_'+('SNARE' if target.startswith('SNARE') else target),time=0,side=side,velocity=1)])
        oldscene.update_drummer(0);full_gather()
    oldcells=set(cells(oldpoints.points));new=Garden(title=g.title,slug=g.slug);proof=[]
    for m in g.models:
        role=m.details['review_role'];points=list(m.points);colors=list(m.colors);subs=copy.deepcopy(m.submodels)
        for part in list(subs):
            if part.startswith('ARM_'):subs[part]=[];cues[m.name].pop(part,None)
        if role=='drummer':
            removed={i+1 for i,c in enumerate(cells(points)) if c in oldcells}
            subs={k:sorted(set(ids)-removed) for k,ids in subs.items()}
        protected=set().union(*(set(ids) for part,ids in subs.items() if part.startswith(('NOTE_','STRING_','MOUTH_'))))
        lookup={c:i+1 for i,c in enumerate(cells(points))};membership={};selections={}
        for j,rig in enumerate(rigs):
            if rig['role']!=role:continue
            selected,states,error=select_states(trajectories[j],limit);selections[j]=states
            proof.append(dict(role=role,side=rig['side'],states=len(selected),max_rms_source_geometry_error=error,
                              changed_adjacent_states=int(np.count_nonzero(np.diff(states))),source_frames=selected.tolist()))
            for state,frame in enumerate(selected):
                transformed=np.asarray(trajectories[j][frame])*5+(0,0,75)
                for cell in cells(transformed):
                    node=lookup.get(cell)
                    if node in protected:continue
                    if node is None:
                        node=len(points)+1;lookup[cell]=node;points.append(np.array(cell)/16);colors.append('#FFD8A0')
                    membership.setdefault(node,set()).add((j,state))
        occupied=set(membership)
        subs={part:sorted(set(ids)-occupied) for part,ids in subs.items()}
        groups={}
        for node,states in membership.items():groups.setdefault(tuple(sorted(states)),[]).append(node)
        for k,(members,nodes) in enumerate(groups.items()):
            part=f'SOURCE_POSE_{k:04d}';subs[part]=nodes
            curve=np.zeros(p.n,'f4')
            for j,state in members:curve=np.maximum(curve,(selections[j]==state)*.90)
            cues[m.name][part]=curve
        mnew=new.custom(m.name,points,m.zone,m.design,colors,subs,details={**m.details,'pose_method':'native source-timed RGB pose banks','ac16_compatible':False})
        mnew.attrs.update(PixelSize='4',Antialias='0',BlackTransparency='100',HelixOutputMode='pixel')
    if len(new.models)!=7 or len({m.name for m in new.models})!=7 or sum(m.channels for m in new.models)>250000:
        raise ValueError('Invalid seven-model or bounded RGB channel contract')
    positions=dict(DRUMMER=(0,26,65),BASS=(-24,9,80),GUITAR=(24,9,80),PIANO=(25,28,65),XYLOPHONE=(-25,28,65),LEAD=(-8,9,80),HARMONY=(8,9,80))
    for old,m in zip(g.models,new.models):
        delta=np.array(positions[m.details['review_role'].upper()])-np.array([float(old.attrs['WorldPos'+a]) for a in 'XYZ'])
        m.points+=delta
        for j,axis in enumerate('XYZ'):m.attrs['WorldPos'+axis]=str(float(m.attrs['WorldPos'+axis])+delta[j])
    allocate(new);output.mkdir(parents=True);(output/'media').mkdir();shutil.copy2(audio,output/'media/audio.wav')
    write_layout(new,output,include_demo=False,export_all_custom=True)
    import xml.etree.ElementTree as ET
    tree=ET.parse(output/'xlights_rgbeffects.xml')
    for camera in tree.findall('./Viewpoints/*'):
        for key,value in dict(angleX='8',angleY='0',distance='-65',pany='-18',panz='-75').items():camera.set(key,value)
    ET.indent(tree);tree.write(output/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
    sequence=NativeSequence(new,36,'media/audio.wav',row['filename'])
    sequence.root.find('head/sequenceTiming').text=f'{frame_ms} ms'
    for m in new.models:
        for part,curve in cues[m.name].items():
            if not m.submodels.get(part):continue
            values=np.rint(np.clip(curve,0,1)*20).astype(int)*5
            color='#FFD8A0' if part.startswith('SOURCE_POSE') else m.colors[m.submodels[part][0]-1]
            if part.startswith(('STRING_','NOTE_MIDI_')):
                rgb=np.array([int(color[k:k+2],16) for k in (1,3,5)]);peak=int(rgb.max())
                if 0<peak<200:color='#'+''.join(f'{int(round(x*200/peak)):02X}' for x in rgb)
            cuts=np.r_[0,np.flatnonzero(np.diff(values))+1,p.n]
            for a,b in zip(cuts[:-1],cuts[1:]):
                if values[a]:sequence.effect(m,part,int(a)*50,int(b)*50,color,int(values[a]))
    sequence.write(output/'Performance.xsq')
    np.savez_compressed(output/'expected_cues.npz',**{name+'::'+part:np.rint(v*20)*5 for name,parts in cues.items() for part,v in parts.items() if new.models[[m.name for m in new.models].index(name)].submodels.get(part)})
    result=dict(excerpt=eid,source_record=row,audio_sha256=digest(audio),source_score='ReviewBandPerformance.pose',geometry_source='Review3DScene',source_frames=720,frame_ms=frame_ms,native_frames=36000//frame_ms,source_pose_frame_ms=50,
                source_musical_cues_retimed=False,ac16_models_modified=False,channels=sum(m.channels for m in new.models),effects=sequence.identifier-1,rigs=proof,
                limitations=['RGB pose-bank geometry requires its own pixel mapping; not a 16-channel AC model','Source musical estimators retain their uncertainty','Finite source-pose medoids approximate geometric motion; source event clock is preserved'])
    (output/'pose_provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('source_root',type=Path);a.add_argument('output',type=Path);a.add_argument('--id',default='E14');a.add_argument('--poses',type=int,default=32);a.add_argument('--frame-ms',type=int,choices=[25,50],default=50);v=a.parse_args();prepare(v.source_root.resolve(),v.output.resolve(),v.id,v.poses,v.frame_ms)
