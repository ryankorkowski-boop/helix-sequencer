"""Bounded actual-MP4 checks for the twelve-panel owner-review delivery."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

import numpy as np
from scipy.signal import correlate,correlation_lags

from tools.phoneme_source import digest
from tools.render_approval_collection import pcm


def verify(movie,audio,output):
    movie,audio,output=map(Path,(movie,audio,output))
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    sound=[s for s in probe['streams'] if s['codec_type']=='audio']
    assert (video['codec_name'],video['width'],video['height'],video['avg_frame_rate'])==('h264',1920,1080,'30/1')
    assert len(sound)==1 and sound[0]['codec_name']=='aac'
    assert 30<=float(video['duration'])<=45
    subprocess.run(['ffmpeg','-v','error','-xerror','-threads','2','-i',str(movie),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
    source,decoded=pcm(audio),pcm(movie);n=min(len(source),len(decoded))
    correlation=float(np.corrcoef(source[:n],decoded[:n])[0,1]);rms=float(np.sqrt(np.mean(decoded**2)))
    assert correlation>=.97 and rms>.0001
    assert abs(len(source)/16000-float(video['duration']))<.1
    windows=[]
    for start in (0.,len(source)/16000*.33,len(source)/16000*.66,len(source)/16000-2.05):
        i=round(start*16000);x=source[i:i+32000];y=decoded[i:i+len(x)]
        values=correlate(y,x,mode='full',method='fft');lags=correlation_lags(len(y),len(x))
        allowed=np.abs(lags)<=3200;lag=int(lags[allowed][np.argmax(values[allowed])])
        assert abs(lag)<=480
        windows.append(dict(source_start_seconds=start,lag_seconds=lag/16000))
    command=['ffmpeg','-v','error','-threads','2','-filter_threads','2','-i',str(movie),'-an',
             '-vf','fps=10,scale=960:540','-pix_fmt','rgb24','-f','rawvideo','-']
    child=subprocess.Popen(command,stdout=subprocess.PIPE)
    hashes=[hashlib.sha256() for _ in range(12)];last=[None]*12
    blank=[0]*12;frozen=[0]*12;max_blank=[0]*12;max_frozen=[0]*12;motions=[[] for _ in range(12)];count=0
    frame_size=960*540*3
    while True:
        block=child.stdout.read(frame_size)
        if not block:break
        if len(block)!=frame_size:raise ValueError('Truncated decoded video frame')
        frame=np.frombuffer(block,'u1').reshape(540,960,3)
        for k in range(12):
            # Exclude panel captions and letterbox: inspect actual display pixels.
            y=(k//4)*180;x=(k%4)*240;crop=frame[y+25:y+156,x:x+240]
            hashes[k].update(crop.tobytes())
            visible=float(np.mean(crop.max(axis=2)>24))
            blank[k]=blank[k]+1 if visible<.0005 else 0;max_blank[k]=max(max_blank[k],blank[k])
            luma=np.mean(crop.astype('f4'),axis=2)
            if last[k] is not None:
                motion=float(np.mean(np.abs(luma-last[k])));motions[k].append(motion)
                frozen[k]=frozen[k]+1 if motion<.04 else 0;max_frozen[k]=max(max_frozen[k],frozen[k])
            last[k]=luma
        count+=1
    child.stdout.close()
    if child.wait():raise ValueError('Frame decoding failed')
    fingerprints=[h.hexdigest() for h in hashes]
    assert len(set(fingerprints))==12,'Repeated comparison panels'
    panels=[dict(number=i+1,content_sha256=fingerprints[i],longest_blank_seconds=max_blank[i]/10,
                 longest_frozen_seconds=max_frozen[i]/10,median_motion=float(np.median(motions[i]))) for i in range(12)]
    assert all(p['longest_blank_seconds']<2 and p['longest_frozen_seconds']<2 for p in panels),panels
    report=dict(schema='helix.actual-twelve-comparison-playback.v1',movie=str(movie),sha256=digest(movie),bytes=movie.stat().st_size,
                video_codec=video['codec_name'],audio_codec=sound[0]['codec_name'],dimensions=[1920,1080],fps=30,
                seconds=float(video['duration']),video_frames=int(video['nb_frames']),full_decode=True,
                source_audio=str(audio),source_audio_sha256=digest(audio),audio_rms=rms,
                soundtrack_correlation=correlation,audio_window_alignment=windows,panels=panels,
                inspected_motion_frames=count,sample_fps=10,owner_approved=False,
                limitation='Playback/mux/panel evidence does not independently establish singer identity or lexical phonemes')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('movie','audio','output'):p.add_argument(name,type=Path)
    a=p.parse_args();verify(a.movie,a.audio,a.output)
