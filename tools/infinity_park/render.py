"""Depth-tested architectural renders and video from actual native FSEQ RGB values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

import moderngl
import numpy as np
from PIL import Image
import trimesh

from .export import native_xyz


MESH_VERTEX = """
#version 330
uniform mat4 camera;
uniform mat4 light_camera;
in vec3 position;
in vec3 normal;
out vec3 world_position;
out vec3 world_normal;
out vec4 shadow_position;
void main() {
    gl_Position = camera * vec4(position, 1);
    shadow_position = light_camera * vec4(position, 1);
    world_position = position;
    world_normal = normal;
}
"""

MESH_FRAGMENT = """
#version 330
uniform sampler2D shadow_map;
uniform vec3 material;
uniform vec3 eye;
uniform vec3 sun;
uniform vec2 finish;
uniform float night;
in vec3 world_position;
in vec3 world_normal;
in vec4 shadow_position;
out vec4 pixel;
void main() {
    vec3 p = world_position;
    vec3 n = normalize(world_normal);
    vec3 view = normalize(eye - p);
    vec3 half_angle = normalize(sun + view);
    vec3 coord = shadow_position.xyz / shadow_position.w * 0.5 + 0.5;
    float shadow = 0.0;
    for (int i=-1; i<=1; i++) {
        for (int j=-1; j<=1; j++) {
            float caster = texture(shadow_map, coord.xy+vec2(i,j)/2048.0).r;
            shadow += step(coord.z-0.0018, caster);
        }
    }
    shadow = 0.44+0.56*shadow/9.0;
    float lit = max(dot(n,sun),0.0)*shadow;
    float fill = max(dot(n,normalize(vec3(0.08,0.68,0.6))),0.0);
    float up = n.y * 0.5 + 0.5;
    vec3 warm = vec3(1.0,0.93,0.79);
    vec3 blue = vec3(0.42,0.62,1.0);
    vec3 env = mix(vec3(.56,.64,.77),vec3(.19,.24,.44),night);
    vec3 tint = env*(0.58+up*0.24) + warm*lit*mix(.69,.16,night)
                + mix(vec3(.22,.23,.25),blue*.48,night)*fill;
    float glint = pow(max(dot(n,half_angle),0.0),mix(72.0,8.0,finish.y));
    float fresnel = pow(1.0-max(dot(n,view),0.0),3.2);
    vec3 base = material*tint;
    base += finish.x*(.32+fresnel*.78)*(mix(vec3(.29,.48,.68),vec3(.10,.24,.44),night))*up;
    base += warm * glint*(0.04+finish.x*.25)*shadow;
    float haze = smoothstep(120.0,430.0,distance(p,eye))*mix(.13,.12,night);
    pixel = vec4(mix(base, mix(vec3(.45,.59,.70),vec3(.09,.13,.22),night),haze),1.0);
}
"""

PIXEL_VERTEX = """
#version 330
uniform mat4 camera;
uniform float pixels_per_metre;
uniform float glow_pass;
in vec3 position;
in float radius;
in vec3 color;
out vec3 emitted;
void main() {
    gl_Position = camera * vec4(position, 1);
    gl_PointSize = max(1.85, radius * pixels_per_metre * 2.0) * (1.0 + glow_pass*3.1);
    emitted = color;
}
"""

PIXEL_FRAGMENT = """
#version 330
uniform float glow_pass;
in vec3 emitted;
out vec4 pixel;
void main() {
    float r = length(gl_PointCoord - vec2(.5)) * 2.0;
    float intensity = max(emitted.r,max(emitted.g,emitted.b));
    if (intensity < 0.008 || r >= 1.0) discard;
    float opacity = mix((1.0-smoothstep(.55,1.0,r))*.94,
                        exp(-r*r*5.5)*.19,glow_pass);
    vec3 color = pow(emitted, vec3(.79));
    if (glow_pass < .5) color = mix(color,vec3(pow(intensity,.79)), (1.0-r)*0.17);
    pixel = vec4(color,opacity);
}
"""


def camera_matrix(camera, aspect):
    eye = native_xyz(camera["eye"]).astype(float)
    target = native_xyz(camera["target"]).astype(float)
    back = eye-target
    back /= np.linalg.norm(back)
    right = np.cross((0.,1.,0.),back)
    right /= np.linalg.norm(right)
    axes = np.array((right,np.cross(back,right),back))
    view = np.eye(4)
    view[:3,:3] = axes
    view[:3,3] = -axes@eye
    width=camera["width"]
    ortho = np.diag((2/width,2*aspect/width,-2/800,1.))
    ortho[2,3] = -1
    return eye, ortho@view


def matrix_bytes(matrix):
    return matrix.T.astype("f4").tobytes()


class Renderer:
    def __init__(self, show, width, height):
        self.ctx=moderngl.create_standalone_context(backend="egl")
        self.width,self.height=width,height
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        self.color=self.ctx.texture((width,height),4)
        self.depth=self.ctx.depth_renderbuffer((width,height))
        self.frame=self.ctx.framebuffer([self.color],self.depth)
        self.background=self.ctx.framebuffer([self.ctx.texture((width,height),4)],
                                             self.ctx.depth_renderbuffer((width,height)))
        self.mesh=self.ctx.program(vertex_shader=MESH_VERTEX,fragment_shader=MESH_FRAGMENT)
        self.lights=self.ctx.program(vertex_shader=PIXEL_VERTEX,fragment_shader=PIXEL_FRAGMENT)
        self.shadow_program=self.ctx.program(
            vertex_shader="#version 330\nuniform mat4 camera; in vec3 position; void main(){gl_Position=camera*vec4(position,1);}",
            fragment_shader="#version 330\nvoid main(){}")
        self.shadow=self.ctx.depth_texture((2048,2048))
        self.shadow.compare_func=""
        self.shadow.repeat_x=self.shadow.repeat_y=False
        self.shadow_fbo=self.ctx.framebuffer(depth_attachment=self.shadow)
        self.shadow_geometry=[]
        self.geometry=[]
        scene=trimesh.load_scene(show/"assets/Infinity_Park.glb", process=False)
        for polygon in scene.geometry.values():
            vertices=polygon.vertices[polygon.faces]
            # Split face normals preserve trim, molded features and broad roof facets.
            normals=np.repeat(polygon.face_normals[:,None,:],3,axis=1)
            data=self.ctx.buffer(np.concatenate((vertices,normals),axis=2).astype("f4").tobytes())
            vao=self.ctx.vertex_array(self.mesh,[(data,"3f 3f","position","normal")])
            shadow=self.ctx.vertex_array(self.shadow_program,[(data,"3f 12x","position")])
            mat=polygon.visual.material
            self.geometry.append((vao,tuple(mat.baseColorFactor[:3]/255),
                                  (float(mat.metallicFactor),float(mat.roughnessFactor))))
            self.shadow_geometry.append(shadow)
        bindings=np.load(show/"rgb_bindings.npz",allow_pickle=False)
        self.static_rgb=bindings["static_rgb"]
        self.count=len(self.static_rgb)
        points=native_xyz(bindings["positions"])
        self.pixel_geometry=self.ctx.buffer(np.c_[points,bindings["radii"]].astype("f4").tobytes())
        self.pixel_colors=self.ctx.buffer(reserve=self.count*3*4)
        self.pixel_vao=self.ctx.vertex_array(self.lights,[(self.pixel_geometry,"3f 1f","position","radius"),
                                                        (self.pixel_colors,"3f","color")])
        self.sun,self.sun_matrix=camera_matrix({"eye":(-173,-155,286),"target":(0,0,0),"width":378},1)
        self.sun /= np.linalg.norm(self.sun)
        self.shadow_fbo.use()
        self.shadow_fbo.clear(depth=1)
        self.shadow_program["camera"].write(matrix_bytes(self.sun_matrix))
        for vao in self.shadow_geometry:
            vao.render()

    def set_camera(self,camera,night):
        eye,matrix=camera_matrix(camera,self.width/self.height)
        self.background.use()
        self.ctx.depth_mask=True
        self.background.clear(*((.042,.06,.102,1) if night else (.39,.54,.65,1)),depth=1)
        self.shadow.use(0)
        self.mesh["camera"].write(matrix_bytes(matrix))
        self.mesh["light_camera"].write(matrix_bytes(self.sun_matrix))
        self.mesh["sun"].value=tuple(self.sun)
        self.mesh["eye"].value=tuple(eye)
        self.mesh["night"].value=float(night)
        self.mesh["shadow_map"].value=0
        for vao,color,finish in self.geometry:
            self.mesh["material"].value=color
            self.mesh["finish"].value=finish
            vao.render()
        self.lights["camera"].write(matrix_bytes(matrix))
        self.lights["pixels_per_metre"].value=self.width/camera["width"]

    def render(self,colors=None):
        self.ctx.copy_framebuffer(self.frame,self.background)
        if colors is not None:
            self.frame.use()
            self.pixel_colors.write((colors.astype("f4")/255).tobytes())
            self.ctx.enable(moderngl.BLEND)
            self.ctx.depth_mask=False
            self.ctx.blend_func=moderngl.SRC_ALPHA, moderngl.ONE
            self.lights["glow_pass"].value=1.
            self.pixel_vao.render(mode=moderngl.POINTS)
            self.ctx.blend_func=moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
            self.lights["glow_pass"].value=0.
            self.pixel_vao.render(mode=moderngl.POINTS)
            self.ctx.disable(moderngl.BLEND)
            self.ctx.depth_mask=True
        return self.frame.read(components=3,alignment=1)

    def still(self, output, colors=None):
        Image.frombytes("RGB",(self.width,self.height),self.render(colors)).transpose(
            Image.Transpose.FLIP_TOP_BOTTOM).save(output)


def stills(renderer, manifest, output, cameras):
    for name in cameras:
        camera=manifest["cameras"][name]
        renderer.set_camera(camera,False)
        renderer.still(output/f"{name}_Day.png")
        if name not in ("plan","front","side"):
            renderer.set_camera(camera,True)
            renderer.still(output/f"{name}_Night.png",renderer.static_rgb)


def native_frames(path, channels, seconds):
    from tools.layout_bench.xlights_fseq import load_fseq
    source=load_fseq(path)
    if source.sparse_start or source.channels<channels:
        raise ValueError(f"FSEQ covers {source.channels} channels from {source.sparse_start}, expected {channels} from 0")
    if abs(source.frames*source.step_ms/1000-seconds)>source.step_ms/1000+.002:
        raise ValueError("Audio and native sequence duration differ")
    iterator=iter(source.rows())
    row=next(iterator)
    t=0
    for frame in range(round(seconds*30)):
        requested=min(frame*1000//(30*source.step_ms),source.frames-1)
        while t<requested:
            row=next(iterator)
            t+=1
        yield row[:channels].reshape(-1,3)


def render_video(renderer, manifest, fseq, audio, output, *, camera, production=False):
    from core.output_provenance import sha256
    if production and sha256(audio)!="efdfe69328b8458ff9b405d091af9d5cb9202e3f53846f1ac0de07814f28739d":
        raise ValueError("Production render requires the verified original WAV")
    duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
                                           "-of","csv=p=0",str(audio)]))
    renderer.set_camera(manifest["cameras"][camera],True)
    ffmpeg=["ffmpeg","-nostdin","-v","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",
            f"{renderer.width}x{renderer.height}","-framerate","30","-i","pipe:0","-i",str(audio),
            "-vf","vflip","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","192k","-map","0:v","-map","1:a","-movflags","+faststart",str(output)]
    start=time.perf_counter()
    nonblank=changed=white=0
    previous=None
    district_nodes={name:[] for name in manifest["districts"]}
    for model in manifest["models"]:
        district_nodes[model["district"]].append(slice((model["first_channel"]-1)//3,model["last_channel"]//3))
    active={name:set() for name in district_nodes}
    proc=subprocess.Popen(ffmpeg,stdin=subprocess.PIPE)
    try:
        for index, row in enumerate(native_frames(fseq,renderer.count*3,duration)):
            nonblank += bool(row.any())
            changed += previous is None or bool(np.any(row!=previous))
            white += float(np.mean(np.min(row,axis=1)>202))>.6
            if index%3==0:
                for name, segments in district_nodes.items():
                    active[name].update(i for i, s in enumerate(segments) if row[s].any())
            proc.stdin.write(renderer.render(row))
            previous=row
        proc.stdin.close()
        if proc.wait()!=0:
            raise RuntimeError("FFmpeg encoding failed")
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(output),"-f","null","-"],check=True)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format",
                                             "-of","json",str(output)]))
    picture=next(s for s in probe["streams"] if s["codec_type"]=="video")
    sound=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    frames=round(duration*30)
    if (picture["codec_name"]!="h264" or sound["codec_name"]!="aac" or
            int(picture["nb_frames"])!=frames or picture["avg_frame_rate"]!="30/1" or
            abs(float(picture["duration"])-float(sound["duration"]))>.05):
        raise ValueError("Video format, frame count, or encoded sync failed")
    report={"owner_approved":False,"camera":camera,"audio_sha256":sha256(audio),"fseq_sha256":sha256(fseq),
            "frames":frames,"frames_with_native_light":nonblank,"native_changes":changed,
            "possible_global_white_frames":white,"active_models_by_district":{k:len(v) for k,v in active.items()},
            "seconds_to_render":round(time.perf_counter()-start,3),"encoder_probe":probe}
    output.with_suffix(".json").write_text(json.dumps(report,indent=2)+"\n")
    if not nonblank or white:
        raise ValueError("Native show is dark or has a global white event")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("show",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--camera",action="append")
    parser.add_argument("--fseq",type=Path)
    parser.add_argument("--audio",type=Path)
    parser.add_argument("--production",action="store_true")
    parser.add_argument("--width",type=int,default=1920)
    args=parser.parse_args()
    if bool(args.fseq)!=bool(args.audio):
        parser.error("Supply both --fseq and --audio for native lighting video")
    manifest=json.loads((args.show/"scene_manifest.json").read_text())
    cameras=args.camera or (["overview"] if args.fseq else list(manifest["cameras"]))
    args.output.mkdir(parents=True,exist_ok=True)
    renderer=Renderer(args.show,args.width,args.width*9//16)
    if not args.fseq:
        stills(renderer,manifest,args.output,cameras)
        return
    for name in cameras:
        render_video(renderer,manifest,args.fseq,args.audio,args.output/f"Infinity_{name}.mp4",
                     camera=name,production=args.production)


if __name__=="__main__":
    main()
