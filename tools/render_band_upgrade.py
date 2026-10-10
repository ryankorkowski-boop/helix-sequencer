"""Render a refined 3D performance rig with preserved lyrics/drummer timing.

These are source-bound 3D character-performance visualizations, not native
xLights FSEQ recordings. Existing native shows are intentionally untouched.
"""
from __future__ import annotations

import argparse
import bisect
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

import moderngl
import numpy as np
from PIL import Image, ImageDraw
import trimesh

from models.band_performance_scene import BandScene, matrix, line_matrix, string_assignment
from tools.build_helpers.ultimate_showcase_preview import _font, read_fseq
from tools.build_snowman_ensemble import soundtrack_check
from models.drummer_review_schedule import decode_review_schedule

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'outputs/Snowman_Ensemble'
OUT=ROOT/'outputs/Snowman_Band_Upgrade'
SHAPES={'REST':(.105,.012),'MBP':(.10,.017),'AH':(.11,.105),'EE':(.14,.035),
        'OH':(.066,.085),'FV':(.105,.031),'L':(.09,.067)}
RENDER_REVISION=2

VERTEX='''#version 330
in vec3 in_position; in vec3 in_normal; in vec3 in_color; in float in_slot;
in vec4 m0; in vec4 m1; in vec4 m2; in vec4 m3;
in vec3 instance_color; in float instance_slot;
uniform mat4 view_projection; uniform float activity[128];
out vec3 world; out vec3 normal; out vec3 color; out float energy;
void main(){
 mat4 model=mat4(m0,m1,m2,m3); vec4 p=model*vec4(in_position,1.0);
 world=p.xyz; normal=normalize(transpose(inverse(mat3(model)))*in_normal);
 color=in_color*instance_color;
 int slot=int(instance_slot>=0.0?instance_slot:in_slot);
 energy=slot>=0?activity[slot]:0.0;
 gl_Position=view_projection*p;
}'''
FRAGMENT='''#version 330
in vec3 world; in vec3 normal; in vec3 color; in float energy;
uniform vec3 eye; out vec4 frag;
void main(){
 vec3 n=normalize(normal), v=normalize(eye-world);
 vec3 l=normalize(vec3(-3.0,7.0,8.0)-world);
 float diffuse=max(dot(n,l),0.0);
 float spec=pow(max(dot(n,normalize(l+v)),0.0),36.0);
 float rim=pow(1.0-max(dot(n,v),0.0),2.5);
 vec3 c=color*(0.17+0.82*diffuse)+vec3(0.25,0.33,0.38)*spec;
 c+=color*(energy*0.70+rim*0.17);
 frag=vec4(pow(clamp(c,0.0,1.0),vec3(0.86)),1.0);
}'''


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def view_projection(width,height):
    eye=np.array((0.,5.05,13.8),dtype=np.float32);target=np.array((0.,1.70,.20))
    forward=(target-eye);forward/=np.linalg.norm(forward)
    right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
    view=np.eye(4,dtype=np.float32);view[:3,:3]=np.vstack((right,up,-forward));view[:3,3]=-view[:3,:3]@eye
    f=1/math.tan(math.radians(43)/2);near,far=.1,60
    perspective=np.zeros((4,4),dtype=np.float32);perspective[0,0]=f/(width/height);perspective[1,1]=f
    perspective[2,2]=(far+near)/(near-far);perspective[2,3]=2*far*near/(near-far);perspective[3,2]=-1
    return perspective@view,eye


class GLView:
    def __init__(self,scene,width=1920,height=1080):
        self.scene=scene;self.width=width;self.height=height
        self.ctx=moderngl.create_standalone_context(backend='egl')
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.program=self.ctx.program(vertex_shader=VERTEX,fragment_shader=FRAGMENT)
        vp,eye=view_projection(width,height);self.program['view_projection'].write(vp.T.tobytes());self.program['eye'].value=tuple(eye)
        self.fbo=self.ctx.simple_framebuffer((width,height),components=3);self.fbo.use()
        templates={'sphere':trimesh.creation.icosphere(subdivisions=2),
                   'box':trimesh.creation.box(),
                   'cylinder':trimesh.creation.cylinder(radius=1,height=1,sections=20)}
        self.groups=[]
        for kind,mesh in templates.items():
            objects=[i for i in scene.instances if i['kind']==kind]
            self.groups.append(self.make_vao(mesh,objects))
        if scene.custom:
            verts=[];normals=[];colors=[];slots=[]
            for item in scene.custom:
                mesh=item['mesh'];ids=mesh.faces.ravel()
                verts.append(mesh.vertices[ids]);normals.append(mesh.vertex_normals[ids])
                colors.append(np.tile(item['color'],(len(ids),1)));slots.append(np.full((len(ids),1),item['slot']))
            data=np.c_[np.vstack(verts),np.vstack(normals),np.vstack(colors),np.vstack(slots)].astype('f4')
            vbo=self.ctx.buffer(data.tobytes());identity=self.ctx.buffer(np.r_[np.eye(4).T.ravel(),(1,1,1),-1].astype('f4').tobytes())
            self.static=self.ctx.vertex_array(self.program,[(vbo,'3f 3f 3f 1f','in_position','in_normal','in_color','in_slot'),
                (identity,'4f 4f 4f 4f 3f 1f /i','m0','m1','m2','m3','instance_color','instance_slot')])
        else:self.static=None

    def make_vao(self,mesh,objects):
        ids=mesh.faces.ravel();vbo=self.ctx.buffer(np.c_[mesh.vertices[ids],mesh.vertex_normals[ids],np.ones((len(ids),3)),np.full(len(ids),-1)].astype('f4').tobytes())
        instances=self.ctx.buffer(reserve=max(1,len(objects))*20*4)
        vao=self.ctx.vertex_array(self.program,[(vbo,'3f 3f 3f 1f','in_position','in_normal','in_color','in_slot'),
            (instances,'4f 4f 4f 4f 3f 1f /i','m0','m1','m2','m3','instance_color','instance_slot')])
        return vao,instances,objects

    def frame(self,levels):
        self.fbo.clear(.018,.027,.047,1)
        self.program['activity'].write(np.asarray(levels,dtype='f4').tobytes())
        for vao,buffer,objects in self.groups:
            if not objects:continue
            values=np.array([np.r_[o['matrix'].T.ravel(),o['color'],o['slot']] for o in objects],dtype='f4')
            buffer.write(values.tobytes());vao.render(instances=len(objects))
        if self.static:self.static.render()
        return Image.frombytes('RGB',(self.width,self.height),self.fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    def close(self):self.ctx.release()


def native_drummer(row):
    folder=OLD/'shows'/f'{row["id"]}_band'
    frames,step=read_fseq(folder/'Snowman_Band.fseq');assert step==50
    levels,strikes,hands,schedule=decode_review_schedule(folder/'Snowman_Band.xsq',len(frames))
    return levels,strikes,hands,{'fseq_sha256':sha(folder/'Snowman_Band.fseq'),
                         'xsq_sha256':sha(folder/'Snowman_Band.xsq'),
                         'drummer_levels_sha256':hashlib.sha256(levels.tobytes()).hexdigest(),
                         'drummer_strike_holds_sha256':hashlib.sha256(strikes.tobytes()).hexdigest(),
                         'source_hand_schedule_sha256':hashlib.sha256(hands.tobytes()).hexdigest(),
                         'schedule':schedule}


class Performance:
    def __init__(self,row,variant,scene):
        self.row=row;self.variant=variant;self.scene=scene
        self.curves=np.load(OUT/'analysis'/row['id']/'performance_curves.npz')
        self.vocals=json.loads((OLD/'analysis'/row['id']/'vocals.json').read_text())
        self.drums,self.strikes,self.hands,self.drum_proof=native_drummer(row)
        self.n=len(self.drums);self.mouths=np.full(self.n,'REST',dtype='<U4')
        for event in self.vocals['mouths']:
            lo=max(0,event['start_ms']//50);hi=min(self.n,math.ceil(event['end_ms']/50))
            self.mouths[lo:hi]=event['phoneme']
        self.lyric_starts=[e['start_ms'] for e in self.vocals['lines']]
        self.note_routes={}

    def levels(self,i):
        out=np.zeros(128,dtype=np.float32)
        for k,kind in enumerate(('bass','guitar','piano')):out[k]=self.curves[kind+'_energy'][i]*.50
        slot=int(self.curves['vocal_route'][i]);out[3+slot]=self.curves['vocal_energy'][i]*.6
        out[5:13]=self.drums[i]
        for kind,first in (('bass',13),('guitar',17)):
            chosen=[]
            for note in self.curves[kind+'_notes'][i]:
                assignment=string_assignment(int(note),kind) if note>=0 else None
                if assignment:
                    string,fret=assignment;out[first+string]=self.curves[kind+'_energy'][i];chosen.append((string,fret))
            self.note_routes[kind]=chosen
        for note in self.curves['piano_notes'][i]:
            if note<0:continue
            while note<48:note+=12
            while note>84:note-=12
            out[23+int(note)-48]=self.curves['piano_energy'][i]
        return out

    def pose(self,i):
        t=i/20;levels=self.levels(i)
        route=int(self.curves['vocal_route'][i])
        for item in self.scene.instances:
            role=item.get('mouth_role')
            if role:
                shape=self.mouths[i] if role in ('faces','lead','harmony') else 'REST'
                if (role=='lead' and route!=0) or (role=='harmony' and route!=1):shape='REST'
                w,h=SHAPES[shape];item['matrix']=matrix(item['mouth_center'],(w,h,.031))
        for rig in self.scene.rigs:
            role,side=rig['role'],rig['side'];shoulder=rig['shoulder'];elbow=rig['elbow'].copy();hand=rig['hand'].copy()
            if role=='bass':
                if side=='pluck':hand[0]+=.045*math.sin(t*28)*self.curves['bass_attack'][i];hand[1]+=.065*self.curves['bass_attack'][i]
                elif self.note_routes['bass']:
                    fret=self.note_routes['bass'][0][1];hand[1]=2.87-min(fret,24)/24*1.12
            elif role=='guitar':
                if side=='strum':hand[1]+=.17*math.sin(t*27)*self.curves['guitar_attack'][i];hand[0]+=.07*math.cos(t*27)*self.curves['guitar_attack'][i]
                elif self.note_routes['guitar']:
                    fret=self.note_routes['guitar'][0][1];u=.90-min(fret,20)/20*.65
                    hand[0]=4+.02+1.20*u;hand[1]=1.27+1.05*u
            elif role=='piano':
                notes=[int(n) for n in self.curves['piano_notes'][i] if n>=0]
                if notes:
                    note=min(notes) if side=='left' else max(notes)
                    while note<48:note+=12
                    while note>84:note-=12
                    hand[0]=(note-66)/18*1.07
                hand[1]-=.035*self.curves['piano_attack'][i]
            elif role in ('lead','harmony') and side=='left':
                slot=0 if role=='lead' else 1;energy=self.curves['vocal_energy'][i] if route==slot and self.mouths[i]!='REST' else 0
                hand[1]+=.65*energy;hand[0]+=.14*energy
            elif role=='drums':
                left=side=='left';hit=0.;point=hand.copy();tip=hand+(-.27 if left else .27,-.25,.07)
                # Only source-tagged strike holds move arms. Idle art and the
                # longer cymbal shimmer must never be treated as motion cues.
                options=[(self.strikes[i,6 if left else 7],(-1.42 if left else 1.4,2.51,-1.74))]
                if (left and self.hands[i]==0) or (not left and self.hands[i]==1):options.append((self.strikes[i,1],(-.88,1.70,-1.18)))
                options += [(self.strikes[i,3 if left else 4],(-.54 if left else .46,2.17 if left else 2.10,-1.60)),
                            (self.strikes[i,5] if not left else 0.,(.97,1.40,-1.79))]
                hit,target=max(options,key=lambda pair:pair[0])
                if hit>.16:
                    tip=np.array(target,float);point=tip+(.20 if left else -.20,.35,-.18)
                    hand=point;elbow=(shoulder+hand)/2+np.array((-.12 if left else .12,.12,-.08))
                if 'stick_id' in rig:self.scene.instances[rig['stick_id']]['matrix']=line_matrix(hand,tip,.015)
            first,second,mitten=rig['ids']
            self.scene.instances[first]['matrix']=line_matrix(shoulder,elbow,.046)
            self.scene.instances[second]['matrix']=line_matrix(elbow,hand,.046)
            self.scene.instances[mitten]['matrix']=matrix(hand,(.10,.075,.08))
        return levels

    def caption(self,frame,i):
        d=ImageDraw.Draw(frame);w,h=frame.size
        d.rounded_rectangle((15,12,w-15,91),radius=12,fill='#071221')
        d.text((32,20),'HELIX  •  SNOWMAN BAND / REFINED 3D PERFORMANCE' if self.variant=='band' else 'HELIX  •  DRUMMER + HELIX SINGING FACES / REFINED 3D',font=_font(26),fill='#E8F3FF')
        d.text((32,57),self.row['title'],font=_font(20),fill='#A5C5D9')
        d.text((w-125,30),f'{i/20:06.1f}s',font=_font(19),fill='#B2D0DF')
        j=bisect.bisect_right(self.lyric_starts,i*50)-1
        if j>=0 and i*50<self.vocals['lines'][j]['end_ms']:
            text=self.vocals['lines'][j]['text'];font=_font(24)
            while d.textlength(text,font=font)>w-120:text=text[:-4]+'…'
            d.rounded_rectangle((30,h-103,w-30,h-52),radius=12,fill='#0A1829')
            d.text((w/2,h-78),text,font=font,fill='#F6DEAB',anchor='mm')
        d.text((30,h-31),'SOURCE-BOUND CHARACTER PERFORMANCE  •  Preserved lyric/drum timing  •  3D review visualization',font=_font(13),fill='#8BAABD')
        return frame


def render(row,variant,seconds=0,start=0,width=1920,height=1080):
    folder=OUT/'movies';folder.mkdir(parents=True,exist_ok=True)
    suffix='_pilot' if seconds else ''
    name=f'{row["id"]}_{variant}_Refined_3D{suffix}.mp4';movie=folder/name
    proof_path=movie.with_suffix('.verification.json')
    if proof_path.exists() and movie.exists():
        cached=json.loads(proof_path.read_text())
        if (cached.get('render_revision')==RENDER_REVISION and cached['width']==width
                and cached['height']==height and sha(movie)==cached['sha256']):return cached
    scene=BandScene(variant);performance=Performance(row,variant,scene);view=GLView(scene,width,height)
    scene.export_glb(folder/f'{variant}_Refined_3D.glb')
    offset=round(start*20);count=min(performance.n-offset,round(seconds*20)) if seconds else performance.n
    original=OLD/'shows'/f'{row["id"]}_band/media/song.mp3'
    assert sha(original)==row['sha256']
    args=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r','20','-i','-',
          '-ss',str(start),'-i',str(original),'-map','0:v:0','-map','1:a:0','-t',str(count/20),
          '-c:v','libx264','-preset','veryfast','-crf','20','-threads','2','-pix_fmt','yuv420p',
          '-c:a','aac','-b:a','192k','-movflags','+faststart',str(movie)]
    proc=subprocess.Popen(args,stdin=subprocess.PIPE);began=time.monotonic()
    try:
        for frame_id in range(count):
            i=offset+frame_id;frame=performance.caption(view.frame(performance.pose(i)),i)
            if frame_id in (0,min(240,count-1),count//2,count-1):frame.save(folder/f'{movie.stem}_{frame_id:05}.png')
            proc.stdin.write(frame.tobytes())
            if frame_id and frame_id%400==0:print(name,frame_id,'/',count,round(frame_id/(time.monotonic()-began),1),'fps',flush=True)
    finally:
        proc.stdin.close();view.close()
    assert proc.wait()==0
    p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    video=next(s for s in p['streams'] if s['codec_type']=='video')
    assert int(video['nb_frames'])==count and video['r_frame_rate']=='20/1' and video['pix_fmt']=='yuv420p'
    subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(movie),'-f','null','-'],check=True)
    sound=soundtrack_check(original,movie) if not seconds else {'pilot_source_offset_seconds':start}
    proof={'id':row['id'],'title':row['title'],'variant':variant,'render_revision':RENDER_REVISION,'file':str(movie),'bytes':movie.stat().st_size,
           'sha256':sha(movie),'source_sha256':row['sha256'],'duration_seconds':count/20,'frames':count,
           'width':width,'height':height,'full_decode_passed':True,'soundtrack':sound,
           'source_native_drummer':performance.drum_proof,'native_xlights_playback':False,
           'new_3d_drummer_interpretation':True,'geometry_primitives':len(scene.instances),
           'source_lyrics_sha256':sha(OLD/'analysis'/row['id']/'vocals.json'),
           'analysis_sha256':sha(OUT/'analysis'/row['id']/'performance_curves.npz')}
    proof_path.write_text(json.dumps(proof,indent=2)+'\n');print('VERIFIED',name,flush=True)
    return proof


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ids',nargs='+',default=['00','01','02','03','04','05'])
    parser.add_argument('--variants',nargs='+',default=['band','faces']);parser.add_argument('--seconds',type=float,default=0)
    parser.add_argument('--start',type=float,default=0);parser.add_argument('--width',type=int,default=1920);parser.add_argument('--height',type=int,default=1080)
    args=parser.parse_args();rows=json.loads((OLD/'sources.json').read_text());proof=[]
    for row in rows:
        if row['id'] not in args.ids:continue
        for variant in args.variants:
            if row['id']=='00' and variant=='faces':continue
            proof.append(render(row,variant,args.seconds,args.start,args.width,args.height))
    (OUT/('pilot_verification.json' if args.seconds else 'render_verification.json')).write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
