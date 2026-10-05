from __future__ import annotations

import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"fixtures/band_geometry/source/drummerbg.png"
MANIFEST=ROOT/"fixtures/band_geometry/drummer_v3_png_layer_manifest.json"
LAYER_DIR=ROOT/"fixtures/band_geometry/layers"
TARGET_TO_LAYER={
 "HX_SNOWMAN_DRUMMER_V3_KICK":"drummer_hit_kick.png",
 "HX_SNOWMAN_DRUMMER_V3_SNARE":"drummer_hit_snare.png",
 "HX_SNOWMAN_DRUMMER_V3_HI_HAT":"drummer_hit_hi_hat.png",
 "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH":"drummer_hit_left_tom.png",
 "HX_SNOWMAN_DRUMMER_V3_TOM_MID":"drummer_hit_right_tom.png",
 "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR":"drummer_hit_floor_tom.png",
 "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT":"drummer_hit_left_crash.png",
 "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT":"drummer_hit_right_crash.png",
}

def parse_effects(xsq:Path):
 root=ET.parse(xsq).getroot(); out=[]
 for element in root.findall("./ElementEffects/Element"):
  name=element.get("name","")
  if name not in TARGET_TO_LAYER: continue
  for layer in element.findall("EffectLayer"):
   for fx in layer.findall("Effect"):
    out.append((int(float(fx.get("startTime","0"))),int(float(fx.get("endTime","0"))),name,fx.get("sourcePose","")))
 return sorted(out)

def load_canonical_asset():
 if not SOURCE.exists(): raise SystemExit(f"FAIL: canonical drummer source image missing: {SOURCE}")
 if not MANIFEST.exists(): raise SystemExit(f"FAIL: canonical drummer layer manifest missing: {MANIFEST}")
 source=Image.open(SOURCE).convert("RGBA")
 manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
 required={str(layer["file"]) for layer in manifest.get("layers",[]) if layer.get("file")}
 layers={}
 for filename in sorted(required):
  path=LAYER_DIR/filename
  if not path.exists(): raise SystemExit(f"FAIL: canonical drummer visual layer missing: {path}")
  layers[filename]=Image.open(path).convert("RGBA")
 # Floor tom is a distinct visual layer derived once from the authored right-tom contact artwork.
 # It is cached as a separate layer so TOM_FLOOR can never accidentally light TOM_MID.
 right=layers.get("drummer_hit_right_tom.png")
 if right is None: raise SystemExit("FAIL: authored right-tom layer missing; cannot derive canonical floor-tom layer")
 floor=Image.new("RGBA",right.size,(0,0,0,0))
 floor.alpha_composite(right,(0,int(right.height*.105)))
 layers["drummer_hit_floor_tom.png"]=floor
 return source,layers

def draw_frame(source,layers,active,width,height,t_ms,duration_ms,font):
 base=source.copy(); base.thumbnail((width,height),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",(width,height),(4,7,12,255)); x=(width-base.width)//2; y=(height-base.height)//2; canvas.alpha_composite(base,(x,y))
 for target,intensity in active.items():
  if intensity<=.02: continue
  layer=layers.get(TARGET_TO_LAYER[target])
  if layer is None: raise SystemExit(f"FAIL: canonical visual layer missing for {target}")
  overlay=layer
  if intensity<.99:
   alpha=overlay.getchannel("A").point(lambda a:int(a*max(0.,min(1.,intensity))))
   overlay=overlay.copy(); overlay.putalpha(alpha)
  if overlay.size!=base.size: overlay=overlay.resize(base.size,Image.Resampling.LANCZOS)
  canvas.alpha_composite(overlay,(x,y))
 d=ImageDraw.Draw(canvas); d.rounded_rectangle((18,16,width-18,88),radius=12,fill=(5,9,16,205),outline=(120,140,170,210),width=2)
 labels={
  "HX_SNOWMAN_DRUMMER_V3_KICK":"KICK","HX_SNOWMAN_DRUMMER_V3_SNARE":"SNARE","HX_SNOWMAN_DRUMMER_V3_HI_HAT":"HI-HAT",
  "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH":"TOM HIGH","HX_SNOWMAN_DRUMMER_V3_TOM_MID":"TOM MID","HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR":"TOM FLOOR",
  "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT":"CRASH L","HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT":"CRASH R"}
 active_names=[labels.get(t,t) for t,v in active.items() if v>.02]
 d.text((34,30),"HELIX — CANONICAL DRUMMER V3",font=font,fill=(245,248,255,255)); d.text((34,53),"ACTIVE: "+(", ".join(active_names) if active_names else "idle"),font=font,fill=(255,215,150,255)); d.text((width-190,30),f"{t_ms/1000:.2f}s / {duration_ms/1000:.2f}s",font=font,fill=(190,210,235,255)); return canvas.convert("RGB")

def _audio_duration_ms(audio:Path)->int:
 ff=imageio_ffmpeg.get_ffmpeg_exe(); proc=subprocess.run([ff,"-v","error","-show_entries","format=duration","-of","json",str(audio)],capture_output=True,text=True)
 if proc.returncode==0:
  try:
   duration=float(json.loads(proc.stdout)["format"]["duration"])
   if duration>0:return int(round(duration*1000.))
  except (KeyError,TypeError,ValueError,json.JSONDecodeError): pass
 raise RuntimeError(f"Unable to determine audio duration for {audio}")

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument("xsq",type=Path); ap.add_argument("--audio",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--fps",type=int,default=30); ap.add_argument("--duration",type=float,default=0.); args=ap.parse_args()
 source,layers=load_canonical_asset(); effects=parse_effects(args.xsq)
 if not effects: raise SystemExit("FAIL: no canonical HX_SNOWMAN_DRUMMER_V3 submodel effects found")
 required_targets=set(TARGET_TO_LAYER); found={e[2] for e in effects}
 if not (found & required_targets): raise SystemExit("FAIL: XSQ contains no canonical drummer targets")
 audio_duration_ms=_audio_duration_ms(args.audio); effect_end_ms=max(e[1] for e in effects)
 if effect_end_ms<int(audio_duration_ms*.95): raise SystemExit(f"FAIL: drummer XSQ ends at {effect_end_ms} ms, but audio is {audio_duration_ms} ms")
 duration_ms=audio_duration_ms if args.duration<=0 else min(int(args.duration*1000),audio_duration_ms)
 print(f"CANONICAL-ASSET MODE: source={SOURCE} effects={len(effects)} targets={sorted(found)} audio_duration_ms={audio_duration_ms}")
 out=args.output; silent=out.with_suffix(".silent.mp4"); font=ImageFont.load_default(); writer=imageio.get_writer(silent,fps=args.fps,codec="libx264",quality=8,macro_block_size=None)
 try:
  for i in range(int(duration_ms/1000*args.fps)):
   t=int(i*1000/args.fps); active={name:0. for name in TARGET_TO_LAYER}
   for start,end,name,_pose in effects:
    if start<=t<end: active[name]=max(active[name],1.)
   writer.append_data(np.asarray(draw_frame(source,layers,active,960,540,t,duration_ms,font)))
 finally: writer.close()
 ff=imageio_ffmpeg.get_ffmpeg_exe(); proc=subprocess.run([ff,"-y","-i",str(silent),"-i",str(args.audio),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-shortest","-movflags","+faststart",str(out)],capture_output=True,text=True)
 if proc.returncode!=0: raise SystemExit(proc.stderr[-4000:])
 silent.unlink(missing_ok=True)
 if not out.exists() or out.stat().st_size<10000: raise SystemExit("FAIL: canonical drummer MP4 missing/empty")
 print(f"PASS: canonical drummer V3 MP4 effects={len(effects)} duration_ms={duration_ms}"); return 0
if __name__=="__main__": raise SystemExit(main())
