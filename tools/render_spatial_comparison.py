"""Six real native xLights FSEQ shows, original soundtrack, orbiting XYZ cameras."""
from __future__ import annotations
import argparse,json,math,time,uuid
from pathlib import Path
import numpy as np
import moderngl
from PIL import Image,ImageDraw,ImageFont
from models.review_spatial_worlds import build_world,TITLES
from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.render_refined_helix_band import encoder
from tools.render_approval_revision import sha
from core.output_provenance import brand_frame,stamp_mp4

VERT='''#version 330
in vec3 pos;in vec3 col;uniform mat4 camera;out vec3 light;
void main(){gl_Position=camera*vec4(pos,1);gl_PointSize=2.4;light=col;}'''
FRAG='''#version 330
in vec3 light;out vec4 frag;
void main(){float d=length(gl_PointCoord-vec2(.5));if(d>.5)discard;frag=vec4(pow(light,vec3(.5))*(1.-.25*d),1);}'''


def camera(width,height,t):
    yaw=math.radians(8+12*math.sin(t*math.pi/36));pitch=math.radians(30)
    eye=np.array((360*math.sin(yaw)*math.cos(pitch),30+360*math.sin(pitch),360*math.cos(yaw)*math.cos(pitch)))
    target=np.array((0,30,0));forward=target-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
    view=np.eye(4);view[:3,:3]=np.vstack((right,up,-forward));view[:3,3]=-view[:3,:3]@eye
    f=1/math.tan(math.radians(42)/2);p=np.zeros((4,4));p[0,0]=f/(width/height);p[1,1]=f;p[2,2]=-1.0002;p[2,3]=-.2;p[3,2]=-1
    return (p@view).astype('f4')


class PixelView:
    def __init__(self,ctx,g,w=640,h=450):
        self.ctx=ctx;self.w=w;self.h=h;points=[];indices=[];accolors=[];acmask=[]
        for m in g.models:
            if m.kind=='pixel':
                points.extend(m.points);indices.extend((m.start-1+np.arange(len(m.points))*3).tolist())
                acmask.extend([False]*len(m.points));accolors.extend([[1,1,1]]*len(m.points))
            elif m.kind=='ac':
                points.extend(m.points);indices.extend((m.start-1+np.array(m.details['point_circuits'])-1).tolist())
                acmask.extend([True]*len(m.points));accolors.extend([[1,1,1]]*len(m.points))
        self.points=np.asarray(points,'f4');self.indices=np.asarray(indices);self.acmask=np.array(acmask);self.accolors=np.asarray(accolors,'f4')
        self.program=ctx.program(vertex_shader=VERT,fragment_shader=FRAG)
        self.pbuf=ctx.buffer(self.points.tobytes());self.cbuf=ctx.buffer(reserve=len(self.points)*12)
        self.vao=ctx.vertex_array(self.program,[(self.pbuf,'3f','pos'),(self.cbuf,'3f','col')])
        self.fbo=ctx.simple_framebuffer((w,h),components=3)
    def frame(self,values,t):
        colors=np.zeros((len(self.indices),3),'f4')
        rgb=~self.acmask
        colors[rgb]=values[self.indices[rgb,None]+np.arange(3)]/255
        if self.acmask.any():colors[self.acmask]=values[self.indices[self.acmask],None]/255*self.accolors[self.acmask]
        self.cbuf.write(colors.tobytes());self.program['camera'].write(getattr(self,'camera_callback',camera)(self.w,self.h,t).T.tobytes())
        self.fbo.use();self.fbo.clear(.015,.030,.055,1);self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.disable(moderngl.DEPTH_TEST);self.ctx.enable(moderngl.BLEND);self.ctx.blend_func=(moderngl.ONE,moderngl.ONE);self.ctx.blend_equation=moderngl.MAX
        self.vao.render(moderngl.POINTS)
        return Image.frombytes('RGB',(self.w,self.h),self.fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def render(root,eid):
    rows=json.loads((root/'sources/selected_excerpts.json').read_text());row=next(x for x in rows if x['excerpt_id']==eid)
    audio=root/'sources'/eid/'audio.wav';ctx=moderngl.create_standalone_context(backend='egl');views=[];channels=[];proof=[]
    for k in range(6):
        folder=root/'shows'/eid/('World_'+str(k+1));g=build_world(k);frames,step=read_fseq(folder/'Performance.fseq')
        assert len(frames)==720 and step==50
        views.append(PixelView(ctx,g));channels.append(frames)
        proof.append(dict(title=TITLES[k],fseq=str((folder/'Performance.fseq').relative_to(root)),
            fseq_sha256=sha(folder/'Performance.fseq'),layout_sha256=sha(folder/'xlights_rgbeffects.xml'),native_xlights_rendered=True))
    path=root/'videos'/(('03' if eid=='E03' else '04')+'_'+eid+'_Native_3D_Comparison.mp4');path.parent.mkdir(exist_ok=True)
    temp=path.with_name(path.stem+'.'+uuid.uuid4().hex+'.rendering.mp4');writer=encoder(temp,1920,1080,20,audio,0,36)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21)
    started=time.monotonic();snap=root/'diagnostics'/path.stem;snap.mkdir(parents=True,exist_ok=True)
    try:
        for i in range(720):
            image=Image.new('RGB',(1920,1080),'#06101D');d=ImageDraw.Draw(image)
            d.text((24,20),'HELIX  /  SIX NATIVE 3D WORLDS  /  '+Path(row['filename']).stem,font=font,fill='#E3EDF5')
            for k,view in enumerate(views):
                panel=view.frame(channels[k][i],i/20);draw=ImageDraw.Draw(panel);draw.rectangle((0,0,640,36),fill='#0D1D2A')
                draw.text((12,5),TITLES[k],font=small,fill='#D5E9F5');image.paste(panel,((k%3)*640,80+(k//3)*450))
            d.text((24,1003),f'Source {row["start_seconds"]+i/20:06.2f}s  /  Same 50 ms clock in every panel  /  Actual native FSEQ channels',font=small,fill='#BDD7E2')
            d.text((24,1040),'88 MIDI rungs  •  Spiral groves  •  Moiré planes  •  Perspective tunnels  •  Integrated snowman stages',font=small,fill='#8FB3C8')
            image=brand_frame(image);writer.stdin.write(image.tobytes())
            if i in (40,240,380,520,700):image.save(snap/f'frame_{i:04}.jpg',quality=94)
            if i%180==0:print('NATIVE_COMPARISON',eid,i,round(time.monotonic()-started,1),flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();temp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
        ctx.release()
    if writer.wait():raise RuntimeError('Comparison encoding failed')
    temp.replace(path);stamp_mp4(path)
    receipt=dict(file=str(path.relative_to(root)),excerpt_id=eid,sha256=sha(path),excerpt_sha256=sha(audio),
        original_audio_sha256=row['sha256'],source_start=row['start_seconds'],source_end=row['end_seconds'],
        frames=720,fps=20,seconds=36,panels=6,all_panels_same_source_clock=True,layouts=proof,
        native_xlights_rendered=True,review_camera_motion='8..20 degree yaw, 30 degree elevation; display gamma 2.0, max-composited native values; review camera, not motorized hardware',
        renderer_sha256=sha(Path(__file__)))
    path.with_suffix('.render.json').write_text(json.dumps(receipt,indent=2)+'\n');print('COMPLETE',path,flush=True)
    return path

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--id',choices=['E03','E14'],required=True);args=a.parse_args();render(args.root,args.id)
