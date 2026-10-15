"""Independently decode every completed review MP4 and check original audio."""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from scipy import signal

CATEGORIES=['01_Standalone_Bands','02_Bands_Inside_Layouts','03_Six_Layout_Comparisons','04_Lyric_Band_Videos']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audio(path):
    data=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(path),'-map','0:a:0','-vn','-ar','8000','-ac','2','-f','f32le','-'])
    return np.frombuffer(data,'<f4').reshape(-1,2)


def inspect(args):
    root,renderproof,row=args;root=Path(root);movie=root/renderproof['file'];eid=row['excerpt_id']
    folder=root/'06_Validation_Reports';folder.mkdir(exist_ok=True);name=movie.stem;dest=folder/(name+'.json')
    digest=sha(movie)
    if renderproof['sha256']!=digest:raise ValueError('Rendered movie hash changed: '+name)
    if dest.exists():
        old=json.loads(dest.read_text())
        if old.get('sha256')==digest and old.get('source_sha256')==row['sha256'] and old.get('source_start')==row['start_seconds']:return old
    metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    video=next(s for s in metadata['streams'] if s['codec_type']=='video');sound=next(s for s in metadata['streams'] if s['codec_type']=='audio')
    assert video['codec_name']=='h264' and video['pix_fmt']=='yuv420p'
    assert sound['codec_name']=='aac' and sound['channels']==2
    assert video['r_frame_rate']=='20/1' and int(video['nb_frames'])==720
    assert abs(float(video['duration'])-36)<.001 and abs(float(sound['duration'])-36)<.06
    assert abs(float(sound.get('start_time',0))-float(video.get('start_time',0)))<.002
    source=root/'07_Layouts_and_Sequences'/eid/'audio.wav'
    assert sha(Path(row['path']))==row['sha256']
    assert sha(source)==renderproof['excerpt_wav_sha256']
    reference=audio(Path(row['path']))[round(row['start_seconds']*8000):round(row['end_seconds']*8000)]
    excerpt=audio(source);actual=audio(movie);n=min(len(actual),len(reference),len(excerpt))
    assert abs(n-288000)<300 and np.sqrt(np.mean(actual**2))>.0001
    source_corr=[float(np.corrcoef(reference[:n,c],excerpt[:n,c])[0,1]) for c in range(2)]
    assert min(source_corr)>.995,('excerpt differs from original',name,source_corr)
    windows=[]
    for second in (0,9,18,27,33):
        lo=second*8000;hi=min(n,lo+24000)
        correlations=[float(np.corrcoef(reference[lo:hi,c],actual[lo:hi,c])[0,1]) for c in range(2)]
        # Search a bounded neighborhood independently; no soundtrack edits.
        x=reference[lo:hi].mean(axis=1);y=actual[lo:hi].mean(axis=1)
        cross=signal.correlate(y,x,mode='full',method='fft');center=len(x)-1
        lag=int(np.argmax(cross[center-160:center+161])-160)
        assert min(correlations)>.99 and abs(lag)<=1,(name,second,correlations,lag)
        windows.append(dict(source_relative_second=second,stereo_correlations=correlations,best_offset_ms=lag/8))
    # Decode every video frame into a bounded stream; inspect image content.
    proc=subprocess.Popen(['ffmpeg','-v','error','-xerror','-threads','1','-i',str(movie),'-map','0:v:0','-an',
        '-vf','scale=160:90','-pix_fmt','gray','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    count=0;black=0;run=0;longest=0;diffs=[];previous=None;means=[]
    while True:
        raw=proc.stdout.read(160*90)
        if not raw:break
        if len(raw)!=160*90:raise ValueError('Truncated decoded video frame')
        frame=np.frombuffer(raw,np.uint8).reshape(90,160);scene=frame[10:80]
        means.append(float(scene.mean()));black+=int(scene.max()<8 and scene.mean()<1.5)
        if previous is not None:
            diff=float(np.abs(frame.astype(float)-previous).mean());diffs.append(diff)
            run=run+1 if diff<.015 else 0;longest=max(longest,run)
        previous=frame.copy();count+=1
    errors=proc.stderr.read().decode();code=proc.wait()
    assert code==0 and count==720 and not black,(name,code,count,black,errors)
    assert max(diffs)>.1 and longest<100,(name,'complete scene frozen for too long',longest)
    # Actual decoded images at drum, mouth and mallet review times.
    screenshots=folder/'Diagnostic_Frames'/name;screenshots.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-v','error','-y','-threads','1','-i',str(movie),'-vf',
        "select='eq(n,40)+eq(n,240)+eq(n,400)+eq(n,520)+eq(n,700)',scale=640:360",'-vsync','0',str(screenshots/'frame_%02d.jpg')],check=True)
    proof=dict(file=renderproof['file'],excerpt_id=eid,sha256=digest,bytes=movie.stat().st_size,source_sha256=row['sha256'],
        source_start=row['start_seconds'],source_end=row['end_seconds'],source_filename=row['filename'],
        seconds=36,frames=count,fps=20,resolution=[video['width'],video['height']],video_codec='H.264',audio_codec='AAC stereo',
        complete_video_decode=True,complete_audio_decode=True,unexpected_black_frames=black,
        maximum_repeated_scene_frames=longest,mean_scene_brightness=float(np.mean(means)),minimum_frame_change=float(min(diffs)),
        av_stream_start_offset_ms=(float(sound.get('start_time',0))-float(video.get('start_time',0)))*1000,
        original_to_excerpt_correlations=source_corr,soundtrack_windows=windows,
        minimum_soundtrack_correlation=min(min(w['stereo_correlations']) for w in windows),
        diagnostic_frame_times=[2,12,20,26,35],musical_transcription_independently_verified=False,hardware_tested=False,
        mallet_contacts=renderproof.get('mallet_contacts'),maximum_mallet_contact_error=renderproof.get('max_mallet_contact_error'),
        unresolved_motion_events=len(renderproof.get('drummer_motion_rejections',[])),review_status='technical checks passed; artistic and listening review requested')
    dest.write_text(json.dumps(proof,indent=2)+'\n');print('VERIFIED',name,proof['minimum_soundtrack_correlation'],flush=True);return proof


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--minimum',type=int,default=0);p.add_argument('--workers',type=int,default=2);a=p.parse_args();root=a.root.resolve()
    rows={r['excerpt_id']:r for r in json.loads((root/'05_Source_Excerpt_Manifests/selected_excerpts.json').read_text())}
    tasks=[]
    for cat in CATEGORIES:
        for p in (root/cat).glob('*.render.json'):
            proof=json.loads(p.read_text());tasks.append((str(root),proof,rows[proof['excerpt_id']]))
    if len(tasks)<a.minimum:raise ValueError(f'Only {len(tasks)} completed movies; {a.minimum} required')
    reports=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for r in pool.map(inspect,tasks):reports.append(r)
    summary=dict(verified_videos=len(reports),categories={c:sum(r['file'].startswith(c+'/') for r in reports) for c in CATEGORIES},
        minimum_soundtrack_correlation=min((r['minimum_soundtrack_correlation'] for r in reports),default=None),
        total_seconds=len(reports)*36,reports=reports,release_approval_received=False,public_exe_apk_rebuilt=False)
    (root/'06_Validation_Reports/MASTER_VALIDATION.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__=='__main__':main()
