"""Independently decode real Android-produced MP4s and compare their source."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import subprocess
import zipfile
import numpy as np
import soundfile as sf
from scipy.signal import correlate, correlation_lags
from tools import preview_renderer as p
from tools.lor_lms_import import prepare_lms_workspace


def decode_video_samples(movie, indices, *, width=640, height=360):
    """Decode every frame, retaining only requested samples in bounded memory."""
    frame_bytes = width * height * 3
    process = subprocess.Popen(['ffmpeg','-v','error','-i',str(movie),'-map','0:v:0',
        '-f','rawvideo','-pix_fmt','rgb24','pipe:1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    selected, count, wanted = {}, 0, set(indices)
    try:
        while True:
            raw = process.stdout.read(frame_bytes)
            if not raw:
                break
            if len(raw) != frame_bytes:
                raise ValueError('Truncated decoded video frame')
            if count in wanted:
                selected[count] = np.frombuffer(raw,np.uint8).reshape(height,width,3).copy()
            count += 1
        if process.wait() != 0:
            raise RuntimeError(process.stderr.read().decode(errors='replace'))
    finally:
        process.stdout.close()
        process.stderr.close()
        if process.poll() is None:
            process.kill()
            process.wait()
    return selected, count

def verify(artifact: Path, output: Path):
    output.mkdir(parents=True,exist_ok=True);reports=[]
    for mode in ('xlights','lor','real-rgb','full-song','band-off'):
        bundle=next(artifact.rglob(mode+'-show.zip'));folder=output/mode;folder.mkdir(exist_ok=True)
        with zipfile.ZipFile(bundle) as z:
            assert z.testzip() is None
            z.extractall(folder)
        movie=next(folder.rglob('*.mp4'));xsq=movie.with_suffix('.xsq');wav=movie.parent/'audio.wav'
        if mode=='lor':
            imported=prepare_lms_workspace(movie.parent/'helix_lor_source_layout.lms',output/'lor-layout')
            layout=p.parse_models(Path(imported['layout']))
        else:layout=p.parse_models(movie.parent/'xlights_rgbeffects.xml')
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
        video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
        assert video['codec_name']=='h264' and audio['codec_name']=='aac'
        assert (video['width'],video['height'])==(640,360)
        seq=p.parse_sequence(xsq)
        seconds=min(seq.duration_ms/1000,600 if mode=='full-song' else 8 if mode=='real-rgb' else 3)
        expected_frames=math.ceil(seconds*15)
        samples=(0,7,15,29,expected_frames//2,expected_frames-1)
        frames,frame_count=decode_video_samples(movie,samples)
        assert frame_count==expected_frames,(mode,frame_count,expected_frames)
        if mode=='full-song':
            assert seconds>120 and abs(sf.info(wav).duration-seconds)<1/15
        leaves,intensity=p.build_leaf_intensity_matrix(layout,seq,15)
        colors=p.build_leaf_color_matrix(layout,seq,15,leaves,intensity.shape[1]);renderer=p.HouseRenderer(layout,640,360)
        errors=[];lit=[]
        for i in samples:
            expected=np.asarray(renderer.render_frame(leaf_names=leaves,frame_values=intensity[:,i],title=xsq.name,
                t_ms=round(i*1000/15),duration_ms=seconds*1000,overlays={},frame_colors=colors[:,i,:] if colors is not None else None).convert('RGB'))
            errors.append(float(np.abs(frames[i].astype(float)-expected).mean()))
            bright=expected.max(axis=2)>150
            lit.append(float(np.mean(frames[i].max(axis=2)[bright]>100)))
        assert max(errors)<12 and min(lit)>.8, (mode,errors,lit)
        source,sr=sf.read(wav);source=np.asarray(source);source=source.mean(axis=1) if source.ndim==2 else source
        pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-map','0:a:0','-ac','1','-ar',str(sr),'-f','f32le','pipe:1'])
        decoded=np.frombuffer(pcm,'<f4');n=min(len(decoded),len(source),round(sr*seconds));a=decoded[:n];b=source[:n]
        correlations=correlate(a,b,method='fft');lags=correlation_lags(len(a),len(b));ok=np.abs(lags)<sr*.067
        lag=int(lags[ok][np.argmax(correlations[ok])]);start=max(0,lag);offset=max(0,-lag);n=min(len(a)-start,len(b)-offset)
        coefficient=float(np.corrcoef(a[start:start+n],b[offset:offset+n])[0,1]);assert coefficient>.97 and abs(lag)<sr*.005 and len(decoded)>=sr*(seconds-.01)
        reports.append({'mode':mode,'frames':frame_count,'video_codec':'h264','audio_codec':'aac','duration':probe['format']['duration'],
            'source_duration_seconds':len(source)/sr,'full_song_preview_verified':mode=='full-song',
            'max_mean_pixel_error':max(errors),'minimum_expected_lit_pixels_visible':min(lit),'audio_correlation':coefficient,'audio_offset_ms':lag*1000/sr})
    with zipfile.ZipFile(next(artifact.rglob('failed-preview-show.zip'))) as archive:
        assert archive.testzip() is None
        run=json.loads(archive.read('android-run.json'))
        assert run['stages']['sequencing']['status']=='success'
        assert run['stages']['preview']['status']=='failed'
        assert any(name.endswith('.xsq') for name in archive.namelist())
        assert not any(name.endswith('.mp4') for name in archive.namelist())
    (output/'decoded-verification.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2));return reports

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('artifact',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();verify(args.artifact,args.output)

