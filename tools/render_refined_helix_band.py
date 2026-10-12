"""Actual Helix source-art/GL performance previews; historical renderer remains intact."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont
from animation.articulated_source_drummer import ArticulatedDrummer,BandLighting
from tools.render_drummer_v3_preview import (TARGETS,LABELS,parse_effects,parse_snare_hands,parse_cymbal_hits,
    load_component_masks,compose_lighting,_active_targets_for_frame,snare_hand_for_frame)
from animation.cymbal_lighting import cymbal_level
from tools.render_drummer_shoulder_preview import score_schedule,source_attacks
from models.refined_band_scene import RefinedBandScene
from tools.refined_band_performance import RefinedPerformance
from tools.readable_band_performance import STRING_FRAGMENT
from tools.render_intricate_band_samplers import SamplerView,SAMPLER_VERTEX,excerpt_audio_check,sha
from tools.render_readable_band import camera_for
from tools.readable_band_performance import ROOT

OUT=ROOT/'outputs/Band_Refinement_20261012'
ANALYSIS=ROOT/'outputs/Band_Logic_Reassessment/analysis'
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
SMALL=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)


def encoder(path,width,height,fps,audio,start,seconds):
    path.parent.mkdir(parents=True,exist_ok=True)
    return subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}',
        '-r',str(fps),'-i','-','-ss',str(start),'-i',str(audio),'-map','0:v','-map','1:a','-t',str(seconds),
        '-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
        '-movflags','+faststart',str(path)],stdin=subprocess.PIPE)


def physical_hits(xsq):
    root=ET.parse(xsq).getroot();unique=set();hits=[]
    # Native exported band schedules retain original sourceRole/sourceComponent.
    db=[e.text or '' for e in root.findall('./EffectDB/Effect')]
    for element in root.findall('./ElementEffects/Element'):
        for e in element.iter('Effect'):
            target=e.get('sourceComponent',element.get('name'))
            if target not in TARGETS or target==TARGETS[0]:continue
            role=e.get('sourceRole')
            if role and role!='visual_geometry':continue
            if e.get('sourcePose')=='shared_actuator_union':continue
            start=int(e.get('startTime'))/1000
            side=e.get('sourceHand') or ('right' if target in (TARGETS[2],TARGETS[3],TARGETS[7]) else 'left')
            key=(target,start,side)
            if key in unique:continue
            unique.add(key)
            setting=e.get('settings','') or (db[int(e.get('ref'))] if e.get('ref') else '')
            fields=dict(f.split('=',1) for f in setting.split(',') if '=' in f)
            velocity=float(fields.get('HELIX_DrummerIntensity','1'))
            hits.append(dict(time=start,target=target,side=side,velocity=velocity))
    return sorted(hits,key=lambda e:e['time'])


def dry(seconds=None,width=1280,height=720,fps=30,lighting=BandLighting()):
    audio=ROOT/'evidence/drummer/dry_drum_test.wav';xsq=ROOT/'evidence/drummer_shoulder_revision/Helix_Drummer_DRY_TEST_ONLY.xsq'
    duration=sf.info(audio).duration if seconds is None else seconds
    report=json.loads((ROOT/'evidence/drummer_shoulder_revision/dry_test_accepted_report.json').read_text())
    raw=json.loads((ROOT/'evidence/drummer/dry_drum_test_adtof.json').read_text())
    assert sha(audio)==raw['audio_sha256']==report['analysis']['audio_sha256']
    hits=physical_hits(xsq);scores=score_schedule(report,raw,source_attacks(audio))
    player=ArticulatedDrummer(hits,lighting);source,masks=load_component_masks()
    effects=parse_effects(xsq);hands=parse_snare_hands(xsq);cymbals,step=parse_cymbal_hits(xsq)
    movies=[OUT/'Video_A_Drummer_Geometry_Comparison.mp4',OUT/'Video_B_Original_Dry_Drum_Test.mp4']
    writers=[encoder(p,width,height,fps,audio,0,duration) for p in movies]
    proof=[];crop=(99,124,494,380)
    try:
        for frame in range(round(duration*fps)):
            time=frame/fps;active=_active_targets_for_frame(effects,time*1000,fps);hand=snare_hand_for_frame(hands,time*1000,fps)
            levels={target:cymbal_level(events,time*1000,frame_ms=step,nearest_ms=500/fps) for target,events in cymbals.items()}
            new=player.frame(time,active,levels).crop(crop).convert('RGB')
            old=compose_lighting(source,masks,active,snare_hand=hand,cymbal_levels=levels).crop(crop).convert('RGB')
            compare=Image.new('RGB',(width,height),'#070E18');d=ImageDraw.Draw(compare)
            size=(width//2-20,round((width//2-20)*256/395));y=(height-size[1])//2
            compare.paste(old.resize(size,Image.Resampling.LANCZOS),(10,y));compare.paste(new.resize(size,Image.Resampling.LANCZOS),(width//2+10,y))
            d.text((20,25),'Previous shoulder revision',font=FONT,fill='white');d.text((width//2+20,25),'Connected joints + recovery',font=FONT,fill='white')
            d.text((20,height-35),f'Identical original dry audio | {time:05.2f}s | source artwork and drum contacts preserved',font=SMALL,fill='#C2D2DF')
            canvas=Image.new('RGB',(width,height),'#070E18');size=(min(width-260,int((height-125)*395/256)),height-125)
            canvas.paste(new.resize(size,Image.Resampling.LANCZOS),(30,75));d=ImageDraw.Draw(canvas)
            d.text((30,20),'Helix drummer — original 38.32-second dry test',font=FONT,fill='white')
            for row,target in enumerate(TARGETS):
                recent=[e for e in scores if e['target']==target and 0<=time-e['timestamp']<.08]
                d.text((width-230,115+row*48),LABELS[target],font=SMALL,fill='#ECD9A8' if recent else '#8194A9')
                d.ellipse((width-250,118+row*48,width-239,129+row*48),fill='#EEDAA5' if recent else '#243342')
            unresolved=[e for e in scores if e['target'] is None and 0<=time-e['timestamp']<.08]
            d.text((30,height-35),f'{time:05.2f}s | unresolved events: {sum(e["target"] is None and e["timestamp"]<=time for e in scores)} | no guessed tom strokes',font=SMALL,fill='#B7C7D6')
            if unresolved:d.text((width-230,530),'UNRESOLVED',font=SMALL,fill='#E9D5A4')
            for writer,image in zip(writers,(compare,canvas)):writer.stdin.write(image.tobytes())
            proof.append(dict(frame=frame,time=time,active=list(active),joints={side:{k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in joints.items()} for side,joints in player.last_joints.items()}))
            if frame%300==0:print('dry',frame,round(duration*fps),flush=True)
    finally:
        for writer in writers:writer.stdin.close()
    assert all(writer.wait()==0 for writer in writers)
    result=dict(audio_sha256=sha(audio),duration=duration,fps=fps,physical_hits=len(hits),accepted_events=report['event_count'],
        family_predictions=len(raw['events']),unresolved=sum(e['target'] is None for e in scores),lighting=vars(player.lighting),rendered_physical_hits=len(player.hits),motion_rejections=player.motion_rejections,hand_reassignments=player.hand_reassignments,
        exact_ground_truth=False,source_xsq_sha256=sha(xsq),joint_frames=proof,score_schedule=scores,
        independent_source_novelty=source_attacks(audio))
    (OUT/'dry_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return movies

class DynamicDry:
    def __init__(self,player):self.player=player;self.time=0;self.proof={'opt_in_articulated_source_compositor':True}
    def frame(self,lighting,strikes,hand):
        active=[t for k,t in enumerate(TARGETS) if strikes[k]>0]
        image=self.player.frame(self.time,active,{TARGETS[k]:float(lighting[k]) for k in (6,7)})
        rgb=np.asarray(image.crop((99,124,494,380)).convert('RGB'))
        alpha=np.clip((rgb.max(axis=2).astype(float)-7)*22,0,255).astype('u1')
        return np.dstack((rgb,alpha))

REFINED_FRAGMENT=STRING_FRAGMENT.replace('0.17+0.82*diffuse','0.27+0.72*diffuse').replace(
    'if(channel>=64.0){','if(channel>=128.0){c=color*(.30+energy*.70); } else if(channel>=64.0){').replace(
    'c=color*(.055+energy*(.65+1.1*shimmer));','c=color*(.24+energy*(.35+.42*shimmer));')


def band(row,start,seconds,focus,name,width=1280,height=720,lighting=BandLighting()):
    scene=RefinedBandScene('prismatic_orrery');perf=RefinedPerformance(row,scene,ANALYSIS)
    view=SamplerView(scene,width,height,SAMPLER_VERTEX.replace('activity[128]','activity[192]'),REFINED_FRAGMENT)
    if focus=='xylophone':
        def mallet_camera(w,h,elapsed):
            import math
            eye=np.array((-6.45,5.6,6.1),dtype='f4');target=np.array((-6.55,1.75,1.7))
            forward=target-eye;forward/=np.linalg.norm(forward)
            right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
            v=np.eye(4,dtype='f4');v[:3,:3]=np.vstack((right,up,-forward));v[:3,3]=-v[:3,:3]@eye
            f=1/math.tan(math.radians(42)/2);near,far=.1,80
            p=np.zeros((4,4),dtype='f4');p[0,0]=f/(w/h);p[1,1]=f;p[2,2]=(far+near)/(near-far);p[2,3]=2*far*near/(near-far);p[3,2]=-1
            return p@v,eye
        view.camera_callback=mallet_camera
    else:view.camera_callback=camera_for(focus)
    native=ROOT/'outputs/Snowman_Ensemble/shows'/f'{row["id"]}_band'
    view.dry=DynamicDry(ArticulatedDrummer(physical_hits(native/'Snowman_Band.xsq'),lighting))
    movie=OUT/(name+'.mp4');audio=native/'media/song.mp3';assert sha(audio)==row['sha256']
    encoder_process=encoder(movie,width,height,20,audio,start,seconds);offset=round(start*20);n=round(seconds*20)
    pose_evidence=[]
    try:
        for frame in range(n):
            i=offset+frame;levels=perf.pose(i);view.dry.time=i/20
            image=view.frame(levels,perf.drums[i],perf.strikes[i],perf.hands[i],i/20,frame/20)
            d=ImageDraw.Draw(image);d.rectangle((0,0,width,46),fill='#07101C')
            d.text((20,13),f'Helix | {row["title"]} | {start:.2f}–{start+seconds:.2f}s | {focus}',font=FONT,fill='white')
            d.rectangle((0,height-36,width,height),fill='#07101C')
            label='Source-timed bass/guitar | connected drummer | warm idle lighting'
            if focus in ('stage','xylophone'):label+=' | mallet candidates: identity unverified'
            d.text((16,height-26),label,font=SMALL,fill='#BCCDDA')
            encoder_process.stdin.write(image.tobytes())
            assert all(np.isfinite(o['matrix']).all() for o in scene.instances)
            pose_evidence.append(dict(frame=frame,source_time=i/20,routes=perf.active_routes,
                hands={str(k):v.tolist() for k,v in perf.hand_targets.items()},mallets={side:[x.tolist() for x in positions] for side,positions in perf.mallet_targets.items()},
                source_attack={kind:float(perf.curves[kind+'_attack'][i]) for kind in ('bass','guitar')},
                bar_levels=levels[128:153].tolist()))
            if frame%100==0:print(name,frame,n,flush=True)
    finally:encoder_process.stdin.close();view.close()
    assert encoder_process.wait()==0
    result=dict(title=row['title'],id=row['id'],start=start,seconds=seconds,fps=20,frames=n,audio_sha256=sha(audio),
        mallet_proof=perf.mallet_proof,mallet_evidence=perf.mallet_evidence,mallet_contact_audit=perf.contact_audit,
        implementation='Helix source-event/GL scene + articulated source-art drummer',
        actual_listening_performed=False,verified_score=False,poses=pose_evidence,
        soundtrack=excerpt_audio_check(audio,movie,start,seconds),source_native_drummer=perf.drum_proof,
        sha256=sha(movie),bytes=movie.stat().st_size)
    movie.with_suffix('.verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return movie

JOBS=[('01',101,18,'guitar','C_Guitar_Who_Knew'),('02',115,18,'bass','C_Bass_49'),
      ('05',26,18,'xylophone','D_Pitched_Percussion_Candidates_Festivus'),
      ('00',164,18,'stage','E_Band_Wire_Tree'),('03',168,18,'stage','E_Band_Candy_Cane_Chaos'),
      ('05',26,18,'stage','E_Band_Festivus')]


def main():
    p=argparse.ArgumentParser();p.add_argument('--dry',action='store_true');p.add_argument('--job',type=int)
    p.add_argument('--pilot',action='store_true');p.add_argument('--idle-brightness',type=float,default=.72);p.add_argument('--strike-brightness',type=float,default=1.35)
    a=p.parse_args();lighting=BandLighting(idle_body=a.idle_brightness,strike=a.strike_brightness);OUT.mkdir(parents=True,exist_ok=True)
    if a.dry:dry(seconds=2 if a.pilot else None,lighting=lighting)
    if a.job is not None:
        id,start,seconds,focus,name=JOBS[a.job];row=next(r for r in json.loads((ROOT/'outputs/Snowman_Ensemble/sources.json').read_text()) if r['id']==id)
        band(row,start,2 if a.pilot else seconds,focus,name+('_pilot' if a.pilot else ''),lighting=lighting)

if __name__=='__main__':main()
