"""Compile the shared musical score to editable native XSQ, then native FSEQ."""
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path
import numpy as np
from models.native_review_band import ROLES, SHAPE_VISEME, add_band, ac_variant, allocate
from models.ultimate_showcase import Garden
from models.review_spatial_worlds import build_world
from models.band_sampler_logic import SHAPE_NAMES
from tools.render_approval_revision import setup
from tools.build_snowman_ensemble import NativeSequence
from tools.build_helpers.ultimate_showcase import write_layout
from music.review_score import spatial_score
from core.output_capabilities import detect_output, encode_output


def _note_curves(events,n):
    result={}
    for event in events:
        a=max(0,int(np.ceil(event.start*20-1e-7)));b=min(n,int(np.ceil(event.end*20-1e-7)))
        if b<=a:continue
        v=result.setdefault(event.pitch,np.zeros(n,'f4'));v[a:b]=np.maximum(v[a:b],event.velocity)
    return result


def band_curves(model,p):
    n=p.n;role=model.details['review_role'];out={};notes=_note_curves(p.keyboard_events,n)
    if role=='drummer':
        # Retain independently tagged physical source schedules (two snare hands).
        from tools.render_refined_helix_band import physical_hits
        out={k:np.zeros(n,'f4') for k in model.submodels}
        out['BASE_DIM'][:]=.14
        for hit in physical_hits(p.row['drummer_xsq']):
            component=hit.get('component',hit.get('target',''))
            # Hits use canonical source names; hand determines snare circuit.
            if 'SNARE' in component:component='SNARE_'+hit.get('side','left').upper()
            elif component.startswith('HX_SNOWMAN_DRUMMER_V3_'):component=component.removeprefix('HX_SNOWMAN_DRUMMER_V3_')
            if component not in out:continue
            a=round(hit['time']*20);length=3 if 'CYMBAL' in component else 1
            for k in range(length):
                if 0<=a+k<n:out[component][a+k]=max(out[component][a+k],float(hit.get('velocity',1))*np.exp(-k/1.3))
        return out
    out['BODY']=np.full(n,.20,'f4')
    if 'EYES' in model.submodels:out['EYES']=np.full(n,.30,'f4')
    if role in ('lead','harmony'):
        j=int(role=='harmony');shapes=p.voice_lanes[:,j]
        for part in model.submodels:
            if part.startswith('MOUTH_'):
                vis=part.removeprefix('MOUTH_');mask=np.array([SHAPE_VISEME[SHAPE_NAMES[int(x)]]==vis for x in shapes])
                out[part]=mask*np.where(shapes==0,.22,np.maximum(.25,p.voice_energy[:,j]))
            elif part.startswith('ARM_'):out[part]=p.voice_energy[:,j]*.6 if part.endswith('ACTIVE') else (p.voice_energy[:,j]<.12)*.2
    elif role in ('piano','xylophone'):
        if role=='xylophone':
            from music.note_events import NoteEvent
            notes=_note_curves([NoteEvent(h['time'],min(n/20,h['time']+.10),h['pitch'],h['velocity']) for h in p.mallet_schedule],n)
        for part in model.submodels:
            if part.startswith('NOTE_MIDI_'):out[part]=notes.get(int(part.rsplit('_',1)[1]),np.zeros(n))
            if part.startswith('PITCH_CLASS_'):
                curves=[v for pitch,v in notes.items() if pitch%12==int(part.rsplit('_',1)[1])]
                out[part]=np.maximum.reduce(curves) if curves else np.zeros(n)
            if part.startswith('ARM_'):
                active=np.maximum.reduce(list(notes.values())) if notes else np.zeros(n)
                out[part]=active*.65 if part.endswith('ACTIVE') else (active<.08)*.2
    else:
        for part in model.submodels:
            if part.startswith('STRING_'):
                j=int(part.rsplit('_',1)[1]);v=np.zeros(n)
                for i,routes in enumerate(p.curves[role+'_routes']):
                    if any(r[0]==j for r in routes):v[i]=p.curves[role+'_energy'][i]
                out[part]=v
            elif part.startswith('ARM_'):out[part]=p.curves[role+'_attack'] if part.endswith('ACTIVE') else (p.curves[role+'_energy']<.1)*.2
    return out


def score(g,p,variant):
    positions=[np.mean(m.points,axis=0) for m in g.models];roles=[]
    for j,m in enumerate(g.models):
        role=2 if m.details.get('midi_rungs') else 0 if 'PROMENADE' in m.zone else 1 if m.details.get('spiral_tree') else j%6
        roles.append(role)
    levels,proof=spatial_score(p,positions,roles,variant)
    notes=_note_curves(p.keyboard_events,p.n);result={}
    for j,m in enumerate(g.models):
        if m.details.get('review_role'):
            result[m.name]=band_curves(m,p);continue
        if m.kind!='pixel':result[m.name]={};continue
        if m.details.get('midi_rungs'):
            result[m.name]={f'KEY_MIDI_{pitch:03d}':notes.get(pitch,np.zeros(p.n)) for pitch in range(21,109)}
            for strand in ('STRAND_A','STRAND_B'):result[m.name][strand]=levels[j]*.32
        elif m.details.get('moire'):
            result[m.name]={}
            for part in [x for x in m.submodels if x.startswith('BAND_')]:
                band=int(part.rsplit('_',1)[1]);shift=(band+variant*2+m.details['plane']*5)*2
                v=np.zeros(p.n);v[shift:]=levels[j,:p.n-shift]
                result[m.name][part]=v
        elif m.details.get('spiral_tree'):
            parts=[x for x in m.submodels if x.startswith('STRAND_')]
            result[m.name]={}
            for k,part in enumerate(parts):
                shift=k*2;v=np.zeros(p.n);v[shift:]=levels[j,:p.n-shift] if shift else levels[j]
                result[m.name][part]=v
        else:
            m.submodels['SCORE_ALL']=list(range(1,len(m.points)+1))
            result[m.name]={'SCORE_ALL':levels[j]}
    return result,proof


def build(root,eid,variant):
    row,audio,scene,p=setup(root,eid)
    if variant<3:g=build_world(variant);name='World_'+str(variant+1)
    else:
        g=Garden(title='Helix '+('AC16' if variant==3 else 'Pixel')+' Snow Band',slug='Helix_Native_Band')
        add_band(g)
        if variant==3:g.models=[ac_variant(m) for m in g.models];allocate(g)
        name='AC16_Band' if variant==3 else 'Pixel_Band'
    p.row={'drummer_xsq':str(root/'sources'/eid/'drummer.xsq')}
    cues,proof=score(g,p,variant);folder=root/'shows'/eid/name;folder.mkdir(parents=True,exist_ok=True)
    media=folder/'media';media.mkdir(exist_ok=True);shutil.copy2(audio,media/'audio.wav')
    write_layout(g,folder,include_demo=False)
    seq=NativeSequence(g,36,'media/audio.wav',g.title+' / '+row['filename'])
    seq.root.find('head/comment').text='Source-clock review: native stationary 3D light poses, source keyboard rungs, independent spatial score. No physical hardware test.'
    output={}
    for m in g.models:
        mode=detect_output({'StringType':'RGB Nodes' if m.kind=='pixel' else 'Single Color White',**m.attrs}).mode
        output[m.name]={'mode':mode,'channels':m.channels,'kind':m.kind}
        for part,values in cues[m.name].items():
            if part not in m.submodels or not m.submodels[part]:continue
            # Fixed 5% levels bound editable effect count; preserve 50ms timing.
            values=(np.rint(np.clip(values,0,1)*20)*5).astype('u1')
            color='#FFFFFF' if mode=='ac16' else m.colors[m.submodels[part][0]-1]
            cuts=np.r_[0,np.flatnonzero(np.diff(values))+1,p.n]
            for a,b in zip(cuts[:-1],cuts[1:]):
                value=int(values[a])
                if value:seq.effect(m,part,int(a)*50,int(b)*50,color,value)
        if mode=='ac16':encode_output(np.zeros((1,m.channels)),mode)
    path=folder/'Performance.xsq';seq.write(path)
    proof.update(excerpt=eid,variant=name,models=len(g.models),effects=seq.identifier-1,
                 outputs=output,native_render_pending=True,all_snowmen=True)
    (folder/'score_proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    # Expected cues let the native gate compare real rendered channels rather
    # than trusting the generator's own XML syntax alone.
    np.savez_compressed(folder/'expected_cues.npz',**{m+'::'+part:np.rint(v*20)*5 for m,parts in cues.items() for part,v in parts.items()})
    print(eid,name,len(g.models),seq.identifier-1,flush=True)
    return g,path

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--id',default='E03');a.add_argument('--variant',type=int,required=True);args=a.parse_args();build(args.root,args.id,args.variant)
