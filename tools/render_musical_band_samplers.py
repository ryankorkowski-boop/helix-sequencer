"""Four source-bound full-band samplers, with musical windows and distinct stages.

Example: python -m tools.render_musical_band_samplers --pilot
The renderer consumes restored source caches; it never alters audio or core scores.
"""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import ImageDraw
from models.refined_band_scene import RefinedBandScene
from models.intricate_band_scene import LAYOUTS
from models.musical_band_response import choose_solo_windows
from tools.musical_band_performance import MusicalBandPerformance
from tools.render_intricate_band_samplers import SamplerView,SAMPLER_VERTEX
from tools.render_refined_helix_band import encoder,physical_hits,DynamicDry,REFINED_FRAGMENT,FONT,SMALL
from animation.articulated_source_drummer import ArticulatedDrummer
from models.drummer_review_schedule import decode_review_schedule
from tools.render_drummer_v3_preview import TARGETS,parse_effects,parse_snare_hands,_active_targets_for_frame,snare_hand_for_frame
from tools.readable_band_performance import ROOT

OUT=ROOT/'outputs/Musical_Band_20261013'
ANALYSIS=ROOT/'outputs/Band_Logic_Reassessment/analysis'
STAGES=('prismatic_orrery','woven_aurora','cymatic_geode','quasicrystal_theatre')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_plan():
    rows={r['id']:r for r in json.loads((ROOT/'outputs/Snowman_Ensemble/sources.json').read_text())}
    windows={}
    for id in ('01','02','05'):
        with np.load(ANALYSIS/id/'performance_curves.npz') as a:
            windows[id]=choose_solo_windows(a['guitar_energy'],a['vocal_energy'],seconds=14,count=4)
    # Four arrangements of real musical windows. Weak third/fourth choices
    # reuse a strong solo with a different start instead of claiming one exists.
    variants=[(('01',106.0),('02',10.2),('05',96.55)),
              (('05',0.0),('02',24.15),('01',101.0)),
              (('02',96.3),('01',106.0),('05',97.0)),
              (('05',0.0),('01',102.5),('02',211.65))]
    plans=[]
    for j,(stage,solo) in enumerate(zip(STAGES,variants)):
        segments=[dict(id='dry',title='Dry Drum Test',start=float(j*3),seconds=8.,purpose='drum opening')]
        segments += [dict(id=id,title=rows[id]['title'],start=start,seconds=14.,purpose='guitar-forward musical passage') for id,start in solo]
        segments.append(dict(id='00',title='Wire Tree',start=196.0,seconds=28.2,purpose='last full chorus ending'))
        plans.append(dict(version=j+1,stage=stage,stage_title=LAYOUTS[stage],segments=segments))
    return rows,plans,windows


def soundtrack(segments,rows,path):
    chunks=[];rate=44100;evidence=[]
    for seg in segments:
        src=ROOT/'evidence/drummer/dry_drum_test.wav' if seg['id']=='dry' else ROOT/'outputs/Snowman_Ensemble/shows'/(seg['id']+'_band')/'media/song.mp3'
        if seg['id']!='dry' and sha(src)!=rows[seg['id']]['sha256']:raise ValueError('audio hash mismatch')
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(src),'-ss',str(seg['start']),'-t',str(seg['seconds']),'-ac','2','-ar',str(rate),'-f','f32le','-'])
        a=np.frombuffer(raw,dtype='<f4').reshape(-1,2).copy();wanted=round(seg['seconds']*rate)
        if len(a)<wanted-1:raise ValueError('excerpt exceeds source')
        a=a[:wanted]
        if len(a)<wanted:a=np.pad(a,((0,wanted-len(a)),(0,0)))
        # Ten-millisecond edge de-clicks; no time stretch, overlap, or resampling
        # beyond the common 44.1kHz soundtrack rate.
        edge=441;a[:edge]*=np.linspace(0,1,edge)[:,None];a[-edge:]*=np.linspace(1,0,edge)[:,None]
        chunks.append(a);evidence.append(dict(seg,source_sha256=sha(src),samples=wanted,edge_fade_ms=10))
    sf.write(path,np.vstack(chunks),rate,subtype='PCM_16')
    return evidence


def silent_performance(perf):
    for key,array in perf.curves.items():
        array[:]=-1 if key.endswith(('_notes','_routes')) else 1 if key.endswith('_phase') else 0
    perf.voice_lanes[:]=0;perf.voice_energy[:]=0;perf.mallet_schedule=[]
    for val in perf.directions.values():val[:]=0
    for kind in perf.fret_targets:
        rig=next(r for r in perf.scene.rigs if r['role']==kind and r['side']=='finger')
        perf.fret_targets[kind][:]=rig['hand']
    for side in perf.key_hand_targets:
        rig=next(r for r in perf.scene.rigs if r['role']=='piano' and r['side']==side)
        perf.key_hand_targets[side][:]=rig['hand']
    return perf


def render(plan,rows,casting,pilot=False,width=1280,height=720):
    OUT.mkdir(parents=True,exist_ok=True);name=f'Helix_Band_{plan["version"]}_{plan["stage"]}'
    if pilot:name+='_pilot'
    segments=[dict(s,seconds=min(2,s['seconds'])) for s in plan['segments']] if pilot else plan['segments']
    audio=OUT/(name+'.wav');audio_proof=soundtrack(segments,rows,audio)
    duration=sum(s['seconds'] for s in segments);movie=OUT/(name+'.mp4');temp=movie.with_suffix('.rendering.mp4')
    writer=encoder(temp,width,height,20,audio,0,duration);proof=[];timeline=0.;total=0
    try:
        for seg in segments:
            row=rows['00'] if seg['id']=='dry' else rows[seg['id']]
            scene=RefinedBandScene(plan['stage'],(48,96),neutral_performers=True);perf=MusicalBandPerformance(row,scene,ANALYSIS,casting.get(row['id']))
            native=ROOT/'outputs/Snowman_Ensemble/shows'/(row['id']+'_band')/'Snowman_Band.xsq'
            if seg['id']=='dry':
                perf=silent_performance(perf)
                native=ROOT/'evidence/drummer_shoulder_revision/Helix_Drummer_DRY_TEST_ONLY.xsq'
                count=math.ceil(sf.info(ROOT/'evidence/drummer/dry_drum_test.wav').duration*20)
                drums=np.zeros((count,8),np.float32);strikes=np.zeros_like(drums);hands=np.zeros(count,np.int8)
                effects=parse_effects(native);hand_schedule=parse_snare_hands(native)
                for i in range(count):
                    for target in _active_targets_for_frame(effects,i*50,20):drums[i,TARGETS.index(target)]=1
                    strikes[i]=drums[i];hands[i]=int(snare_hand_for_frame(hand_schedule,i*50,20)=='right')
            else:drums,strikes,hands=perf.drums,perf.strikes,perf.hands
            player=ArticulatedDrummer(physical_hits(native),natural_arms=True)
            view=SamplerView(scene,width,height,SAMPLER_VERTEX.replace('activity[128]','activity[192]'),REFINED_FRAGMENT)
            view.dry=DynamicDry(player);offset=round(seg['start']*20);n=round(seg['seconds']*20)
            limb_lengths=[];contacts=[];mouth_frames=[0,0];max_contact_error=0
            try:
                for frame in range(n):
                    source_index=offset+frame;idx=0 if seg['id']=='dry' else source_index
                    levels=perf.pose(idx);levels[5:13]=drums[source_index]
                    if seg['id']=='dry':
                        for k in range(48):levels[64+k]=.12+.65*max(strikes[source_index])
                    view.dry.time=source_index/20
                    image=view.frame(levels,drums[source_index],strikes[source_index],hands[source_index],source_index/20,(timeline+frame/20)%42)
                    d=ImageDraw.Draw(image);d.rectangle((0,0,width,46),fill='#07101C')
                    d.text((18,12),f'HELIX BAND {plan["version"]}  |  {plan["stage_title"]}  |  {seg["title"]}',font=FONT,fill='#DDF5FF')
                    d.rectangle((0,height-35,width,height),fill='#07101C')
                    label='Drummer • Bass • Guitar • Keys • Bells / Marimba • Singers'
                    d.text((18,height-26),label,font=SMALL,fill='#C6D7DD')
                    from core.output_provenance import brand_frame
                    writer.stdin.write(brand_frame(image).tobytes());total+=1
                    for key,(s,e,h) in perf.joint_targets.items():limb_lengths.append((str(key),float(np.linalg.norm(e-s)),float(np.linalg.norm(h-e))))
                    for k in (0,1):mouth_frames[k]+=int(perf.voice_lanes[idx,k]!=0)
                    for side,joint in player.last_joints.items():
                        assert np.all(np.isfinite(np.r_[joint['shoulder'],joint['elbow'],joint['wrist'],joint['tip']]))
                    for hit in perf.mallet_schedule:
                        if abs(hit['time']-idx/20)<1e-7:
                            hand,tip=perf.mallet_targets[hit['side']]
                            expected=scene.bars[hit['pitch']]+(0,.0275+.057,0)
                            error=float(np.linalg.norm(tip-expected));max_contact_error=max(max_contact_error,error)
                            contacts.append(dict(source_time=hit['time'],pitch=hit['pitch'],error=error))
                    if frame in (0,min(n-1,round(n*.5))):image.save(OUT/f'{name}_{seg["id"]}_{frame:04d}.png')
                    if frame%200==0:print(name,seg['id'],frame,n,flush=True)
            finally:view.close()
            proof.append(dict(seg,frames=n,casting=perf.casting,mouth_active_frames=mouth_frames,
                mallet_proof=perf.mallet_proof,mallet_contacts=contacts,max_mallet_contact_error=max_contact_error,
                keyboard_note_events=len(perf.keyboard_events),guitar_events_unchanged=True,
                natural_drum_arms=True,source_xsq_sha256=sha(native),drum_motion_rejections=len(player.motion_rejections),
                rendered_hand_reassignments=len(player.hand_reassignments),limb_lengths=limb_lengths[::max(1,len(limb_lengths)//40)]))
            timeline+=seg['seconds']
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();temp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
    if writer.wait():raise RuntimeError('sampler encoding failed')
    temp.replace(movie)
    from core.output_provenance import stamp_mp4
    stamp_mp4(movie)
    result=dict(plan=plan,pilot=pilot,seconds=duration,frames=total,fps=20,resolution=[width,height],
        movie_sha256=sha(movie),audio_sha256=sha(audio),soundtrack=audio_proof,segments=proof,
        scene_members=['drummer','bass','guitar','keyboard','xylophone / bells / marimba','singer A','singer B'],
        neutral_singers=True,neutral_mallet_player=True,visible_watermark=True,visible_helix_watermark=True,internal_helix_credit=True,
        continuous_animation_output='video/pixel matrix',physical_prop_channel_export=False,
        instrument_detection_score_independently_verified=False,singer_assignment_listening_verified=False)
    movie.with_suffix('.verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return movie


def main():
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--version',type=int,choices=range(1,5));p.add_argument('--casting',type=Path);p.add_argument('--width',type=int,default=1280);p.add_argument('--height',type=int,default=720)
    args=p.parse_args();rows,plans,windows=build_plan();OUT.mkdir(parents=True,exist_ok=True)
    casting=json.loads(args.casting.read_text()) if args.casting else {}
    (OUT/'audio_selection.json').write_text(json.dumps(dict(plans=plans,ranked_guitar_windows=windows,selection='measured guitar-forward windows; not a verified guitar solo score'),indent=2)+'\n')
    for plan in plans:
        if args.version and plan['version']!=args.version:continue
        print(render(plan,rows,casting,args.pilot,args.width,args.height),flush=True)


if __name__=='__main__':main()
