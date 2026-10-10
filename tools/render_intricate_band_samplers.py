"""Render 42-second musical stages with the exact dry-test drummer pose art."""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

import moderngl
import numpy as np
from PIL import Image, ImageDraw

from models.band_performance_scene import matrix
from models.band_sampler_logic import SHAPE_NAMES
from models.intricate_band_scene import IntricateBandScene, LAYOUTS
from tools.render_band_upgrade import GLView, Performance, VERTEX, FRAGMENT, SHAPES, native_drummer
from tools.render_drummer_v3_preview import load_component_masks, compose_lighting, TARGETS
from tools.build_helpers.ultimate_showcase_preview import _font

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'outputs/Snowman_Ensemble'
OUT=ROOT/'outputs/Intricate_Band_Samplers'
REVISION=4
SAMPLER_VERTEX=VERTEX.replace('out vec3 world;', 'out float channel; out vec3 world;').replace(
    'energy=slot>=0?activity[slot]:0.0;', 'channel=float(slot); energy=slot>=0?activity[slot]:0.0;')
SAMPLER_FRAGMENT=FRAGMENT.replace('in vec3 world;', 'in float channel; in vec3 world;').replace(
    'uniform vec3 eye;', 'uniform vec3 eye; uniform float song_time;').replace(
    'c+=color*(energy*0.70+rim*0.17);', '''
 if(channel>=64.0){
   float path=world.x*0.36+world.y*0.54+world.z*0.19;
   float wave=0.5+0.5*sin(path*4.2-song_time*3.5+channel*0.22);
   float sparkle=pow(max(0.0,sin(world.y*5.0+world.x*3.0-song_time*2.4+channel)),12.0);
   c=color*(0.07+diffuse*0.10+(0.20+energy)*(.26+.74*wave))+color*sparkle*energy*.60;
 } else { c+=color*(energy*0.70+rim*0.17); }
''')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def camera(width,height,elapsed):
    # A slow dolly reveals depth while keeping the musical performance readable.
    near_weight=math.sin(math.pi*np.clip((elapsed-3)/36,0,1))**2
    eye=np.array((.65*math.sin(elapsed*.065),6.1-near_weight*.85,19.5-near_weight*4.1),dtype='f4')
    target=np.array((0,3.0-near_weight*.65,-1.0))
    forward=target-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
    view=np.eye(4,dtype='f4');view[:3,:3]=np.vstack((right,up,-forward));view[:3,3]=-view[:3,:3]@eye
    f=1/math.tan(math.radians(44)/2);near,far=.1,80
    p=np.zeros((4,4),dtype='f4');p[0,0]=f/(width/height);p[1,1]=f
    p[2,2]=(far+near)/(near-far);p[2,3]=2*far*near/(near-far);p[3,2]=-1
    return p@view,eye


class ExactDryDrummer:
    """Cache exact compositor poses, retaining source pixels and mirrored kit."""
    def __init__(self):
        source,masks=load_component_masks();self.source=source;self.masks=masks
        self.crop=(99,124,494,380)
        self.idle=np.asarray(compose_lighting(source,masks,[]).crop(self.crop).convert('RGB'),dtype='f4')
        self.poses={}
        for hand in ('left','right'):
            for k,target in enumerate(TARGETS):
                self.poses[k,hand]=np.asarray(compose_lighting(source,masks,[target],snare_hand=hand,
                    cymbal_levels={target:1} if k>=6 else None).crop(self.crop).convert('RGB'),dtype='f4')
        self.ringing={k:np.asarray(compose_lighting(source,masks,[],cymbal_levels={TARGETS[k]:1}).crop(self.crop).convert('RGB'),dtype='f4') for k in (6,7)}
        paths=['fixtures/band_geometry/source/drummerbg.png','fixtures/band_geometry/source/drummer_idle.png',
               'fixtures/band_geometry/drummer_v3_pose_spec.json','fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel']
        self.proof={'source':'same canonical geometry/compositor as dry artifact11527580859',
                    'assets':{p:sha(ROOT/p) for p in paths},'replacement_3d_kit':False,
                    'high_tom_viewer_right':True,'mid_and_floor_toms_viewer_left':True,
                    'crop':self.crop,'planar_physical_prop_mounted_in_3d_stage':True}

    def frame(self,lighting,strikes,hand):
        out=self.idle.copy();name='right' if hand else 'left'
        for k in range(8):
            if strikes[k]>.16:
                np.maximum(out,self.poses[k,name],out=out)
        for k in (6,7):
            if lighting[k]>0:
                np.maximum(out,self.idle+(self.ringing[k]-self.idle)*lighting[k],out=out)
        rgb=np.clip(out,0,255).astype('u1')
        # Empty stage/grid/background pixels do not hide the surrounding layout.
        # This is transparent projection of the existing physical source art.
        alpha=np.clip((rgb.max(axis=2).astype(float)-7)*22,0,255).astype('u1')
        return np.dstack((rgb,alpha))


class SamplerView(GLView):
    def __init__(self,scene,width,height):
        super().__init__(scene,width,height,SAMPLER_VERTEX,SAMPLER_FRAGMENT)
        self.dry=ExactDryDrummer()
        self.quad=self.ctx.program(vertex_shader='''#version 330
            in vec3 position; in vec2 uv; uniform mat4 view_projection;
            out vec2 texcoord; void main(){texcoord=uv;gl_Position=view_projection*vec4(position,1.0);}''',
            fragment_shader='''#version 330
            uniform sampler2D artwork; in vec2 texcoord; out vec4 frag;
            void main(){vec4 c=texture(artwork,texcoord);if(c.a<.10)discard;
            frag=vec4(pow(c.rgb,vec3(.86)),c.a);}''')
        order=[0,1,2,2,1,3];uv=np.array([(0,1),(1,1),(0,0),(1,0)],dtype='f4')
        data=np.c_[scene.dry_drummer_corners[order],uv[order]].astype('f4')
        self.quad_buffer=self.ctx.buffer(data.tobytes())
        self.quad_vao=self.ctx.vertex_array(self.quad,[(self.quad_buffer,'3f 2f','position','uv')])
        self.texture=self.ctx.texture((395,256),4)
        self.texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
        self.scene_texture=self.ctx.texture((width,height),3)
        self.scene_fbo=self.ctx.framebuffer([self.scene_texture],self.ctx.depth_renderbuffer((width,height)))
        self.bloom_textures=[self.ctx.texture((width//3,height//3),3) for _ in range(2)]
        self.bloom_fbos=[self.ctx.framebuffer([t]) for t in self.bloom_textures]
        for tex in [self.scene_texture,*self.bloom_textures]:tex.filter=(moderngl.LINEAR,moderngl.LINEAR)
        full_vertex='''#version 330
            in vec2 position;out vec2 uv;void main(){uv=position*.5+.5;gl_Position=vec4(position,0,1);}'''
        self.extract=self.ctx.program(vertex_shader=full_vertex,fragment_shader='''#version 330
            uniform sampler2D image;in vec2 uv;out vec4 frag;
            void main(){vec3 c=texture(image,uv).rgb;float hi=max(c.r,max(c.g,c.b));
            float lo=min(c.r,min(c.g,c.b));float saturation=(hi-lo)/max(hi,.01);
            frag=vec4(c*smoothstep(.20,.6,hi)*smoothstep(.18,.5,saturation),1);}''')
        self.blur=self.ctx.program(vertex_shader=full_vertex,fragment_shader='''#version 330
            uniform sampler2D image;uniform vec2 direction;in vec2 uv;out vec4 frag;
            void main(){vec3 c=texture(image,uv).rgb*.227027;
            c+=(texture(image,uv+direction*1.384615).rgb+texture(image,uv-direction*1.384615).rgb)*.316216;
            c+=(texture(image,uv+direction*3.230769).rgb+texture(image,uv-direction*3.230769).rgb)*.070270;
            frag=vec4(c,1);}''')
        self.combine=self.ctx.program(vertex_shader=full_vertex,fragment_shader='''#version 330
            uniform sampler2D image;uniform sampler2D glow;in vec2 uv;out vec4 frag;
            void main(){vec3 c=texture(image,uv).rgb+texture(glow,uv).rgb*.65;
            frag=vec4(clamp(c,0,1),1);}''')
        self.full_buffer=self.ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[-1,1],[1,-1],[1,1]],dtype='f4').tobytes())
        self.full_vaos={name:self.ctx.vertex_array(prog,[(self.full_buffer,'2f','position')])
                        for name,prog in [('extract',self.extract),('blur',self.blur),('combine',self.combine)]}
        self.output_fbo=self.fbo

    def frame(self,levels,lighting,strikes,hand,source_time,elapsed):
        vp,eye=camera(self.width,self.height,elapsed)
        self.program['view_projection'].write(vp.T.tobytes());self.program['eye'].value=tuple(eye)
        self.program['song_time'].value=source_time
        self.fbo=self.scene_fbo;self.fbo.use();self.draw(levels)
        self.texture.write(self.dry.frame(lighting,strikes,hand).tobytes());self.texture.use(0)
        self.quad['view_projection'].write(vp.T.tobytes())
        self.ctx.enable(moderngl.BLEND);self.ctx.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA)
        self.quad_vao.render();self.ctx.disable(moderngl.BLEND)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.bloom_fbos[0].use();self.scene_texture.use(0);self.full_vaos['extract'].render()
        for axis in ((3/self.width,0),(0,3/self.height)):
            self.bloom_fbos[1].use();self.bloom_textures[0].use(0);self.blur['direction'].value=axis
            self.full_vaos['blur'].render()
            self.bloom_textures.reverse();self.bloom_fbos.reverse()
        self.output_fbo.use();self.scene_texture.use(0);self.bloom_textures[0].use(1)
        self.combine['image'].value=0;self.combine['glow'].value=1;self.full_vaos['combine'].render()
        self.ctx.enable(moderngl.DEPTH_TEST)
        return Image.frombytes('RGB',(self.width,self.height),self.output_fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)


class SamplerPerformance(Performance):
    def __init__(self,row,scene):
        self.row=row;self.variant='band';self.scene=scene
        with np.load(OUT/'analysis'/row['id']/'performance_curves.npz') as curves:
            self.curves={k:v.copy() for k,v in curves.items()}
        self.vocals=json.loads((OUT/'analysis'/row['id']/'vocals.json').read_text())
        self.drums,self.strikes,self.hands,self.drum_proof=native_drummer(row)
        self.n=len(self.drums);self.mouths=np.array([SHAPE_NAMES[int(x)] for x in self.curves['mouth_lanes'][:,0]])
        # Parent performs arms/string/key routes; final mouth lanes override
        # its historical single-singer behavior immediately below.
        self.lyric_starts=[e['start_ms'] for e in self.vocals['lines']];self.note_routes={}
        self.key_centers={int(o['name'].removeprefix('piano_key_')):o['matrix'][:3,3].copy()
                          for o in scene.instances if o['name'].startswith('piano_key_')}

    def pose(self,i):
        levels=super().pose(i)
        lanes=self.curves['mouth_lanes'][i]
        for k in (0,1):
            levels[3+k]=self.curves['vocal_energy'][i]*.6 if lanes[k] else 0
        for item in self.scene.instances:
            role=item.get('mouth_role')
            if role in ('lead','harmony'):
                shape=SHAPE_NAMES[int(lanes[int(role=='harmony')])];w,h=SHAPES[shape]
                # Jaw aperture follows actual vocal energy without making
                # consonant closures disappear or expanding a silent mouth.
                gain=.75+.25*self.curves['vocal_energy'][i] if shape!='REST' else 1
                item['matrix']=matrix(item['mouth_center'],(w,h*gain,.031))
        for rig in self.scene.rigs:
            if rig['role']=='bass' and rig['side']=='finger':
                from models.band_performance_scene import line_matrix
                hand=rig['hand'].copy();hand[1]=self.curves['bass_height'][i]
                elbow=(rig['shoulder']+hand)/2+(.23,.05,.15)
                a,b,c=rig['ids'];self.scene.instances[a]['matrix']=line_matrix(rig['shoulder'],elbow,.046)
                self.scene.instances[b]['matrix']=line_matrix(elbow,hand,.046)
                self.scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
            elif rig['role']=='piano':
                # Parent key positions are relative to its old center; retain
                # the new instrument offset for both complete arm segments.
                from models.band_performance_scene import line_matrix
                notes=[int(n) for n in self.curves['piano_notes'][i] if n>=0]
                hand=rig['hand'].copy()
                if notes:
                    note=min(notes) if rig['side']=='left' else max(notes)
                    while note<48:note+=12
                    while note>84:note-=12
                    key=self.key_centers[note]
                    hand[0]=key[0];hand[2]=key[2]+.10
                    hand[1]=key[1]+.035+.095-.030*self.curves['piano_attack'][i]
                elbow=rig['elbow'].copy();a,b,c=rig['ids']
                self.scene.instances[a]['matrix']=line_matrix(rig['shoulder'],elbow,.046)
                self.scene.instances[b]['matrix']=line_matrix(elbow,hand,.046)
                self.scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
            elif rig['role'] in ('lead','harmony') and rig['side']=='left':
                from models.band_performance_scene import line_matrix
                k=int(rig['role']=='harmony')
                energy=self.curves['vocal_energy'][i] if lanes[k] else 0
                hand=rig['hand'].copy();hand[1]+=.65*energy;hand[0]+=.14*energy
                a,b,c=rig['ids']
                self.scene.instances[a]['matrix']=line_matrix(rig['shoulder'],rig['elbow'],.046)
                self.scene.instances[b]['matrix']=line_matrix(rig['elbow'],hand,.046)
                self.scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
        source=np.array([self.curves['bass_energy'][i],self.curves['guitar_energy'][i],
                         self.curves['piano_energy'][i],self.curves['vocal_energy'][i],
                         self.strikes[i,0],max(self.strikes[i,1],self.strikes[i,6],self.strikes[i,7])])
        for k in range(48):
            levels[64+k]=.12+.78*source[k%6]
        return levels

    def caption(self,frame,i):
        d=ImageDraw.Draw(frame);w,h=frame.size
        d.rounded_rectangle((18,12,w-18,86),radius=12,fill='#071221')
        d.text((34,21),LAYOUTS[self.scene.layout].upper(),font=_font(25),fill='#DDF5FF')
        d.text((34,55),self.row['title']+'  •  Snowman ensemble',font=_font(18),fill='#A7CDE1')
        d.text((w-148,35),f'{i/20:06.1f}s',font=_font(19),fill='#A7CDE1')
        j=bisect.bisect_right(self.lyric_starts,i*50)-1
        if j>=0 and i*50<self.vocals['lines'][j]['end_ms']:
            text=self.vocals['lines'][j]['text'];font=_font(23)
            while d.textlength(text,font=font)>w-120:text=text[:-4]+'…'
            d.rounded_rectangle((32,h-93,w-32,h-48),radius=10,fill='#0A1829')
            d.text((w/2,h-71),text,font=font,fill='#F5DEAC',anchor='mm')
        elif self.curves['mouth_lanes'][i].max():
            d.text((w/2,h-65),'♪  Wordless vocal  ♪',font=_font(21),fill='#F5DEAC',anchor='mm')
        d.text((32,h-28),'42-SECOND PERFORMANCE STUDY  •  Original dry-test drummer  •  Duet casting',font=_font(13),fill='#8DAFC3')
        return frame


def excerpt_audio_check(original,movie,start,seconds):
    def samples(path,offset=0):
        return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-ss',str(offset),'-i',str(path),
            '-t',str(seconds),'-vn','-ac','1','-ar','8000','-f','f32le','-']),dtype='<f4')
    a,b=samples(original,start),samples(movie);n=min(len(a),len(b))
    correlation=float(np.corrcoef(a[:n],b[:n])[0,1])
    assert correlation>.995 and abs(len(a)-len(b))<960
    return dict(source_offset_seconds=start,sample_rate=8000,zero_offset_correlation=correlation,
                source_samples=len(a),movie_samples=len(b),original_excerpt_matches=True)


def render(row,layout,start,seconds=42,width=1920,height=1080,suffix=''):
    folder=OUT/'movies';folder.mkdir(parents=True,exist_ok=True)
    movie=folder/f'{row["id"]}_{layout}{suffix}_42s.mp4';proof_path=movie.with_suffix('.verification.json')
    inputs={p.name:sha(p) for p in (OUT/'analysis'/row['id']).glob('*') if p.is_file()}
    implementation={p:sha(ROOT/p) for p in ('models/intricate_band_scene.py','models/band_sampler_logic.py',
                   'models/band_performance_scene.py','models/drummer_review_schedule.py',
                   'tools/render_intricate_band_samplers.py','tools/render_band_upgrade.py')}
    if movie.exists() and proof_path.exists():
        cached=json.loads(proof_path.read_text())
        if (cached['revision']==REVISION and cached['analysis_inputs']==inputs
            and cached.get('implementation_sha256')==implementation and cached['duration_seconds']==seconds
            and cached['width']==width and cached['height']==height
            and cached['soundtrack']['source_offset_seconds']==start and sha(movie)==cached['sha256']):
            return cached
    scene=IntricateBandScene(layout);performance=SamplerPerformance(row,scene);view=SamplerView(scene,width,height)
    offset=round(start*20);count=round(seconds*20)
    assert offset+count<=performance.n,'Song is too short for the requested excerpt'
    original=OLD/'shows'/f'{row["id"]}_band/media/song.mp3';assert sha(original)==row['sha256']
    proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}',
        '-r','20','-i','-','-ss',str(start),'-i',str(original),'-map','0:v:0','-map','1:a:0','-t',str(seconds),
        '-c:v','libx264','-preset','veryfast','-crf','19','-threads','2','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','192k','-movflags','+faststart',str(movie)],stdin=subprocess.PIPE)
    began=time.monotonic()
    try:
        for frame_id in range(count):
            i=offset+frame_id
            frame=performance.caption(view.frame(performance.pose(i),performance.drums[i],performance.strikes[i],
                                                performance.hands[i],i/20,frame_id/20),i)
            if frame_id in (0,min(220,count-1),count//2,count-1):frame.save(folder/f'{movie.stem}_{frame_id:04}.png')
            proc.stdin.write(frame.tobytes())
            if frame_id and frame_id%200==0:print(movie.name,frame_id,count,round(frame_id/(time.monotonic()-began),1),'fps',flush=True)
    finally:
        proc.stdin.close();view.close()
    assert proc.wait()==0
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert int(video['nb_frames'])==count and video['r_frame_rate']=='20/1' and video['pix_fmt']=='yuv420p'
    assert abs(float(video['duration'])-seconds)<.001
    subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(movie),'-f','null','-'],check=True)
    sound=excerpt_audio_check(original,movie,start,seconds)
    levels=performance.curves['mouth_lanes'][offset:offset+count]
    proof=dict(id=row['id'],title=row['title'],layout=layout,layout_title=LAYOUTS[layout],revision=REVISION,
               file=str(movie),bytes=movie.stat().st_size,sha256=sha(movie),analysis_inputs=inputs,
               implementation_sha256=implementation,
               duration_seconds=seconds,frames=count,width=width,height=height,full_decode_passed=True,
               soundtrack=sound,source_sha256=row['sha256'],source_native_drummer=performance.drum_proof,
               drummer_geometry=view.dry.proof,geometry=scene.technical_proof,
               singer_active_frames=[int(np.count_nonzero(levels[:,k])) for k in (0,1)],
               native_xlights_playback=False,static_concept_art_video=False)
    proof_path.write_text(json.dumps(proof,indent=2)+'\n');print('VERIFIED',movie.name,flush=True)
    return proof


def main():
    p=argparse.ArgumentParser();p.add_argument('--layouts',nargs='+',default=list(LAYOUTS));p.add_argument('--ids',nargs='+',default=['00','01','02','03','05'])
    p.add_argument('--seconds',type=float,default=42);p.add_argument('--start',type=float);p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080);p.add_argument('--suffix',default='')
    args=p.parse_args();rows=json.loads((OLD/'sources.json').read_text())
    for layout in args.layouts:
        for row in rows:
            if row['id'] not in args.ids:continue
            proof=json.loads((OUT/'analysis'/row['id']/'verification.json').read_text())
            start=args.start if args.start is not None else proof['best_42s_start_seconds']
            render(row,layout,start,args.seconds,args.width,args.height,args.suffix)


if __name__=='__main__':main()
