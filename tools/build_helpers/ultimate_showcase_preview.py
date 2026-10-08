"""Geometry-backed review artifacts and optional native-FSEQ playback."""
from __future__ import annotations

import json
import math
from pathlib import Path
import struct
import subprocess
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from models.ultimate_showcase import Garden
from tools.build_helpers.ultimate_showcase import demo_envelope


def read_fseq(path: Path) -> tuple[np.ndarray,int]:
    """Read native xLights v2 (zstd/zlib/raw), including sparse channel ranges."""
    data=path.read_bytes()
    if data[:4]!=b"PSEQ" or len(data)<32 or data[7]!=2:
        raise ValueError("Expected xLights FSEQ v2")
    offset,header=struct.unpack_from("<H2xH",data,4)
    channels,frames=struct.unpack_from("<II",data,10)
    step,compression,blocks,ranges=data[18],data[20]&15,data[21]+((data[20]&240)<<4),data[22]
    if not channels or not frames or offset>len(data) or header<32:
        raise ValueError("Invalid FSEQ header")
    sparse=[];position=32+blocks*8
    for _ in range(ranges):
        start=int.from_bytes(data[position:position+3],"little")
        count=int.from_bytes(data[position+3:position+6],"little")
        sparse.append((start,count));position+=6
    payload=bytearray()
    if compression==0:
        payload.extend(data[offset:])
    else:
        for i in range(blocks):
            _,size=struct.unpack_from("<II",data,32+i*8)
            chunk=data[offset:offset+size];offset+=size
            if not size:continue
            if len(chunk)!=size:raise ValueError("Truncated FSEQ block")
            if compression==1:
                import zstandard
                payload.extend(zstandard.ZstdDecompressor().decompress(chunk))
            elif compression==2:
                payload.extend(zlib.decompress(chunk))
            else:raise ValueError(f"Unsupported FSEQ compression {compression}")
    if len(payload)!=frames*channels:
        raise ValueError(f"FSEQ data length {len(payload)} != {frames*channels}")
    packed=np.frombuffer(payload,dtype=np.uint8).reshape(frames,channels)
    if sparse:
        if sum(n for _,n in sparse)!=channels:raise ValueError("Sparse FSEQ channel mismatch")
        result=np.zeros((frames,max(s+n for s,n in sparse)),dtype=np.uint8)
        position=0
        for start,count in sparse:
            result[:,start:start+count]=packed[:,position:position+count];position+=count
    else:result=packed
    return result,step


def _font(size: int) -> ImageFont.ImageFont:
    candidates=["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for path in candidates:
        if Path(path).exists():return ImageFont.truetype(path,size)
    return ImageFont.load_default()


def _project(points: np.ndarray, width: int, height: int, yaw: float, pitch: float, *, zoom: float = 1) -> np.ndarray:
    yaw,pitch=math.radians(yaw),math.radians(pitch)
    x=points[:,0]*math.cos(yaw)-points[:,2]*math.sin(yaw)
    z=points[:,0]*math.sin(yaw)+points[:,2]*math.cos(yaw)
    y=(points[:,1]-35)*math.cos(pitch)+z*math.sin(pitch)
    scale=min(width/415,height/200)*zoom
    return np.c_[width/2+x*scale,height*.53-y*scale,z]


def _base(width: int, height: int) -> Image.Image:
    t=np.linspace(0,1,height)[:,None,None]
    pixels=np.repeat(np.array([[[6,9,22]]])*(1-t)+np.array([[[10,23,38]]])*t,width,axis=1).astype(np.uint8)
    result=Image.fromarray(pixels)
    d=ImageDraw.Draw(result)
    d.text((width*.045,height*.05),"H E L I X   A U R O R A",font=_font(round(width*.025)),fill=(222,241,250))
    d.text((width*.047,height*.105),"THE ULTIMATE SHOWCASE  /  SCULPTURE + LIGHT",font=_font(round(width*.009)),fill=(114,155,179))
    return result


def _rgb(colors: list[str]) -> np.ndarray:
    return np.array([[int(c[i:i+2],16) for i in (1,3,5)] for c in colors],dtype=np.uint8)


def render_frame(g: Garden, width: int = 1920, height: int = 1080, *, yaw: float = 7,
                 pitch: float = 18, time: float | None = None, native: np.ndarray | None = None) -> Image.Image:
    base=_base(width,height)
    # Restrained ground grid: staging and depth remain legible, without fake props.
    grid=Image.new("RGB",(width,height));draw=ImageDraw.Draw(grid)
    for z in range(-120,61,20):
        p=_project(np.array([[-190,0,z],[190,0,z]]),width,height,yaw,pitch)
        draw.line([tuple(p[0,:2]),tuple(p[1,:2])],fill=(8,17,24),width=1)
    for x in range(-180,181,30):
        p=_project(np.array([[x,0,-125],[x,0,60]]),width,height,yaw,pitch)
        draw.line([tuple(p[0,:2]),tuple(p[1,:2])],fill=(8,17,24),width=1)
    from PIL import ImageChops
    base=ImageChops.add(base,grid)
    screen=np.zeros((height,width,3),dtype=np.uint8)
    for i,m in enumerate(g.models):
        if m.kind!="pixel":continue
        colors=_rgb(m.colors)
        if native is not None:
            end=m.start-1+len(m.points)*3
            if end>len(native):raise ValueError(f"Native FSEQ missing channels for {m.name}")
            colors=native[m.start-1:end].reshape(-1,3)
        elif time is not None:
            brightness=0
            for start,end,b0,b1 in demo_envelope(m,i):
                if start<=time*1000<end:
                    brightness=(b0+(b1-b0)*(time*1000-start)/(end-start))/100
            colors=(colors*brightness).astype(np.uint8)
        p=_project(m.points,width,height,yaw,pitch)
        x,y=np.rint(p[:,0]).astype(int),np.rint(p[:,1]).astype(int)
        mask=(x>=2)&(x<width-2)&(y>=2)&(y<height-2)
        x,y,colors=x[mask],y[mask],colors[mask]
        for dx,dy,factor in [(0,0,1),(-1,0,.48),(1,0,.48),(0,-1,.48),(0,1,.48)]:
            for c in range(3):
                np.maximum.at(screen[:,:,c],(y+dy,x+dx),(colors[:,c]*factor).astype(np.uint8))
    lights=Image.fromarray(screen)
    halo=lights.filter(ImageFilter.GaussianBlur(4))
    result=ImageChops.add(base,ImageChops.add(lights,halo))
    draw=ImageDraw.Draw(result)
    draw.text((width*.045,height*.914),"36 SPIRAL TREES    /    12 DNA SCULPTURES    /    27 NATIVE FAMILIES",font=_font(round(width*.0105)),fill=(183,222,238))
    label="NATIVE XLIGHTS LIGHTING • 24 SECOND STUDY" if native is not None else "3D LAYOUT DESIGN • NIGHT VIEW"
    draw.text((width*.045,height*.949),label,font=_font(round(width*.0075)),fill=(99,140,157))
    return result


def write_previews(g: Garden, output: Path, *, video: bool = True, fseq: Path | None = None) -> dict:
    render_frame(g).save(output/"Helix_Aurora_Night.png")
    render_frame(g,yaw=-26,pitch=25).save(output/"Helix_Aurora_Perspective.png")
    write_html(g,output)
    frames,step=read_fseq(fseq) if fseq else (None,50)
    if video:
        width,height,fps=1600,900,20
        cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{width}x{height}","-r",str(fps),"-i","-",
             "-an","-c:v","libx264","-preset","fast","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(output/"Helix_Aurora_Showcase.mp4")]
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        try:
            for i in range(24*fps):
                time=i/fps
                native=frames[min(len(frames)-1,round(time*1000/step))] if frames is not None else None
                frame=render_frame(g,width,height,yaw=7+16*math.sin(time*math.pi/24),pitch=18,time=time,native=native)
                process.stdin.write(frame.tobytes())
        finally:
            process.stdin.close()
        if process.wait():raise RuntimeError("ffmpeg showcase render failed")
    return {"native_fseq":bool(fseq),"native_frame_count":len(frames) if frames is not None else None,
            "native_frame_ms":step if fseq else None,"mp4_seconds":24 if video else None}


def write_html(g: Garden, output: Path) -> None:
    data=[{"name":m.name,"type":m.display,"zone":m.zone,"design":m.design,"kind":m.kind,
           "dna":bool(m.details.get("double_helix")),"spiral":bool(m.details.get("spiral_tree")),
           "points":m.points.round(4).tolist(),"colors":m.colors} for m in g.models]
    # Inline geometry and WebGL; no CDN, fonts, server or network connection needed.
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Helix Aurora | Ultimate Showcase</title><style>
*{box-sizing:border-box}body{margin:0;background:#060c19;color:#e9f5ff;font:14px system-ui,sans-serif}canvas{display:block;width:100vw;height:100vh;touch-action:none}
header{position:absolute;top:30px;left:34px;pointer-events:none}h1{letter-spacing:.25em;font-size:30px;font-weight:400;margin:0 0 12px}header p{color:#92adbf;font-size:11px;letter-spacing:.13em}
aside{position:absolute;right:24px;top:24px;width:276px;max-height:90vh;overflow:auto;padding:22px;background:#0b1725e8;border:1px solid #223b4d;border-radius:14px}h2{font-size:15px;letter-spacing:.06em;margin:0 0 16px}
button,select{background:#142b3c;color:#bceeff;border:1px solid #2a4c60;border-radius:7px;padding:9px;margin:3px 2px;cursor:pointer;font:inherit}button.active{background:#265466;color:white}select{width:100%;margin:10px 0}
.counts{display:flex;gap:18px;margin:20px 0}.counts b{font-size:24px;color:#70f0f1}.counts span{display:block;font-size:10px;text-transform:uppercase;color:#8eabb9}#detail{line-height:1.6;color:#b4ccd8;font-size:12px}footer{position:absolute;bottom:22px;left:34px;color:#82a0b5;font-size:12px}label{font-size:12px;color:#9dbbcb}.legend{display:flex;gap:14px;color:#a7c2d0;font-size:11px;margin-top:18px}.legend i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
@media(max-width:800px){aside{width:210px;padding:12px;right:10px;top:105px}header{left:18px;top:18px}h1{font-size:22px}footer{left:18px;font-size:10px}}
</style><canvas id="scene"></canvas><header><h1>HELIX AURORA</h1><p>THE ULTIMATE SHOWCASE / SCULPTURE + LIGHT</p></header>
<aside><h2>Explore the light garden</h2><div id="filters"><button class="active" data-mode="all">Whole show</button><button data-mode="dna">DNA sculptures</button><button data-mode="spiral">Spiral forest</button><button data-mode="gallery">Native gallery</button></div>
<div class="counts"><div><b>36</b><span>Spiral trees</span></div><div><b>12</b><span>DNA forms</span></div><div><b>27</b><span>Native types</span></div></div>
<label for="model">Inspect a model</label><select id="model"><option value="">All models in view</option></select><div id="detail">A cathedral of cyan and magenta DNA, surrounded by graduated spiral groves, golden crowns and a flowing infinity promenade.</div>
<div class="legend"><span><i style="background:#64f5ff"></i>Strand A</span><span><i style="background:#ff70ce"></i>Strand B</span><span><i style="background:#ffd98a"></i>Rungs</span></div>
<div style="margin-top:20px"><button id="front">Front</button><button id="plan">Site plan</button><button id="orbit">Auto orbit</button><button id="reset">Reset</button></div></aside>
<footer>Drag to orbit · Scroll or pinch to zoom · Standalone xLights layout included</footer>
<script>const models=__DATA__;const c=document.getElementById('scene'),gl=c.getContext('webgl',{alpha:false,antialias:true});
let yaw=.12,pitch=.32,zoom=1,mode='all',selected='',orbit=false,last=0,drag=null,pinch=0;const pointers=new Map();
if(!gl){document.getElementById('detail').textContent='WebGL is unavailable. Open the included Night.png to review this layout.';throw Error('WebGL unavailable')}
function shader(type,src){let s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,`attribute vec3 pos;attribute vec3 color;uniform vec4 camera;uniform vec2 scale;uniform float density;varying vec3 col;void main(){float x=pos.x*cos(camera.x)-pos.z*sin(camera.x);float z=pos.x*sin(camera.x)+pos.z*cos(camera.x);float y=(pos.y-35.)*cos(camera.y)+z*sin(camera.y);gl_Position=vec4((x*scale.x-.16)*camera.z,y*scale.y*camera.z,-z/500.,1.);gl_PointSize=2.9*density*sqrt(camera.z);col=color;}`));
gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`precision mediump float;varying vec3 col;void main(){float d=length(gl_PointCoord-.5)*2.;if(d>1.)discard;gl_FragColor=vec4(col*pow(1.-d,1.2),1.);}`));gl.linkProgram(program);gl.useProgram(program);
const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);let count=0;
for(const [attr,offset]of [['pos',0],['color',12]]){let loc=gl.getAttribLocation(program,attr);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,3,gl.FLOAT,false,24,offset)}
const camera=gl.getUniformLocation(program,'camera'),scale=gl.getUniformLocation(program,'scale'),density=gl.getUniformLocation(program,'density');gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE);gl.clearColor(.025,.044,.081,1);
function visible(m){return mode==='all'||mode==='dna'&&m.dna||mode==='spiral'&&m.spiral||mode==='gallery'&&!m.dna&&!m.spiral}
function update(){let values=[],shown=models.filter(visible);for(let m of shown){if(m.kind!=='pixel')continue;for(let i=0;i<m.points.length;i++){const col=m.colors[i],dim=selected&&m.name!==selected?.09:1;values.push(...m.points[i],...([1,3,5].map(k=>parseInt(col.slice(k,k+2),16)/255*dim)))}}gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(values),gl.STATIC_DRAW);count=values.length/6;
 const list=document.getElementById('model');list.innerHTML='<option value="">All models in view</option>';for(let m of shown){let o=document.createElement('option');o.value=m.name;o.textContent=m.name.replace(/^HX_/,'').replaceAll('_',' ');list.appendChild(o)}list.value=selected;
 const m=models.find(m=>m.name===selected);document.getElementById('detail').textContent=m?m.design+' · '+m.type+' · '+m.points.length.toLocaleString()+(m.kind==='pixel'?' pixels':' control channels. Review this control fixture in xLights.'):'108 models across 27 native families. Choose a sculpture to see its design and illuminate it in context.';
}
function render(t){let dpr=Math.min(devicePixelRatio,2);if(c.width!==Math.round(innerWidth*dpr)||c.height!==Math.round(innerHeight*dpr)){c.width=Math.round(innerWidth*dpr);c.height=Math.round(innerHeight*dpr);gl.viewport(0,0,c.width,c.height)}if(orbit&&last)yaw+=(t-last)*.00007;last=t;gl.clear(gl.COLOR_BUFFER_BIT);gl.uniform4f(camera,yaw,pitch,zoom,0);let aspect=c.width/c.height;gl.uniform2f(scale,1/235,aspect/235);gl.uniform1f(density,dpr);gl.drawArrays(gl.POINTS,0,count);requestAnimationFrame(render)}
c.addEventListener('pointerdown',e=>{pointers.set(e.pointerId,[e.clientX,e.clientY]);drag=[e.clientX,e.clientY];pinch=0;c.setPointerCapture(e.pointerId);orbit=false});function release(e){pointers.delete(e.pointerId);drag=null;pinch=0}c.addEventListener('pointerup',release);c.addEventListener('pointercancel',release);c.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,[e.clientX,e.clientY]);if(pointers.size===2){const [a,b]=[...pointers.values()];const distance=Math.hypot(a[0]-b[0],a[1]-b[1]);if(pinch)zoom=Math.min(8,Math.max(.4,zoom*distance/pinch));pinch=distance;drag=null}else if(drag){yaw+=(e.clientX-drag[0])*.006;pitch=Math.min(1.56,Math.max(-.3,pitch+(e.clientY-drag[1])*.006));drag=[e.clientX,e.clientY]}});c.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.min(8,Math.max(.4,zoom*Math.exp(-e.deltaY*.001)))},{passive:false});
document.getElementById('model').onchange=e=>{selected=e.target.value;update()};document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;selected='';document.querySelectorAll('[data-mode]').forEach(v=>v.classList.toggle('active',v===b));update()});
document.getElementById('front').onclick=()=>{yaw=0;pitch=0;orbit=false};document.getElementById('plan').onclick=()=>{yaw=0;pitch=1.5;orbit=false};document.getElementById('orbit').onclick=()=>orbit=!orbit;document.getElementById('reset').onclick=()=>{yaw=.12;pitch=.32;zoom=1;orbit=false;selected='';update()};update();requestAnimationFrame(render);
</script></html>'''
    html=html.replace("__DATA__",json.dumps(data,separators=(",",":")))
    (output/"Helix_Aurora_3D.html").write_text(html,encoding="utf-8")
