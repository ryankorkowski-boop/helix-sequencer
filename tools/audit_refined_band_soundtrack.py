"""Independent waveform alignment of every montage excerpt; no listening claim."""
from pathlib import Path
import json,subprocess
import numpy as np
from scipy.signal import correlate
from tools.render_refined_helix_band import OUT,ROOT


def wave(path,offset=0,seconds=None):
    command=['ffmpeg','-v','error','-ss',str(offset),'-i',str(path)]
    if seconds is not None:command+=['-t',str(seconds)]
    command+=['-vn','-ac','1','-ar','8000','-f','f32le','-']
    return np.frombuffer(subprocess.check_output(command),dtype='<f4')


def main():
    shows=ROOT/'outputs/Snowman_Ensemble/shows'
    paths={'dry':ROOT/'evidence/drummer/dry_drum_test.wav',**{id:shows/f'{id}_band/media/song.mp3' for id in ['00','01','02','03','05']}}
    cases={'Video_E_Full_Band_Showcase.mp4':[('dry',0,0,38.32),('00',38.35,164,18),('03',56.35,168,18),('05',74.35,26,18),('02',92.35,115,18),('01',110.35,101,18)],
           'Video_C_Bass_and_Guitar.mp4':[('02',0,115,18),('01',18,101,18)]}
    results=[]
    for movie,cues in cases.items():
        rendered=wave(OUT/movie)
        for id,offset,start,seconds in cues:
            reference=wave(paths[id],start,seconds);expected=round(offset*8000);lo=max(0,expected-640);hi=min(len(rendered),expected+len(reference)+640)
            signal=rendered[lo:hi];scores=correlate(signal,reference,mode='valid',method='fft');lag=int(scores.argmax());index=lo+lag
            value=float(np.corrcoef(reference,rendered[index:index+len(reference)])[0,1])
            result=dict(movie=movie,source_id=id,source_start=start,source_duration=seconds,expected_montage_offset=offset,
               measured_audio_offset=index/8000,offset_error_ms=1000*(index/8000-offset),waveform_correlation=value,independent_audio_waveform_check=True,listening_performed=False)
            print(result,flush=True)
            assert value>.995 and abs(index/8000-offset)<.002
            results.append(result)
    (OUT/'montage_audio_verification.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
