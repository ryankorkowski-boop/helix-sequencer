"""Render and check source-bound instrument studies, with encoded cue evidence."""
from __future__ import annotations
import argparse,json,math,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image
from models.readable_band_scene import ReadableBandScene
from tools.readable_band_performance import ReadablePerformance,STRING_FRAGMENT,OUT,ROOT
from tools.render_intricate_band_samplers import SamplerView,SAMPLER_VERTEX,sha,excerpt_audio_check

OLD=ROOT/'outputs/Snowman_Ensemble'


def camera_for(focus):
    positions={'stage':((.3,5.6,16.5),(.7,2.7,-.9),44),
               'bass':((-3.8,3.5,6.8),(-3.5,1.9,.0),40),
               'guitar':((4.9,3.6,6.9),(4.5,1.8,.15),40),
               'keyboard':((6.6,4.6,8.6),(6.5,1.65,2.65),43)}
    eye0,target,fov=positions[focus]
    def camera(width,height,elapsed):
        eye=np.array(eye0,dtype='f4');eye[2]-=.30*math.sin(elapsed*.08)
        forward=np.asarray(target)-eye;forward/=np.linalg.norm(forward)
        right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
        v=np.eye(4,dtype='f4');v[:3,:3]=np.vstack((right,up,-forward));v[:3,3]=-v[:3,:3]@eye
        f=1/math.tan(math.radians(fov)/2);near,far=.1,80
        p=np.zeros((4,4),dtype='f4');p[0,0]=f/(width/height);p[1,1]=f;p[2,2]=(far+near)/(near-far);p[2,3]=2*far*near/(near-far);p[3,2]=-1
        return p@v,eye
    return camera


def instrument_box(scene,kind,view,elapsed):
    if kind in ('bass','guitar'):
        points=np.vstack([np.linspace(s['a'],s['b'],20) for s in scene.strings[kind]])
    else:points=np.array([o['matrix'][:3,3] for o in scene.instances if o['name'].startswith('piano_key_')])
    vp,_=view.camera_callback(view.width,view.height,elapsed)
    q=np.c_[points,np.ones(len(points))]@vp.T;q=q[:,:2]/q[:,3,None]
    xy=(q+1)*np.array((view.width/2,view.height/2));xy[:,1]=view.height-xy[:,1]
    lo=np.floor(xy.min(axis=0)-8).astype(int);hi=np.ceil(xy.max(axis=0)+8).astype(int)
    lo=np.maximum(lo,0);hi=np.minimum(hi,(view.width,view.height))
    return tuple(map(int,(*lo,*hi)))


def assert_pose(performance,i,levels):
    scene=performance.scene
    for kind,first,count in [('bass',13,4),('guitar',17,6)]:
        routes=performance.active_routes[kind]
        assert len({r[0] for r in routes})==len(routes)
        assert np.all(np.isfinite(levels[first:first+count]))
        assert all(0<=f<=24 for s,f,n in routes)
        if routes:
            hand=performance.hand_targets[kind,'finger']
            if kind=='bass':
                assert abs(hand[0]-scene.strings[kind][routes[0][0]]['a'][0])<1e-5
                assert abs(hand[1]-performance.curves['bass_height'][i])<1e-5
            else:
                s=scene.strings[kind][routes[0][0]]
                fret=float(np.median([r[1] for r in routes]));u=.96-.50*min(fret,24)/24
                assert np.allclose(hand,s['a']+(s['b']-s['a'])*u+(0,0,.065))
    expected=np.zeros(37)
    for pitch,v in performance.key_levels.items():expected[pitch-48]=v
    assert np.allclose(levels[23:60],expected)
    if performance.key_levels:
        notes=sorted(performance.key_levels);spread=notes[-1]-notes[0]>=3
        which='left' if notes[0]<66 else 'right'
        for side in ('left','right'):
            if spread or side==which:
                pitch=notes[0] if side=='left' else notes[-1]
                hand=performance.hand_targets['piano',side]
                assert np.allclose(hand[[0,2]],performance.key_centers[pitch][[0,2]]+(0,.08))
    assert all(np.isfinite(o['matrix']).all() for o in scene.instances)


def render(row,layout,start,focus='stage',seconds=42,width=1920,height=1080,suffix=''):
    dest=OUT/'movies';dest.mkdir(parents=True,exist_ok=True)
    name=f'{row["id"]}_{layout}_{focus}{suffix}_{seconds:g}s'
    movie=dest/(name+'.mp4');scene=ReadableBandScene(layout);perf=ReadablePerformance(row,scene)
    view=SamplerView(scene,width,height,SAMPLER_VERTEX,STRING_FRAGMENT);view.camera_callback=camera_for(focus)
    view.dry.proof['source']='canonical source-art compositor with torso shoulder revision, pose spec v7'
    offset=round(start*20);count=round(seconds*20);assert offset+count<=perf.n
    original=OLD/'shows'/f'{row["id"]}_band/media/song.mp3';assert sha(original)==row['sha256']
    # Representative actual source onsets across the excerpt, independent of
    # activity in the surrounding layout. Test each surface against its muted
    # counterfactual in the identical scene and pose.
    selected={};coverage={}
    for kind in ('bass','guitar','piano'):
        hits=np.flatnonzero(perf.curves[kind+'_attack'][offset:offset+count]>.09)
        coverage[kind]={'source_attack_frames':len(hits),'visible_checks':0}
        if len(hits) and (focus=='stage' or kind=={'bass':'bass','guitar':'guitar','keyboard':'piano'}.get(focus)):
            choose=hits[np.unique(np.linspace(0,len(hits)-1,min(5,len(hits))).astype(int))]
            for f in choose:selected.setdefault(int(f),[]).append(kind)
    refs=[];began=time.monotonic()
    proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}',
        '-r','20','-i','-','-ss',str(start),'-i',str(original),'-map','0:v:0','-map','1:a:0','-t',str(seconds),
        '-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(movie)],stdin=subprocess.PIPE)
    try:
        for f in range(count):
            i=offset+f;levels=perf.pose(i);assert_pose(perf,i,levels)
            frame=view.frame(levels,perf.drums[i],perf.strikes[i],perf.hands[i],i/20,f/20)
            if f in selected:
                for kind in selected[f]:
                    box=instrument_box(scene,kind,view,f/20);muted=levels.copy()
                    low,high={'bass':(13,17),'guitar':(17,23),'piano':(23,60)}[kind];muted[low:high]=0
                    control=view.frame(muted,perf.drums[i],perf.strikes[i],perf.hands[i],i/20,f/20)
                    active=np.asarray(frame.crop(box));quiet=np.asarray(control.crop(box))
                    delta=np.abs(active.astype(float)-quiet.astype(float)).mean(axis=2)
                    # Restrict delivery checks to pixels actually affected by
                    # this instrument's own channels, excluding layout flashes.
                    mask=delta>5;assert mask.sum()>=6,(name,kind,f,'no visible instrument response')
                    refs.append((f,kind,box,active.copy(),quiet.copy(),mask))
            frame=perf.caption(frame,i,focus)
            if f in (0,count//3,2*count//3,count-1):frame.save(dest/f'{name}_{f:04}.png')
            proc.stdin.write(frame.tobytes())
            if f and f%200==0:print(name,f,count,round(f/(time.monotonic()-began),2),'fps',flush=True)
    finally:proc.stdin.close();view.close()
    assert proc.wait()==0
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(movie)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert int(video['nb_frames'])==count and abs(float(video['duration'])-seconds)<.001
    subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(movie),'-f','null','-'],check=True)
    encoded=[]
    for f,kind,box,active,quiet,mask in refs:
        data=subprocess.check_output(['ffmpeg','-v','error','-ss',str(f/20),'-i',str(movie),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
        decoded=np.frombuffer(data,np.uint8).reshape(height,width,3)[box[1]:box[3],box[0]:box[2]]
        active_error=float(np.abs(decoded.astype(float)-active).mean(axis=2)[mask].mean())
        quiet_error=float(np.abs(decoded.astype(float)-quiet).mean(axis=2)[mask].mean())
        assert quiet_error-active_error>1,(name,kind,f,active_error,quiet_error)
        coverage[kind]['visible_checks']+=1
        encoded.append(dict(frame=f,kind=kind,box=box,own_channel_pixels=int(mask.sum()),active_error=active_error,muted_error=quiet_error))
    proof=dict(id=row['id'],title=row['title'],layout=layout,focus=focus,start=start,seconds=seconds,width=width,height=height,frames=count,
        sha256=sha(movie),bytes=movie.stat().st_size,source_sha256=row['sha256'],full_decode_passed=True,
        all_frames_pose_routing_checked=True,encoded_instrument_checks=encoded,source_attacks=coverage,
        soundtrack=excerpt_audio_check(original,movie,start,seconds),drummer_geometry=view.dry.proof,
        native_drummer=perf.drum_proof,native_xlights_playback=False,verified_musical_score=False,
        analysis_inputs={p.name:sha(p) for p in (OUT/'analysis'/row['id']).glob('*')},
        implementation_sha256={p:sha(ROOT/p) for p in ['models/readable_band_scene.py','models/band_instrument_logic.py',
            'tools/readable_band_performance.py','tools/render_readable_band.py','tools/render_intricate_band_samplers.py','tools/render_band_upgrade.py']})
    movie.with_suffix('.verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('VERIFIED',name,flush=True);return proof


def main():
    p=argparse.ArgumentParser();p.add_argument('--group');p.add_argument('--id');p.add_argument('--focus',default='stage');p.add_argument('--layout',default='prismatic_orrery')
    p.add_argument('--start',type=float,default=77);p.add_argument('--seconds',type=float,default=42);p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080)
    args=p.parse_args();rows={r['id']:r for r in json.loads((OLD/'sources.json').read_text())}
    if args.group:
        jobs=json.loads((ROOT/'evidence/band_instrument_review/batch.json').read_text())
        for j in jobs:
            if j['id']==args.group:render(rows[j['id']],j['layout'],j['start'],j['focus'],suffix=j.get('suffix',''))
    else:render(rows[args.id],args.layout,args.start,args.focus,args.seconds,args.width,args.height,'_pilot')


if __name__=='__main__':main()
