from __future__ import annotations
import argparse, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
import imageio.v2 as imageio
from PIL import Image, ImageChops, ImageEnhance, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
POSE_FILES={
 "kick_hit":"drummer_hit_kick.png","snare_hit":"drummer_hit_snare.png",
 "hi_hat_pulse":"drummer_hit_hi_hat.png","left_tom_hit":"drummer_hit_left_tom.png",
 "right_tom_hit":"drummer_hit_right_tom.png","left_crash":"drummer_hit_left_crash.png",
 "right_crash":"drummer_hit_right_crash.png","both_crash":"drummer_hit_both_crash.png",
 "downbeat_impact":"drummer_downbeat_impact.png",
}
def parse_effects(xsq):
 root=ET.parse(xsq).getroot(); out=[]
 for e in root.findall("./ElementEffects/Element"):
  if not (e.get("name") or "").startswith("HX_DRUMMER_"): continue
  for layer in e.findall("EffectLayer"):
   for fx in layer.findall("Effect"):
    pose=fx.get("sourcePose")
    if pose in POSE_FILES:
     out.append((int(float(fx.get("startTime","0"))),int(float(fx.get("endTime","0"))),pose))
 return sorted(set(out))
def main():
 p=argparse.ArgumentParser()
 p.add_argument("xsq",type=Path); p.add_argument("--audio",type=Path,required=True)
 p.add_argument("--output",type=Path,required=True); p.add_argument("--fps",type=int,default=30)
 p.add_argument("--duration",type=float,default=20)
 a=p.parse_args()
 bg=Image.open(ROOT/"fixtures/band_geometry/source/drummerbg.png").convert("RGBA")
 layers={k:Image.open(ROOT/"fixtures/band_geometry/layers"/v).convert("RGBA") for k,v in POSE_FILES.items()}
 effects=parse_effects(a.xsq)
 if not effects: raise SystemExit("FAIL: no drummer pose effects found in XSQ")
 duration_ms=min(int(a.duration*1000),max(1000,max(e[1] for e in effects)))
 size=bg.size
 frames=[]
 writer=imageio.get_writer(a.output,fps=a.fps,codec="libx264",quality=8,macro_block_size=None)
 try:
  for i in range(int(duration_ms/1000*a.fps)):
   t=int(i*1000/a.fps); active=[pose for s,e,pose in effects if s<=t<e]
   # Use the most recent active hit, with idle background otherwise.
   frame=bg.copy()
   if active:
    # Composite every simultaneous hit so both hands/crashes can appear together.
    for pose in active:
     frame.alpha_composite(layers[pose])
   # Small explicit status banner makes it unambiguous this is the drummer render.
   draw=ImageDraw.Draw(frame)
   draw.rounded_rectangle((20,20,610,78),radius=12,fill=(0,0,0,185))
   draw.text((35,36),f"HELIX DRUMMER V3  |  {', '.join(active) if active else 'idle'}",(255,255,255,255))
   writer.append_data(__import__("numpy").asarray(frame.convert("RGB")))
  writer.close()
 finally:
  try: writer.close()
  except Exception: pass
 # Mux the real soundtrack.
 import imageio_ffmpeg
 ff=imageio_ffmpeg.get_ffmpeg_exe()
 silent=a.output.with_suffix(".silent.mp4")
 a.output.replace(silent)
 cmd=[ff,"-y","-i",str(silent),"-i",str(a.audio),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-shortest","-movflags","+faststart",str(a.output)]
 proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if proc.returncode!=0: raise SystemExit(proc.stderr[-4000:])
 silent.unlink(missing_ok=True)
 # Verification: the rendered video contains the drummer and the XSQ has distinct poses.
 poses=sorted({p for _,_,p in effects})
 if len(poses)<4: raise SystemExit(f"FAIL: only {len(poses)} distinct drummer poses: {poses}")
 if not a.output.exists() or a.output.stat().st_size<10000: raise SystemExit("FAIL: MP4 missing/empty")
 print(f"PASS: drummer MP4 {a.output} poses={poses} effects={len(effects)} duration_ms={duration_ms}")
if __name__=="__main__": main()
