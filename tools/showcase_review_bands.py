"""New solo-band movies from final Helix rigs and source-bound performances."""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess,time,uuid
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from PIL import ImageDraw,ImageFont
from models.final_band_scene import FinalBandScene
from models.expressive_band_face import lip_ring_mesh
from tools.final_band_performance import FinalBandPerformance
from tools.render_intricate_band_samplers import SamplerView,SAMPLER_VERTEX
from tools.render_refined_helix_band import encoder,physical_hits,DynamicDry,REFINED_FRAGMENT
from tools.render_band_upgrade import GLView
from animation.articulated_source_drummer import ArticulatedDrummer
from core.output_provenance import brand_frame,stamp_mp4

STAGES=['glacier_pier','circuit_garage','cathedral_organ','ember_amphitheatre','lantern_garden','orbital_halo']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def camera(focus):
    config={'stage':((.6,5.2,16.2),(.8,2.1,-.2),44),
        'guitar':((5,3.5,8),(4,1.8,.2),42),'bass':((-4.6,3.5,7),(-4,1.8,.1),42),
        'drummer':((.1,3.6,7),(0,2.3,-1.5),40),'mallet':((6.7,4.2,7.4),(6.55,1.6,1.9),43),
        'vocals':((-.6,3.1,8.7),(0,2.05,1.5),43)}
    def apply(width,height,elapsed):
        selected=focus
        if focus=='tour':selected='stage' if elapsed<12 or elapsed>=30 else 'guitar' if elapsed<18 else 'mallet' if elapsed<24 else 'drummer'
        if focus=='vocal_tour':selected='stage' if elapsed<8 or elapsed>=28 else 'vocals' if elapsed<20 else 'guitar'
        eye0,target,fov=config[selected];eye=np.array(eye0,dtype='f4');eye[0]+=.15*np.sin(elapsed*.15)
        forward=np.asarray(target)-eye;forward/=np.linalg.norm(forward)
        right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
        v=np.eye(4,dtype='f4');v[:3,:3]=np.vstack((right,up,-forward));v[:3,3]=-v[:3,:3]@eye
        f=1/math.tan(math.radians(fov)/2);near,far=.1,100
        p=np.zeros((4,4),dtype='f4');p[0,0]=f/(width/height);p[1,1]=f;p[2,2]=(far+near)/(near-far);p[2,3]=2*far*near/(near-far);p[3,2]=-1
        return p@v,eye
    return apply


class SoloView(SamplerView):
    def __init__(self,scene,width,height):
        super().__init__(scene,width,height,SAMPLER_VERTEX.replace('activity[128]','activity[192]'),REFINED_FRAGMENT)
        objects=[o for o in scene.instances if o['kind']=='lip_ring']
        if objects:self.groups.append(GLView.make_vao(self,lip_ring_mesh(),objects))


def render(args):
    root,row,stage,rock,focus,category,number,seconds=args;root=Path(root);eid=row['excerpt_id']
    folder=root/'07_Layouts_and_Sequences'/eid;audio=folder/'audio.wav';analysis=root/'analysis'/eid
    out=root/category;out.mkdir(parents=True,exist_ok=True)
    slug=''.join(c if c.isalnum() else '_' for c in Path(row['filename']).stem).strip('_')[:52]
    name=f'{number:02d}_{eid}_{slug}_{"Rock" if rock else "Snow"}'
    movie=out/(name+'.mp4');proofpath=movie.with_suffix('.render.json')
    inputs={p.name:sha(p) for p in analysis.glob('*') if p.suffix in ('.json','.npz')}
    config=dict(stage=stage,rock=rock,focus=focus,seconds=seconds,resolution=[1280,720],fps=20,inputs=inputs,
        renderer_sha256=sha(Path(__file__)),decoder_sha256=sha(Path(__file__).resolve().parents[1]/'models/drummer_review_schedule.py'))
    config['scene_sha256']=sha(Path(__file__).resolve().parents[1]/'models/final_band_scene.py')
    if proofpath.exists() and movie.exists():
        old=json.loads(proofpath.read_text())
        if old['config']==config and old['sha256']==sha(movie):return old
    scene=FinalBandScene(stage,rock=rock)
    source=dict(id=eid,title=row['filename'],path=str(audio),sha256=sha(audio),duration=36,drummer_xsq=str(folder/'drummer.xsq'))
    perf=FinalBandPerformance(source,scene,root/'analysis')
    view=SoloView(scene,1280,720);view.camera_callback=camera(focus)
    player=ArticulatedDrummer(physical_hits(folder/'drummer.xsq'),natural_arms=True);view.dry=DynamicDry(player)
    tmp=movie.with_name(movie.stem+'.'+uuid.uuid4().hex+'.rendering.mp4');writer=encoder(tmp,1280,720,20,audio,0,seconds)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    began=time.monotonic();contacts=0;maxerror=0;active={k:0 for k in ['bass','guitar','pitched','vocal']}
    hitmap={}
    for h in perf.mallet_schedule:hitmap.setdefault(round(h['time']*20),[]).append(h)
    try:
        for i in range(round(seconds*20)):
            levels=perf.pose(i);levels[177]=.8;view.dry.time=i/20
            image=view.frame(levels,perf.drums[i],perf.strikes[i],perf.hands[i],i/20,i/20)
            d=ImageDraw.Draw(image);d.rectangle((0,0,1280,44),fill='#08111b')
            title=Path(row['filename']).stem
            while d.textlength(title,font=font)>930:title=title[:-2]
            d.text((18,10),'HELIX  /  '+title,font=font,fill='#e7f4ff')
            d.text((1258,15),'ROCK STAGE' if rock else 'SNOW STAGE',anchor='ra',font=small,fill='#c5d9e6')
            d.rectangle((0,682,1280,720),fill='#08111b')
            start=row['start_seconds'];d.text((18,694),f'{eid}   •   {start+i/20:06.2f}s source   •   {i/20:04.1f} / {seconds:g}s',font=small,fill='#adcadb')
            # Only reference-corroborated words can enter the movie.
            lines=[l for l in perf.vocals['lines'] if l['start_ms']<=i*50<l['end_ms']]
            if category=='04_Lyric_Band_Videos' and lines:
                text=lines[0]['text'];size=25
                lyricfont=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
                while d.textlength(text,font=lyricfont)>1170 and size>16:
                    size-=1;lyricfont=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
                d.rounded_rectangle((35,618,1245,669),10,fill='#0c1727')
                d.text((640,643),text,font=lyricfont,anchor='mm',fill='#ffe4a5')
            image=brand_frame(image);writer.stdin.write(image.tobytes())
            for h in hitmap.get(i,[]):
                tip=perf.mallet_targets[h['side']][1];error=float(np.linalg.norm(tip-(scene.bars[h['pitch']]+(0,.0275+.057,0))))
                maxerror=max(maxerror,error);contacts+=1
            for k,v in [('bass',perf.curves['bass_energy'][i]),('guitar',perf.curves['guitar_energy'][i]),('pitched',perf._bar_levels[i].max()),('vocal',perf.voice_energy[i].max())]:active[k]+=int(v>.08)
            if i in (0,240,400,520,round(seconds*20)-1):image.save(out/(name+f'_{i:04d}.jpg'),quality=90)
            if i%240==0:print('BAND_FRAMES',eid,number,i,round(seconds*20),round(i/max(time.monotonic()-began,.01),2),flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();tmp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
        view.close()
    if writer.wait():raise RuntimeError('Band encoder failed')
    tmp.replace(movie);stamp_mp4(movie)
    if maxerror>1e-5:raise ValueError('Mallet contact does not match its bar')
    proof=dict(file=str(movie.relative_to(root)),excerpt_id=eid,category=category,config=config,sha256=sha(movie),bytes=movie.stat().st_size,
        source_sha256=row['sha256'],excerpt_wav_sha256=sha(audio),source_start=row['start_seconds'],seconds=seconds,
        six_visible_performers=True,unified_pitched_performer=True,mallet_contacts=contacts,max_mallet_contact_error=maxerror,
        motion_omissions=perf.mallet_motion_omissions,drummer_motion_rejections=player.motion_rejections,active_frames=active,
        lyrics_reference_corroborated=bool(perf.vocals['lines']),independent_voices_verified=False,physical_hardware_tested=False,
        render_seconds=round(time.monotonic()-began,2))
    proofpath.write_text(json.dumps(proof,indent=2)+'\n');print('BAND_COMPLETE',name,proof['render_seconds'],flush=True);return proof


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--category',choices=['standalone','lyrics'],required=True)
    p.add_argument('--workers',type=int,default=2);p.add_argument('--ids',nargs='*');p.add_argument('--seconds',type=float,default=36);a=p.parse_args();root=a.root.resolve()
    rows=json.loads((root/'05_Source_Excerpt_Manifests/selected_excerpts.json').read_text());chosen=rows[:12] if a.category=='standalone' else rows[12:]
    tasks=[]
    for i,row in enumerate(chosen):
        if a.ids and row['excerpt_id'] not in a.ids:continue
        tasks.append((str(root),row,STAGES[i%6],bool(i%2),'tour' if a.category=='standalone' else 'vocal_tour',
            '01_Standalone_Bands' if a.category=='standalone' else '04_Lyric_Band_Videos',i+1,a.seconds))
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(render,t) for t in tasks]
        for f in as_completed(futures):f.result()


if __name__=='__main__':main()
