"""Decode exact preview frames and verify that its soundtrack matches the song."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import imageio_ffmpeg
import librosa
import numpy as np
from PIL import Image,ImageDraw
import soundfile as sf
from tools.render_drummer_v3_preview import parse_effects,_active_targets_for_frame

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('video',type=Path);p.add_argument('--xsq',type=Path,required=True);p.add_argument('--audio',type=Path,default=Path('Helix Audiolights.mp3'));p.add_argument('--start',type=float,default=9.5);p.add_argument('--duration',type=float,default=25);p.add_argument('--fps',type=int,default=60);p.add_argument('--output',type=Path,required=True)
    p.add_argument("--times",help="Comma-separated absolute song times for eight decoded review frames")
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();effects=parse_effects(a.xsq)
    times=[float(t) for t in a.times.split(",")] if a.times else [10.5,11.0,11.9833,13.6167,14.5833,19.15,23.3833,24.7]
    if len(times)!=8 or any(not a.start<=t<a.start+a.duration for t in times):
        raise ValueError("Choose eight review times within the rendered source interval")
    sheet=Image.new('RGB',(960,1160),'#111111');draw=ImageDraw.Draw(sheet);rows=[]
    for i,time in enumerate(times):
        frame=round((time-a.start)*a.fps);actual=a.start+frame/a.fps;path=a.output/f'decoded_{actual:.4f}.png'
        subprocess.run([ffmpeg,'-v','error','-y','-i',str(a.video),'-vf',f'select=eq(n\\,{frame})','-frames:v','1',str(path)],check=True)
        im=Image.open(path).convert('RGB');x=(i%2)*480;y=(i//2)*290;sheet.paste(im.resize((480,270)),(x,y));draw.text((x+10,y+273),f'Actual source time {actual:.4f}s, frame {frame}',fill='white')
        rows.append(dict(frame=frame,source_time=actual,targets=sorted(_active_targets_for_frame(effects,actual*1000,a.fps)),file=str(path)))
    sheet.save(a.output/'decoded_hit_contact_sheet.png')
    wav=a.output/'encoded_audio.wav'
    subprocess.run([ffmpeg,'-v','error','-y','-i',str(a.video),'-vn','-ac','1','-ar','48000',str(wav)],check=True)
    encoded,sr=sf.read(wav);source,_=librosa.load(a.audio,sr=sr,mono=True,offset=a.start,duration=a.duration)
    n=min(len(encoded),len(source));correlation=float(np.corrcoef(encoded[:n],source[:n])[0,1]);assert correlation>.98,correlation
    evidence=dict(video_sha256=hashlib.sha256(a.video.read_bytes()).hexdigest(),frames=rows,
                  audio_source_offset=a.start,audio_zero_lag_correlation=correlation,
                  note='Decoded frame and soundtrack identity evidence, not auditory approval.')
    (a.output/'preview_frame_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');print('Decoded frames and verified soundtrack',correlation)
