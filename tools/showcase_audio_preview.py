"""Cached projection of actual native FSEQ pixels, with the source soundtrack."""
from __future__ import annotations

import math
from pathlib import Path
import subprocess
import time

import numpy as np
from PIL import Image,ImageChops,ImageDraw,ImageFilter

from tools.build_helpers.ultimate_showcase_preview import _base,_font,_project,read_fseq,render_frame


class NativeSongView:
    def __init__(self,g,song:str,width=1280,height=720,*,halo_scale=1):
        self.width,self.height=width,height
        self.halo_scale=halo_scale
        channels=max(m.start-1+m.channels for m in g.models)
        self.base=render_frame(g,width,height,yaw=7,pitch=18,native=np.zeros(channels,dtype=np.uint8))
        clean=_base(width,height,g.title)
        bottom=int(height*.935);self.base.paste(clean.crop((0,bottom,width,height)),(0,bottom))
        draw=ImageDraw.Draw(self.base)
        draw.text((width*.045,height*.95),song+'  /  NATIVE XLIGHTS • ORIGINAL SONG AUDIO',font=_font(round(width*.009)),fill=(134,180,198))
        locations=[];indices=[]
        for m in g.models:
            if m.kind!='pixel':continue
            p=_project(m.points,width,height,7,18);x,y=np.rint(p[:,:2]).astype(int).T
            keep=(x>=2)&(x<width-2)&(y>=2)&(y<height-2)
            locations.extend((y[keep]*width+x[keep]).tolist())
            indices.extend((m.start-1+np.arange(len(m.points))[keep]*3).tolist())
        locations=np.asarray(locations);self.indices=np.asarray(indices)
        self.order=np.argsort(locations,kind='stable');ordered=locations[self.order]
        self.starts=np.r_[0,np.flatnonzero(np.diff(ordered))+1]
        self.unique=ordered[self.starts]

    def frame(self,values:np.ndarray)->Image.Image:
        colors=values[self.indices[:,None]+np.arange(3)]
        merged=np.maximum.reduceat(colors[self.order],self.starts,axis=0)
        screen=np.zeros((self.height*self.width,3),dtype=np.uint8)
        screen[self.unique]=merged;screen=screen.reshape(self.height,self.width,3)
        # Same five-pixel dot footprint as the original compositor; collisions
        # use maximum, never sums that would invent brightness.
        small=(screen*.48).astype(np.uint8);lights=screen.copy()
        np.maximum(lights[:,1:],small[:,:-1],out=lights[:,1:])
        np.maximum(lights[:,:-1],small[:,1:],out=lights[:,:-1])
        np.maximum(lights[1:],small[:-1],out=lights[1:])
        np.maximum(lights[:-1],small[1:],out=lights[:-1])
        image=Image.fromarray(lights)
        if self.halo_scale==1:
            glow=image.filter(ImageFilter.GaussianBlur(4))
        else:
            scale=self.halo_scale
            glow=image.resize((self.width//scale,self.height//scale),Image.Resampling.BOX).filter(
                ImageFilter.GaussianBlur(4/scale)).resize(image.size,Image.Resampling.BILINEAR)
        return ImageChops.add(self.base,ImageChops.add(image,glow))


def render_native_song(g,fseq:Path,audio:Path,output:Path,duration_s:float,*,fps=20,width=1280,height=720)->dict:
    frames,step=read_fseq(fseq);view=NativeSongView(g,audio.stem,width,height,halo_scale=2)
    total=int(math.ceil(duration_s*fps));started=time.monotonic()
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}',
             '-r',str(fps),'-i','-','-i',str(audio),'-map','0:v:0','-map','1:a:0','-t',str(duration_s),
             '-c:v','libx264','-preset','veryfast','-crf','22','-threads','1','-pix_fmt','yuv420p',
             '-c:a','aac','-b:a','192k','-movflags','+faststart',str(output)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for i in range(total):
            index=min(len(frames)-1,int(round(i/fps*1000/step)))
            process.stdin.write(view.frame(frames[index]).tobytes())
    finally:process.stdin.close()
    if process.wait():raise RuntimeError('Native-song video encoder failed')
    return {'video_seconds':duration_s,'fps':fps,'width':width,'height':height,'native_frames':len(frames),
            'native_frame_ms':step,'render_wall_seconds':round(time.monotonic()-started,2),'soundtrack':audio.name}
