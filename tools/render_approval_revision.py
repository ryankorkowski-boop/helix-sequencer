"""Render exactly two revised snowman bands and two six-layout comparisons."""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess,time,uuid
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from models.review_snowman_scene import ReviewSnowmanScene
from tools.review_band_performance import ReviewBandPerformance
from tools.render_intricate_band_samplers import SamplerView,SAMPLER_VERTEX
from tools.render_refined_helix_band import encoder,physical_hits,DynamicDry,REFINED_FRAGMENT
from animation.articulated_source_drummer import ArticulatedDrummer
from core.output_provenance import brand_frame,stamp_mp4
from music.review_score import spatial_score

LAYOUTS={'E03':'prismatic_orrery','E14':'woven_aurora'}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def setup(root,eid,*,scene_factory=None):
    row=next(x for x in json.loads((root/'sources/selected_excerpts.json').read_text()) if x['excerpt_id']==eid)
    audio=root/'sources'/eid/'audio.wav';scene=(scene_factory or ReviewSnowmanScene)(LAYOUTS.get(eid,'woven_aurora'))
    import soundfile as sf
    duration=float(sf.info(audio).duration)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Source audio has no positive finite duration')
    source=dict(id=eid,title=row['filename'],path=str(audio),sha256=sha(audio),duration=duration,
                drummer_xsq=str(root/'sources'/eid/'drummer.xsq'))
    performance=ReviewBandPerformance(source,scene,root/'analysis')
    return row,audio,scene,performance


def camera(eid,drummer3d=False):
    def apply(w,h,t):
        eye=(.3,6.0,20.0);target=(0,3.0,-.8);fov=46
        if eid=='E14' and 8<=t<16:eye=(.0,3.6,10);target=(0,2.0,1.2);fov=43
        elif 16<=t<23:eye=(6.8,4.5,7.3);target=(6.5,1.65,3.05);fov=43
        elif 23<=t<29:eye=(-6.5,4.4,6.8);target=(-6.55,1.7,1.8);fov=43
        if drummer3d and 29<=t<33:eye=(0,4.4,4);target=(0,1.8,-2.8);fov=43
        eye=np.asarray(eye,dtype='f4');eye[0]+=.09*np.sin(t*.15)
        forward=np.asarray(target)-eye;forward/=np.linalg.norm(forward)
        right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
        view=np.eye(4,dtype='f4');view[:3,:3]=np.vstack((right,up,-forward));view[:3,3]=-view[:3,:3]@eye
        f=1/math.tan(math.radians(fov)/2);p=np.zeros((4,4),'f4');p[0,0]=f/(w/h);p[1,1]=f
        p[2,2]=-(100+.1)/(100-.1);p[2,3]=-2*100*.1/(100-.1);p[3,2]=-1
        return p@view,eye
    return apply


def band(root,eid,frames=720,*,scene_factory=None):
    row,audio,scene,p=setup(root,eid,scene_factory=scene_factory);folder=root/'videos';folder.mkdir(exist_ok=True)
    path=folder/(('01' if eid=='E03' else '02')+'_'+eid+'_Snowman_Band.mp4')
    shader=REFINED_FRAGMENT.replace(
        'c=color*(0.07+diffuse*0.10+(0.20+energy)*(.26+.74*wave))+color*sparkle*energy*.60;',
        'c=color*(.022+.90*energy)+color*sparkle*energy*.12;')
    view=SamplerView(scene,1280,720,SAMPLER_VERTEX.replace('activity[128]','activity[192]'),shader)
    view.camera_callback=camera(eid,hasattr(scene,"configure_drummer"))
    player=ArticulatedDrummer(physical_hits(root/'sources'/eid/'drummer.xsq'),natural_arms=True,cache_lighting=True)
    view.dry=DynamicDry(player)
    if hasattr(scene,"configure_drummer"):
        class NoSprite:
            time=0
            def frame(self,*args):return Image.new("RGBA",(395,256))
        view.dry=NoSprite()
    temp=path.with_name(path.stem+'.'+uuid.uuid4().hex+'.rendering.mp4');writer=encoder(temp,1280,720,20,audio,0,frames/20)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    began=time.monotonic();contacts=[];keys=[];mouths=[];poses=[];drum_contacts=[];snap=root/'diagnostics'/path.stem;snap.mkdir(parents=True,exist_ok=True)
    try:
        for i in range(frames):
            levels=p.pose(i);view.dry.time=i/20
            drum_contacts.extend(getattr(scene,"drum_contact_proof",[]))
            image=view.frame(levels,p.drums[i],p.strikes[i],p.hands[i],i/20,i/20)
            d=ImageDraw.Draw(image);d.rectangle((0,0,1280,45),fill='#08131E')
            d.text((18,10),'HELIX  /  '+Path(row['filename']).stem,font=font,fill='#DEEAF4')
            d.rectangle((0,682,1280,720),fill='#08131E')
            d.text((18,692),f'7 SNOWMEN  •  Separate keyboard + mallets  •  Source {row["start_seconds"]+i/20:06.2f}s',font=small,fill='#C0D5DE')
            image=brand_frame(image);writer.stdin.write(image.tobytes())
            for hit in p.mallet_schedule:
                if abs(hit['time']-i/20)<1e-7:
                    error=float(np.linalg.norm(p.mallet_targets[hit['side']][1]-(scene.bars[hit['pitch']]+(0,.0275+.057,0))))
                    contacts.append(dict(frame=i,pitch=hit['pitch'],side=hit['side'],error=error))
            for side in ('left','right'):
                pitch=p.key_assignments[side][i]
                if pitch is not None:
                    tip=p.hand_targets['piano',side]
                    key=next(o for o in scene.instances if o['name']==f'piano_key_{pitch}')
                    contact=key['matrix'][:3,3]+(0,.035,0)
                    mitten_contact=tip+(0,-.075,-.065)
                    changed=i==0 or p.key_assignments[side][i-1]!=pitch
                    keys.append(dict(frame=i,side=side,pitch=pitch,source_contact_change=changed,
                        error=float(np.linalg.norm(mitten_contact-contact))))
            mouths.append(dict(frame=i,source_clock_index=i*5,shape=int(p.voice_lanes[i,0]),energy=float(p.voice_energy[i,0]),
                aperture=float(next(o for o in scene.instances if o.get('mouth_role')=='lead')['matrix'][1,1])))
            if i in (40,200,360,500,680):image.save(snap/f'frame_{i:04}.jpg',quality=93)
            if i%180==0:print('BAND',eid,i,frames,round(time.monotonic()-began,1),flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();temp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
        view.close()
    if writer.wait():raise RuntimeError('Band encoding failed')
    temp.replace(path);stamp_mp4(path)
    proof=dict(file=str(path.relative_to(root)),excerpt_id=eid,sha256=sha(path),excerpt_sha256=sha(audio),
        original_audio_sha256=row['sha256'],source_start=row['start_seconds'],source_end=row['end_seconds'],
        frames=frames,fps=20,seconds=frames/20,all_snowmen=True,visible_roles=list(scene.visible_roles),
        keyboard_events=len(p.keyboard_events),mallet_contacts=contacts,keyboard_contacts=keys,
        mallet_motion_omissions=p.mallet_motion_omissions,mouth_frames=mouths,stage_score=p.stage_proof,
        drummer_motion_rejections=[] if hasattr(scene,'configure_drummer') else player.motion_rejections,
        volumetric_drummer=hasattr(scene,'configure_drummer'),drummer_contacts=drum_contacts,source_pitch_identity_verified=False,
        exact_phonemes_verified=False,independent_backing_singer_verified=False,renderer_sha256=sha(Path(__file__)))
    path.with_suffix('.render.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('BAND_COMPLETE',path.name,flush=True)
    return path


def comparison(root,eid):
    from models.showcase_flavors import FLAVORS,build_flavor
    from tools.review_channel_export import export_channels
    from tools.showcase_audio_preview import NativeSongView
    from tools.fseq_pixel_preview import FseqReader
    row,audio,scene,p=setup(root,eid);views=[];evidence=[]
    for variant,flavor in enumerate(FLAVORS[1:],1):
        g=build_flavor(flavor.key);positions=[np.mean(m.points,axis=0) for m in g.models];roles=[]
        for j,m in enumerate(g.models):
            if m.details.get('double_helix'):role=2
            elif m.details.get('spiral_tree'):role=1 if j%3 else 2
            elif any(x in m.zone for x in ('RIBBON','PATH','PROMENADE')):role=0
            elif any(x in m.display for x in ('Star','Spinner','Snowflake')):role=5
            else:role=j%6
            roles.append(role)
        score,proof=spatial_score(p,positions,roles,variant);score[[j for j,m in enumerate(g.models) if m.kind!='pixel']]=0
        folder=root/'channel_sequences'/eid/flavor.key;fseq=export_channels(g,score,folder)
        reader=FseqReader(fseq);view=NativeSongView(g,'',640,450,halo_scale=2,yaw=7,pitch=18)
        background=np.asarray(view.base).copy()
        background[:72]=background[:72,:1];background[405:]=background[405:,:1]
        view.base=Image.fromarray(background);view.scene_base=view.base.crop(view.box)
        views.append((view,iter(reader.iter_frames())))
        proof.update(flavor=flavor.key,fseq_sha256=sha(fseq),layout_sha256=sha(folder/'xlights_rgbeffects.xml'),
                     all_control_channels_dark=True,native_xlights_rendered=False)
        evidence.append(proof);(folder/'score_proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    bandpath=root/'videos'/(('01' if eid=='E03' else '02')+'_'+eid+'_Snowman_Band.mp4')
    bandproof=json.loads(bandpath.with_suffix('.render.json').read_text())
    if bandproof['sha256']!=sha(bandpath) or bandproof['excerpt_sha256']!=sha(audio) or bandproof['frames']!=720:raise ValueError('band panel is not completed/source-bound')
    movie=root/'videos'/(('03' if eid=='E03' else '04')+'_'+eid+'_Six_Layout_Comparison.mp4')
    decoder=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-i',str(bandpath),'-an','-vf','scale=640:360','-pix_fmt','rgb24','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    temp=movie.with_name(movie.stem+'.'+uuid.uuid4().hex+'.rendering.mp4');writer=encoder(temp,1920,1080,20,audio,0,36)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21)
    snap=root/'diagnostics'/movie.stem;snap.mkdir(parents=True,exist_ok=True)
    try:
        for i in range(720):
            image=Image.new('RGB',(1920,1080),'#07111D');d=ImageDraw.Draw(image)
            d.text((24,22),'HELIX / SIX DISTINCT LAYOUTS / '+Path(row['filename']).stem,font=font,fill='#E0ECF6')
            raw=decoder.stdout.read(640*360*3)
            if len(raw)!=640*360*3:raise ValueError('Band panel decode ended early')
            panel=Image.new('RGB',(640,450),'#08131F');panel.paste(Image.frombytes('RGB',(640,360),raw),(0,50))
            panels=[panel]+[view.frame(np.frombuffer(next(frames),'u1')) for view,frames in views]
            names=[('Prismatic' if eid=='E03' else 'Woven Aurora')+' Snow Band']+[f.title for f in FLAVORS[1:]]
            for k,(panel,name) in enumerate(zip(panels,names)):
                draw=ImageDraw.Draw(panel);draw.rectangle((0,0,640,36),fill='#0E1C2A');draw.text((12,6),name,font=small,fill='#DBECF5')
                image.paste(panel,((k%3)*640,88+(k//3)*450))
            d=ImageDraw.Draw(image);d.text((24,1020),f'{eid} / Source {row["start_seconds"]+i/20:06.2f}s / One soundtrack clock / Independent source-scored groups',font=small,fill='#B7CCD9')
            image=brand_frame(image);writer.stdin.write(image.tobytes())
            if i in (40,200,360,500,680):image.save(snap/f'frame_{i:04}.jpg',quality=93)
            if i%180==0:print('COMPARISON',eid,i,720,flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();decoder.terminate();decoder.wait();temp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
    if writer.wait() or decoder.wait():raise RuntimeError('Comparison encoding/decoding failed')
    temp.replace(movie);stamp_mp4(movie)
    proof=dict(file=str(movie.relative_to(root)),excerpt_id=eid,sha256=sha(movie),excerpt_sha256=sha(audio),
        original_audio_sha256=row['sha256'],source_start=row['start_seconds'],source_end=row['end_seconds'],
        frames=720,fps=20,seconds=36,panels=6,all_panels_same_source_clock=True,
        channel_output='Helix-generated FSEQ v2; native xLights import/render not exercised in this revision',
        layouts=evidence,band_panel_sha256=sha(bandpath),renderer_sha256=sha(Path(__file__)))
    movie.with_suffix('.render.json').write_text(json.dumps(proof,indent=2)+'\n');print('COMPARISON_COMPLETE',movie.name,flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--mode',choices=['band','comparison'],required=True);a.add_argument('--id',choices=['E03','E14'],required=True);a.add_argument('--frames',type=int,default=720);args=a.parse_args()
    (band(args.root.resolve(),args.id,args.frames) if args.mode=='band' else comparison(args.root.resolve(),args.id))
