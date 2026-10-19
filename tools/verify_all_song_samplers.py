"""Independent full MP4 decode plus encoded image/audio comparison for new samplers."""
from pathlib import Path
import argparse
import json
import subprocess
import numpy as np
from PIL import Image
import soundfile as sf


def verify(root):
    manifest=json.loads((root/'manifest.json').read_text());reports=[]
    songs={s['sha256'] for s in manifest['inventory']['songs']}
    for row in manifest['samples']:
        folder=root/('sampler_'+row['sampler']);audio=folder/Path(row['audio']).name
        assert {c['source_sha256'] for c in row['clips']}==songs
        reference,rate=sf.read(audio);movies=[folder/Path(row['comparison']).name]+[folder/Path(p).name for p in row.get('individual_movies',[])]
        for movie in movies:
            subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
            video=next(s for s in probe['streams'] if s['codec_type']=='video');sound=next(s for s in probe['streams'] if s['codec_type']=='audio')
            assert video['codec_name']=='h264' and sound['codec_name']=='aac' and video['pix_fmt']=='yuv420p'
            assert int(video['nb_frames'])==1800 and abs(float(probe['format']['duration'])-90)<.025
            pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-map','0:a:0','-ar',str(rate),'-ac','2','-f','f32le','-'])
            actual=np.frombuffer(pcm,'<f4').reshape(-1,2);correlations=[]
            for clip in row['clips']:
                lo=round((clip['montage_start_seconds']+1)*rate);hi=lo+rate*3
                for channel in (0,1):
                    coefficient=float(np.corrcoef(reference[lo:hi,channel],actual[lo:hi,channel])[0,1]);assert coefficient>.99,(movie,clip['title'],coefficient);correlations.append(coefficient)
            errors=[]
            if movie.name.endswith('_Six_Layouts.mp4'):
                for image in sorted(folder.glob('decoded_source_*.png')):
                    frame=int(image.stem.rsplit('_',1)[1]);raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-vf',rf'select=eq(n\,{frame})','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
                    expected=np.asarray(Image.open(image).convert('RGB'));decoded=np.frombuffer(raw,np.uint8).reshape(expected.shape)
                    error=float(np.abs(expected.astype(float)-decoded).mean());assert error<8,(movie,frame,error);errors.append(error)
            reports.append({'movie':movie.name,'all_repo_songs':len(songs),'frames':1800,'duration_seconds':90,'full_decode':True,'minimum_source_audio_correlation':min(correlations),'maximum_sampled_frame_mean_error':max(errors) if errors else None})
            print(json.dumps(reports[-1]),flush=True)
    assert len(reports)==5
    (root/'verification.json').write_text(json.dumps(reports,indent=2)+'\n');return reports

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);args=parser.parse_args();verify(args.root)
