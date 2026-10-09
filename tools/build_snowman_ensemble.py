"""Build source-bound native performances and movies from their rendered FSEQ.

Only native On cues drive the stationary model/submodel replacement geometry.
Movies project the same XYZ nodes and actual native values, with original audio.
"""
from __future__ import annotations
import argparse
import bisect
import json
import math
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image,ImageDraw

from models.snowman_ensemble import build_ensemble
from models.approved_concepts import ROOT
from tools.build_helpers.ultimate_showcase import write_layout,model_xml,_write_xml
from tools.build_helpers.ultimate_showcase_preview import read_fseq,_font,write_html
from tools.build_approved_concepts import ConceptView
from tools.analyze_snowman_ensemble import sha


class NativeSequence:
    def __init__(self,g,duration,media,title):
        self.g,self.duration=g,round(math.ceil(duration*20)*50)
        self.root=ET.Element('xsequence',{'BaseChannel':'1','FixedPointTiming':'1','ModelBlending':'true'})
        head=ET.SubElement(self.root,'head')
        for key,value in dict(version='2026.18',author='Helix',song=title,sequenceTiming='50 ms',
                              sequenceType='Media',sequenceDuration=f'{self.duration/1000:.3f}',mediaFile=media,
                              comment='Source-bound inferred performance; native stationary replacement poses. Word-aligned mouths use allocated phone durations.').items():ET.SubElement(head,key).text=value
        ET.SubElement(self.root,'nextid').text='1'
        for tag in ('ColorPalettes','EffectDB','DisplayElements','ElementEffects'):ET.SubElement(self.root,tag)
        self.palettes,self.settings,self.layers,self.elements={},{},{},{}
        self.identifier=1
        for model in g.models:
            ET.SubElement(self.root.find('DisplayElements'),'Element',{'type':'model','name':model.name,'visible':'1','collapsed':'1'})
            self.elements[model.name]=ET.SubElement(self.root.find('ElementEffects'),'Element',{'type':'model','name':model.name})
            ET.SubElement(self.elements[model.name],'EffectLayer')

    def effect(self,model,part,start,end,color,b0=70,b1=None,provenance=None,layer=0,settings=None,palette=None):
        if part not in model.submodels:raise ValueError(f'Unknown native target {model.name}/{part}')
        start=max(0,round(start/50)*50);end=min(self.duration,round(end/50)*50)
        if end<=start:return
        b1=b0 if b1 is None else b1
        setting=settings or f'E_TEXTCTRL_Eff_On_Start={b0},E_TEXTCTRL_Eff_On_End={b1}'
        palette=palette or f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'
        if setting not in self.settings:
            self.settings[setting]=len(self.settings);ET.SubElement(self.root.find('EffectDB'),'Effect').text=setting
        if palette not in self.palettes:
            self.palettes[palette]=len(self.palettes);ET.SubElement(self.root.find('ColorPalettes'),'ColorPalette').text=palette
        key=(model.name,part,layer)
        if key not in self.layers:self.layers[key]=ET.SubElement(self.elements[model.name],'SubModelEffectLayer',{'name':part,'layer':str(layer)})
        ET.SubElement(self.layers[key],'Effect',{'name':'On','ref':str(self.settings[setting]),'palette':str(self.palettes[palette]),
                                               'startTime':str(start),'endTime':str(end),'id':str(self.identifier),**(provenance or {})})
        self.identifier+=1

    def write(self,path):
        self.root.find('nextid').text=str(self.identifier);_write_xml(self.root,path)


def intervals(values):
    boundaries=np.r_[0,np.flatnonzero(np.diff(values))+1,len(values)]
    return [(int(a*50),int(b*50),int(values[a])) for a,b in zip(boundaries[:-1],boundaries[1:])]


def source_curves(events,frames,part_count):
    active=np.zeros(frames,dtype=np.uint8);notes=[np.zeros(frames,dtype=np.uint8) for _ in range(part_count)]
    for event in events:
        a=round(event['start_ms']/50);b=min(frames,a+max(2,round(event.get('duration_ms',180)/50)))
        if a>=frames:continue
        level=round(60+40*event['intensity']);active[a:b]=np.maximum(active[a:b],level)
        curve=notes[event['midi']%part_count];curve[a:b]=np.maximum(curve[a:b],level)
    return active,notes


def import_drummer(sequence,base,audio,transcript,output):
    from tools.integrate_drummer_v3_into_xsq import inject_drummer_v3
    report=inject_drummer_v3(base,output,audio,transcription_path=transcript)
    tree=ET.parse(output)
    model=sequence.g.models[0]
    source_count=0
    for element in tree.findall('./ElementEffects/Element'):
        part=element.get('name')
        if part not in model.submodels:continue
        for layer in element.findall('EffectLayer'):
            if layer.get('visible')=='0':continue
            for effect in layer.findall('Effect'):
                settings=effect.get('settings','');palette=effect.get('palette','')
                if 'E_TEXTCTRL_Eff_On_Start=' not in settings:
                    import re
                    brightness=re.search(r'E_SLIDER_Brightness=(\d+)',settings)
                    level=int(brightness[1]) if brightness else 100
                    settings+=f',E_TEXTCTRL_Eff_On_Start={level},E_TEXTCTRL_Eff_On_End={level}'
                if 'C_CHECKBOX_Palette1' not in palette:palette+=',C_CHECKBOX_Palette1=1'
                provenance={k:v for k,v in effect.attrib.items() if k.startswith('source')}
                sequence.effect(model,part,int(effect.get('startTime')),int(effect.get('endTime')),'#FFFFFF',
                                settings=settings,palette=palette,provenance=provenance,layer=1)
                source_count+=1
    if source_count!=report['visual_placement_count']:raise ValueError('Native drummer adapter omitted source visual placements')
    return report


def add_performers(seq,analysis,vocals):
    frames=seq.duration//50
    mouths=np.full(frames,'REST',dtype='<U4')
    for event in vocals['mouths']:
        a,b=event['start_ms']//50,min(frames,event['end_ms']//50)
        mouths[a:b]=event['phoneme']
    for model in seq.g.models:
        if model.details.get('canonical_drummer'):
            # Source-colored idle wire artwork below the unchanged strike lanes.
            for shade,color in [('BLUE','#308CC1'),('RED','#C83D31'),('GREEN','#52B766'),('GOLD','#DDB52E'),('NEUTRAL','#A8BAC6')]:
                part='IDLE_'+shade
                if part in model.submodels:seq.effect(model,part,0,seq.duration,color,52 if shade!='NEUTRAL' else 35)
            continue
        role=model.details.get('performer')
        if not role:
            for part in ('STRAND_A','STRAND_B','RUNGS') if model.details.get('double_helix') else ('SECTOR_00','SECTOR_01','SECTOR_02','SECTOR_03','SECTOR_04','SECTOR_05','SECTOR_06','SECTOR_07'):
                if part in model.submodels:
                    seq.effect(model,part,0,seq.duration,model.colors[model.submodels[part][0]-1],25)
                    for event in analysis['bass']:
                        seq.effect(model,part,event['start_ms'],event['start_ms']+180,model.colors[model.submodels[part][0]-1],70,25,layer=1,
                                   provenance={'sourceStem':'bass','sourceMethod':'stem_onset'})
                    # Word-timed keyword cues reuse the existing lyric lexicon.
                    for hit in vocals.get('lyric_interpretation',{}).get('trigger_hits',[]):
                        color='#FFF0BA' if hit['trigger_type'] in ('impact','light_bright') else '#A494FF'
                        seq.effect(model,part,hit['start_ms'],hit['start_ms']+350,color,85,25,layer=2,
                                   provenance={'sourceMethod':'existing_lyric_trigger_lexicon','sourceWord':hit['word']})
            continue
        for part,nodes in model.submodels.items():
            if part.startswith(('MOUTH_','ARM_','FRET_','STRING_','KEY_','HELIX_')):continue
            seq.effect(model,part,0,seq.duration,model.colors[nodes[0]-1],80 if part not in ('BASE','TORSO','HEAD') else 62)
        vocal_role=role in ('singer','female_singer','tree','bulb','pumpkin','snowman')
        if vocal_role:
            changes=np.r_[0,np.flatnonzero(mouths[1:]!=mouths[:-1])+1,frames]
            for a,b in zip(changes[:-1],changes[1:]):
                seq.effect(model,'MOUTH_'+mouths[a],int(a*50),int(b*50),'#FFA6B6',75 if mouths[a]!='REST' else 35,
                           provenance={'sourceMethod':'whisper_word_timing_cmu_allocated_phone','sourcePhoneme':str(mouths[a])})
            active=(mouths!='REST').astype(np.uint8)*90
            for rail,color in [('HELIX_A','#75E9FF'),('HELIX_B','#FF85CF')]:
                if rail in model.submodels:
                    for a,b,value in intervals(active):seq.effect(model,rail,a,b,color,60 if value else 14,
                                                                  provenance={'sourceStem':'vocals'})
        else:
            stem={'bassist':'bass','guitarist':'guitar','keyboardist':'piano'}[role]
            count=24 if role=='keyboardist' else 4 if role=='bassist' else 6
            active,notes=source_curves(analysis[stem],frames,count)
            for i,curve in enumerate(notes):
                part=('KEY_' if role=='keyboardist' else 'STRING_')+str(i)
                seq.effect(model,part,0,seq.duration,model.colors[model.submodels[part][0]-1],35)
                for a,b,value in intervals(curve):
                    if value:seq.effect(model,part,a,b,'#FFF3AF',value,layer=1,provenance={'sourceStem':stem,'sourceMethod':'dominant_pitch_proxy'})
            if role!='keyboardist':
                _,frets=source_curves(analysis[stem],frames,8)
                for i,curve in enumerate(frets):
                    for a,b,value in intervals(curve):
                        if value:seq.effect(model,'FRET_'+str(i),a,b,'#89FFE1',value,provenance={'sourceStem':stem})
            seq.effect(model,'MOUTH_REST',0,seq.duration,'#FFA6B6',30)
        if 'ARM_ACTIVE' in model.submodels:
            for a,b,value in intervals(active):
                seq.effect(model,'ARM_ACTIVE' if value else 'ARM_REST',a,b,'#B87937',75,
                           provenance={'sourceStem':'vocals' if vocal_role else stem,'sourceMethod':'source_bound_pose_hold'})
    return mouths


def timing_tracks(seq,vocals):
    from models.snowman_face_contract import SHAPE_TO_VISEME
    for label,rows in [('Lyrics',vocals['lines']),('Words',[dict(start_ms=round(w['start']*1000),end_ms=round(w['end']*1000),text=w['word']) for w in vocals['words']]),
                       ('Phonemes',[dict(start_ms=w['start_ms'],end_ms=w['end_ms'],text=w['phoneme']) for w in vocals['mouths']]),
                       ('xLights Visemes',[dict(start_ms=w['start_ms'],end_ms=w['end_ms'],text=SHAPE_TO_VISEME[w['phoneme']]) for w in vocals['mouths']])]:
        name='Helix '+label
        ET.SubElement(seq.root.find('DisplayElements'),'Element',{'type':'timing','name':name,'visible':'1','collapsed':'0'})
        e=ET.SubElement(seq.root.find('ElementEffects'),'Element',{'type':'timing','name':name,'fixed':'0'})
        if label=='xLights Visemes':
            # Native Faces reads phonemes from layer2: phrases, words, phonemes.
            for upstream in ('Helix Lyrics','Helix Words'):
                source=seq.root.find(f'./ElementEffects/Element[@name="{upstream}"]/EffectLayer')
                first=ET.SubElement(e,'EffectLayer')
                for event in source.findall('Effect'):ET.SubElement(first,'Effect',dict(event.attrib))
        layer=ET.SubElement(e,'EffectLayer')
        for row in rows:
            if row['end_ms']>row['start_ms']:ET.SubElement(layer,'Effect',{'label':row['text'],'startTime':str(row['start_ms']),'endTime':str(row['end_ms'])})


def export(row,variant,root):
    analysis_dir=root/'analysis'/row['id'];analysis=json.loads((analysis_dir/'instruments.json').read_text());vocals=json.loads((analysis_dir/'vocals.json').read_text())
    if any(d['audio_sha256']!=sha(row['path']) for d in (analysis,vocals)):raise ValueError('Source identity mismatch')
    g=build_ensemble(variant);g.concept_id='1'
    folder=root/'shows'/(row['id']+'_'+variant);manifest=write_layout(g,folder)
    for name in ('drummer_idle.png','drummerbg.png'):shutil.copy2(ROOT/'fixtures/band_geometry/source'/name,folder/'assets'/name)
    for model in g.models:_write_xml(model_xml(model,'custommodel'),folder/'models'/(model.name+'.xmodel'))
    write_html(g,folder)
    # Portable local media is copied only to the generated show, not git source.
    media=folder/'media';media.mkdir(exist_ok=True);shutil.copy2(row['path'],media/'song.mp3')
    seq=NativeSequence(g,row['duration'],'media/song.mp3',row['title'])
    seed=folder/'performance_seed.xsq';seq.write(seed)
    report=import_drummer(seq,seed,Path(row['path']),analysis_dir/'drums.json',folder/'drummer_injected.xsq')
    mouths=add_performers(seq,analysis,vocals);timing_tracks(seq,vocals)
    xsq=folder/(g.slug+'.xsq');seq.write(xsq)
    seed.unlink();(folder/'drummer_injected.xsq').unlink();(folder/(g.slug+'_Showcase.xsq')).unlink()
    for name in ('vocals.json','instruments.json','drums.json','embedded_lyrics.txt'):
        if (analysis_dir/name).exists():shutil.copy2(analysis_dir/name,folder/name)
    manifest.update(name=g.title,native_families=['Custom'],native_coverage_complete=False,
                    audio_source_sha256=row['sha256'],variant=variant,performer_count=6 if variant=='band' else 5,
                    singing_face_types=[] if variant=='band' else ['tree','bulb','pumpkin','snowman'])
    (folder/'showcase_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (folder/'drummer_report.json').write_text(json.dumps(report,indent=2)+'\n')
    (folder/'README.txt').write_text(f'{g.title} / {row["title"]}\nSelect this folder as an xLights show. Open {xsq.name} and Render All.\n'
        'Native Custom geometry, 50ms Media sequence and relative original song media. No output controllers.\n'
        'Stationary replacement arm/mouth poses; no mechanical movement. Canonical drummer/source ranges preserved.\n'
        'Bass/guitar/piano: Demucs six-stem onsets and dominant pitch proxies. Drums: ADTOF through existing V3 mapping.\n'
        'Vocals: Whisper word timing; dictionary phones allocated within words. Review inferred lyrics/timing.\n'
        'Male/female singers share authored vocals, without claiming separated voice identity. Unknown toms abstain.\n'
        'Movies project actual native FSEQ values onto identical exported XYZ, with original audio; not GUI recordings.\n'
        'Faces are original helix interpretations of familiar categories, not exact branded vendor models or a sales ranking.\n')
    return g,xsq,manifest,mouths


class PerformanceView(ConceptView):
    def __init__(self,g,row,vocals,width=1280,height=720):
        super().__init__(g,width,height)
        # Positive depth is the foreground: looking down makes nearer floor
        # points lower on screen. Separate the front keyboard from rear drummer.
        points=np.vstack([m.points for m in g.models]);yaw,pitch=np.radians((8,16))
        x=points[:,0]*np.cos(yaw)-points[:,2]*np.sin(yaw)
        z=points[:,0]*np.sin(yaw)+points[:,2]*np.cos(yaw)
        y=points[:,1]*np.cos(pitch)-z*np.sin(pitch)
        scale=min(width*.88/np.ptp(x),height*.74/np.ptp(y))
        sx=np.rint(width/2+(x-(x.min()+x.max())/2)*scale).astype(int)
        sy=np.rint(height*.53-(y-(y.min()+y.max())/2)*scale).astype(int)
        locations=sy*width+sx
        self.order=np.argsort(locations,kind='stable');ordered=locations[self.order]
        self.starts=np.r_[0,np.flatnonzero(np.diff(ordered))+1];self.locations=ordered[self.starts]
        self.indices=(np.arange(len(points))[:,None]*3+np.arange(3))[self.order]
        self.base=Image.new('RGB',(width,height),'#07111D');draw=ImageDraw.Draw(self.base)
        draw.text((25,15),g.title,font=_font(25),fill='#ECF4FF')
        draw.text((25,48),row['title'],font=_font(17),fill='#A6CDE0')
        draw.text((25,height-22),'XLIGHTS NATIVE PERFORMANCE  /  SOURCE AUDIO  /  WORD-ALIGNED MOUTHS',font=_font(10),fill='#93B7C8')
        self.lines=vocals['lines'];self.lyric_starts=[line['start_ms'] for line in self.lines]

    def timed_frame(self,values,ms):
        frame=self.frame(values);draw=ImageDraw.Draw(frame)
        i=bisect.bisect_right(self.lyric_starts,ms)-1
        if i>=0 and ms<self.lines[i]['end_ms']:
            text=self.lines[i]['text'];font=_font(17)
            while draw.textlength(text,font=font)>self.width-70:text=text[:-4]+'…'
            draw.text((self.width/2,self.height-48),text,font=font,fill='#F1DFB9',anchor='mm')
        draw.text((self.width-95,20),f'{ms/1000:05.1f}s',font=_font(14),fill='#7A9CAD')
        return frame


def check_native(g,frames,mouths,analysis=None):
    coverage=[]
    for model in g.models:
        values=frames[:,model.start-1:model.start-1+model.channels]
        if values.max()==0:raise ValueError('Dark native model '+model.name)
        coverage.append(dict(model=model.name,lit_frames=int(np.any(values,axis=1).sum()),peak=int(values.max())))
        if model.details.get('performer') in ('singer','female_singer','tree','bulb','pumpkin','snowman'):
            union=set().union(*(set(model.submodels['MOUTH_'+s]) for s in ('REST','MBP','AH','EE','OH','FV','L')))
            # Independent scheduled-node vs native-node equality. Shared pixels
            # between mouth shapes are valid; inactive exclusive pixels stay off.
            for i,shape in enumerate(mouths):
                expected=set(model.submodels['MOUTH_'+shape])
                actual={node for node in union if np.any(values[i,(node-1)*3:node*3])}
                if actual!=expected:raise ValueError(f'Native mouth mismatch {model.name} frame {i}: {len(actual)} vs {len(expected)}')
        if analysis is not None and 'ARM_ACTIVE' in model.submodels:
            role=model.details['performer']
            if role in ('singer','female_singer'):expected=mouths!='REST'
            else:
                stem={'bassist':'bass','guitarist':'guitar','keyboardist':'piano'}[role]
                curve,_=source_curves(analysis[stem],len(frames),24 if role=='keyboardist' else 4 if role=='bassist' else 6)
                expected=curve>0
            other=set().union(*(set(ids) for part,ids in model.submodels.items() if not part.startswith('ARM_')))
            for part,state in [('ARM_ACTIVE',expected),('ARM_REST',~expected)]:
                exclusive=set(model.submodels[part])-other-set(model.submodels['ARM_REST' if part=='ARM_ACTIVE' else 'ARM_ACTIVE'])
                if not exclusive:raise ValueError('Pose lacks independently observable nodes')
                indices=np.array(sorted(exclusive))-1
                actual=np.any(values.reshape(len(frames),-1,3)[:,indices]>0,axis=(1,2))
                if not np.array_equal(actual,state):raise ValueError('Native source-bound arm hold mismatch '+model.name+'/'+part)
    return coverage


def soundtrack_check(original,movie):
    def samples(path):
        data=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar','8000','-f','f32le','-'])
        return np.frombuffer(data,dtype='<f4')
    a,b=samples(original),samples(movie);n=min(len(a),len(b))
    correlation=float(np.corrcoef(a[:n],b[:n])[0,1])
    if correlation<.97 or abs(len(a)-len(b))/8000>.12:raise ValueError('Soundtrack differs from original song')
    return dict(sample_rate=8000,original_samples=len(a),movie_samples=len(b),
                zero_offset_correlation=correlation,full_song_duration_matches=True)


def render(row,variant,root,xlights):
    folder=root/'shows'/(row['id']+'_'+variant)
    if (folder/'verification.json').exists():return json.loads((folder/'verification.json').read_text())
    g,xsq,manifest,mouths=export(row,variant,root)
    with (folder/'native_render.log').open('w') as log:
        subprocess.run([str(xlights),'--headless','-q','-s',str(folder.resolve()),'-od',str(folder.resolve()),str(xsq.resolve())],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
    frames,step=read_fseq(xsq.with_suffix('.fseq'))
    if step!=50 or frames.shape!=(len(mouths),manifest['channel_count']):raise ValueError('Unexpected native frames')
    coverage=check_native(g,frames,mouths,json.loads((root/'analysis'/row['id']/'instruments.json').read_text()))
    vocals=json.loads((root/'analysis'/row['id']/'vocals.json').read_text())
    view=PerformanceView(g,row,vocals);movie=folder/(row['id']+'_'+variant+'.mp4')
    proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','20','-i','-',
                           '-i',row['path'],'-map','0:v','-map','1:a','-t',f'{len(frames)/20:.3f}',
                           '-c:v','libx264','-preset','veryfast','-crf','21','-threads','1','-pix_fmt','yuv420p',
                           '-c:a','aac','-b:a','192k','-movflags','+faststart',str(movie)],stdin=subprocess.PIPE)
    try:
        for i,values in enumerate(frames):
            frame=view.timed_frame(values,i*50)
            if i in (100,len(frames)//3,len(frames)*2//3):frame.save(folder/f'preview_{i:05}.png')
            proc.stdin.write(frame.tobytes())
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('MP4 encoding failed')
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    if int(video['nb_frames'])!=len(frames) or video['pix_fmt']!='yuv420p' or audio['codec_name']!='aac':raise ValueError('Movie contract mismatch')
    subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True,timeout=180)
    soundtrack=soundtrack_check(row['path'],movie)
    proof=dict(id=row['id'],title=row['title'],variant=variant,show_folder=str(folder),movie=str(movie),
               source_sha256=row['sha256'],native_frames=len(frames),frame_ms=step,native_models=coverage,
               native_mouth_nodes_match=True,source_drummer_sha256=sha(ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel'),
               native_arm_pose_holds_match=True,
               duration_s=len(frames)/20,video=dict(codec='h264',pixel_format='yuv420p',fps=20,width=1280,height=720,full_decode='pass',audio_codec='aac'),
               hashes={p.name:sha(p) for p in (xsq,xsq.with_suffix('.fseq'),movie,folder/'xlights_rgbeffects.xml')},
               soundtrack=soundtrack,
               musical_acceptance='inferred_performance_pending_user_listening')
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('RENDER_READY',row['id'],variant,movie,flush=True)
    return proof


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--xlights',type=Path,required=True);p.add_argument('--ids',nargs='*');p.add_argument('--variant',choices=['band','faces','both'],default='both')
    a=p.parse_args();rows=json.loads((a.root/'sources.json').read_text());proof=[]
    for row in sorted(rows,key=lambda r:(r['id']!='04',r['id'])):
        if a.ids and row['id'] not in a.ids:continue
        variants=['band','faces'] if a.variant=='both' and not row['previous'] else ['band'] if a.variant=='both' else [a.variant]
        for variant in variants:proof.append(render(row,variant,a.root.resolve(),a.xlights.resolve()))
    (a.root/'render_verification.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
