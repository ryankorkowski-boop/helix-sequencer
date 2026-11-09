"""Decode band movies and verify timing, source soundtrack and visible frames."""
from __future__ import annotations
import argparse,json,subprocess,hashlib
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw


def audit(movie):
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(movie)]))
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    sound=next(s for s in info['streams'] if s['codec_type']=='audio')
    proof=json.loads(movie.with_suffix('.verification.json').read_text())
    assert video['codec_name']=='h264' and sound['codec_name']=='aac'
    assert int(video['nb_read_frames'])==proof['frames']
    assert abs(float(video['duration'])-proof['seconds'])<.051
    subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True)
    original,rate=sf.read(movie.with_suffix('.wav'),dtype='float32')
    decoded=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-vn','-ac','2','-ar',str(rate),'-f','f32le','-']),dtype='<f4').reshape(-1,2)
    count=min(len(original),len(decoded));corr=float(np.corrcoef(original[:count].ravel(),decoded[:count].ravel())[0,1])
    assert corr>.99,('soundtrack correlation',corr)
    samples=[];tiles=[];duration=proof['seconds']
    for i,t in enumerate([duration*.06,duration*.22,duration*.43,duration*.63,duration*.85]):
        path=movie.with_name(movie.stem+f'_decoded_{i}.jpg')
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(movie),'-frames:v','1',str(path)],check=True)
        image=Image.open(path).convert('RGB');rgb=np.asarray(image)
        assert rgb.max()>200 and (rgb.max(axis=2)>35).mean()>.05
        samples.append(dict(time=t,path=path.name,lit_fraction=float((rgb.max(axis=2)>35).mean())))
        tile=image.resize((512,288));ImageDraw.Draw(tile).text((8,268),f'{t:.2f}s',fill='white');tiles.append(tile)
    sheet=Image.new('RGB',(512*3,288*2),'#080D17')
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%3)*512,(i//3)*288))
    sheet.save(movie.with_name(movie.stem+'_contact_sheet.jpg'),quality=92)
    result=dict(file=movie.name,bytes=movie.stat().st_size,sha256=hashlib.sha256(movie.read_bytes()).hexdigest(),
        seconds=proof['seconds'],frames=proof['frames'],full_decode_passed=True,codec='H264/AAC',
        waveform_correlation=corr,decoded_samples=samples,max_contact_error=max((s.get('max_mallet_contact_error',0) for s in proof['segments']),default=0))
    print(json.dumps(result),flush=True);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('movies',nargs='+',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=[audit(m) for m in a.movies];a.output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
