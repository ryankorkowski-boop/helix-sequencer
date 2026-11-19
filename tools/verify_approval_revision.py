"""Fully decode the four approval movies and check original excerpt timing."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import numpy as np
from scipy.signal import correlate


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def audio(p):
    b=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(p),'-map','0:a:0','-vn','-ar','8000','-ac','2','-f','f32le','-'])
    return np.frombuffer(b,'<f4').reshape(-1,2)


def verify(root,*,expected_videos=4):
    reports=[];folder=root/'validation';folder.mkdir(exist_ok=True)
    receipts=sorted((root/'videos').glob('*.render.json'))
    if len(receipts)!=expected_videos:raise ValueError('Completed review movie count mismatch')
    for receipt in receipts:
        r=json.loads(receipt.read_text());movie=root/r['file'];source=root/'sources'/r['excerpt_id']/'audio.wav'
        assert r['frames']==720 and r['seconds']==36 and r['sha256']==sha(movie)
        assert sha(source)==r['excerpt_sha256']
        bound=json.loads((source.parent/'source.json').read_text())
        assert bound['excerpt_wav_sha256']==sha(source) and bound['sha256']==r['original_audio_sha256']
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
        v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
        assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p' and v['r_frame_rate']=='20/1' and int(v['nb_frames'])==720
        assert a['codec_name']=='aac' and a['channels']==2
        assert abs(float(v['duration'])-36)<.001 and abs(float(a['duration'])-36)<.06
        assert abs(float(a.get('start_time',0))-float(v.get('start_time',0)))<.002
        expected=audio(source);actual=audio(movie);n=min(len(expected),len(actual));assert abs(n-288000)<300
        windows=[]
        for sec in [0,9,18,27,33]:
            lo=sec*8000;hi=min(n,lo+24000);x=expected[lo:hi];y=actual[lo:hi]
            coefficients=[float(np.corrcoef(x[:,c],y[:,c])[0,1]) for c in [0,1]]
            c=correlate(y.mean(1),x.mean(1),method='fft');center=len(x)-1;lag=int(np.argmax(c[center-160:center+161])-160)
            assert min(coefficients)>.99 and abs(lag)<=1
            windows.append(dict(second=sec,correlations=coefficients,lag_ms=lag/8))
        proc=subprocess.Popen(['ffmpeg','-v','error','-xerror','-threads','1','-i',str(movie),'-an','-vf','scale=160:90','-pix_fmt','gray','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        count=0;black=0;repeated=0;maxrepeat=0;previous=None
        while True:
            b=proc.stdout.read(160*90)
            if not b:break
            assert len(b)==160*90
            frame=np.frombuffer(b,'u1');black+=int(frame.max()<8)
            if previous is not None:
                change=np.abs(frame.astype(float)-previous).mean();repeated=repeated+1 if change<.015 else 0;maxrepeat=max(maxrepeat,repeated)
            previous=frame.copy();count+=1
        error=proc.stderr.read().decode();assert proc.wait()==0 and not error and count==720 and black==0 and maxrepeat<100
        contact={}
        if 'mallet_contacts' in r:
            maxmallet=max((e['error'] for e in r['mallet_contacts']),default=0)
            maxkey=max((e['error'] for e in r['keyboard_contacts'] if e['source_contact_change']),default=0)
            assert maxmallet<1e-5 and maxkey<1e-5,(maxmallet,maxkey)
            routed=root/'analysis'/r['excerpt_id']/'voice_roles.npz'
            with np.load(routed if routed.exists() else root/'analysis'/r['excerpt_id']/'vocal_clock.npz') as z:
                for m in r['mouth_frames']:
                    j=m['frame'] if routed.exists() else m['source_clock_index']
                    energy=z['energy'][j,0] if routed.exists() else z['energy'][j]
                    shape=z['shapes'][j,0] if routed.exists() else z['shapes'][j]
                    assert abs(m['energy']-energy)<1e-7 and m['shape']==shape
                    if energy==0:assert m['shape']==0 and m['aperture']<=.00701
                    assert m['aperture']<=.07101
            if r.get('volumetric_drummer'):
                assert r['drummer_contacts'] and max(c['error'] for c in r['drummer_contacts'])<1e-5
                assert max(abs(c['time']-c['source_time']) for c in r['drummer_contacts'])<=.02501
            contact=dict(mallet_contacts=len(r['mallet_contacts']),max_mallet_contact_error=maxmallet,
                         keyboard_contact_changes=sum(e['source_contact_change'] for e in r['keyboard_contacts']),
                         maximum_key_contact_error_on_change=maxkey,mouth_clock_matches_source_analysis=True,
                         phone_identity_independently_verified=False)
        else:
            assert r['panels'] in (2,6) and r['all_panels_same_source_clock']
        screenshots=folder/movie.stem;screenshots.mkdir(exist_ok=True)
        subprocess.run(['ffmpeg','-v','error','-y','-threads','1','-i',str(movie),'-vf',"select='eq(n,40)+eq(n,240)+eq(n,380)+eq(n,520)+eq(n,700)',scale=640:360",'-vsync','0',str(screenshots/'frame_%02d.jpg')],check=True)
        report=dict(file=r['file'],sha256=sha(movie),source_sha256=sha(source),source_start=r['source_start'],source_end=r['source_end'],
            frames=count,seconds=36,fps=20,resolution=[v['width'],v['height']],complete_video_decode=True,complete_audio_decode=True,
            unexpected_black_frames=black,maximum_repeated_scene_frames=maxrepeat,soundtrack_windows=windows,contacts=contact)
        reports.append(report);(folder/(movie.stem+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('VERIFIED',movie.name,flush=True)
    summary=dict(videos=expected_videos,reports=reports,minimum_soundtrack_correlation=min(min(w['correlations']) for r in reports for w in r['soundtrack_windows']),
        artistic_approval_received=False,physical_hardware_tested=False,release_integration_performed=False)
    (folder/'MASTER_VALIDATION.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();verify(a.root.resolve())
