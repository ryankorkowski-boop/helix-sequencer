"""Decode and source-align recovery movies without implying artistic approval."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
from scipy.signal import correlate,correlation_lags
from tools.phoneme_source import digest
from tools.native_preview import probe_media


def pcm(path):
    return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),
        '-map','0:a:0','-ac','1','-ar','16000','-f','f32le','-']),dtype='<f4')


def verify(video,audio,expected_sha256):
    video,audio=Path(video),Path(audio)
    if digest(audio)!=expected_sha256:raise ValueError('Soundtrack substitution refused')
    probe=probe_media(video,'ffprobe')
    v=next(x for x in probe['streams'] if x['codec_type']=='video')
    a=next(x for x in probe['streams'] if x['codec_type']=='audio')
    if v['codec_name']!='h264' or a['codec_name']!='aac' or int(v['width'])<1280 or int(v['height'])<720:
        raise ValueError('Video codecs or minimum dimensions failed')
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True,capture_output=True)
    original,encoded=pcm(audio),pcm(video);n=min(len(original),len(encoded))
    correlation=float(np.corrcoef(original[:n],encoded[:n])[0,1])
    if not np.isfinite(correlation) or correlation<.97:raise ValueError('Soundtrack identity correlation failed')
    duration=len(original)/16000
    if abs(float(v['duration'])-duration)>.1 or abs(float(a['duration'])-duration)>.1:
        raise ValueError('Complete soundtrack duration failed')
    alignments=[]
    for fraction in (.1,.5,.85):
        start=int(duration*fraction*16000);window=min(32000,n-start)
        margin=2400;lo=max(0,start-margin);hi=min(n,start+window+margin)
        values=correlate(encoded[lo:hi],original[start:start+window],method='fft',mode='valid')
        lag=(int(values.argmax())+lo-start)/16000
        alignments.append(dict(source_start_seconds=start/16000,decoded_lag_seconds=lag))
    if max(abs(x['decoded_lag_seconds']) for x in alignments)>.05:raise ValueError('Soundtrack alignment exceeds one native50ms frame')
    return dict(file=video.name,sha256=digest(video),bytes=video.stat().st_size,
        source_audio=audio.name,source_audio_sha256=expected_sha256,source_duration_seconds=duration,
        codecs=[v['codec_name'],a['codec_name']],dimensions=[v['width'],v['height']],
        actual_frame_rate=v['avg_frame_rate'],actual_frame_count=v.get('nb_frames'),
        video_duration_seconds=float(v['duration']),audio_duration_seconds=float(a['duration']),
        stream_start_seconds=[float(v.get('start_time',0)),float(a.get('start_time',0))],
        full_decode=True,soundtrack_correlation=correlation,window_alignment=alignments,
        musical_or_visual_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);p.add_argument('audio',type=Path)
    p.add_argument('--expected-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=verify(a.video,a.audio,a.expected_sha256)
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
