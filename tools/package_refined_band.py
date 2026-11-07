"""Build review montages and portable XSQ/matrix show packages."""
from pathlib import Path
import argparse,json,subprocess,zipfile
from tools.render_refined_helix_band import OUT
from tools.export_refined_band_matrix import export


def concat(files,name):
    manifest=OUT/(name+'.concat.txt');manifest.write_text(''.join("file '"+str(p)+"'\n" for p in files))
    movie=OUT/(name+'.mp4')
    command=['ffmpeg','-v','error','-y']
    for path in files:command+=['-threads','1','-i',str(path)]
    filters=[]
    for i in range(len(files)):
        duration=float(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=duration','-of','csv=p=0',str(files[i])]))
        duration=round(duration*20)/20
        filters+=[f'[{i}:v]fps=20,setpts=PTS-STARTPTS[v{i}]',
                  f'[{i}:a]aresample=48000,atrim=duration={duration},apad=pad_dur=0.05,atrim=duration={duration},asetpts=PTS-STARTPTS[a{i}]']
    inputs=''.join(f'[v{i}][a{i}]' for i in range(len(files)))
    filters.append(inputs+f'concat=n={len(files)}:v=1:a=1[v][a]')
    command+=['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]',
              '-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p',
              '-c:a','aac','-b:a','192k','-movflags','+faststart',str(movie)]
    subprocess.run(command,check=True)
    return movie


def montages():
    c=concat([OUT/'C_Bass_49.mp4',OUT/'C_Guitar_Who_Knew.mp4'],'Video_C_Bass_and_Guitar')
    e=concat([OUT/'Video_B_Original_Dry_Drum_Test.mp4',OUT/'E_Band_Wire_Tree.mp4',OUT/'E_Band_Candy_Cane_Chaos.mp4',
              OUT/'E_Band_Festivus.mp4',OUT/'C_Bass_49.mp4',OUT/'C_Guitar_Who_Knew.mp4'],'Video_E_Full_Band_Showcase')
    return c,e


def main():
    p=argparse.ArgumentParser();p.add_argument('--montages',action='store_true');p.add_argument('--exports',action='store_true');a=p.parse_args()
    if a.montages:montages()
    if a.exports:
        for movie in sorted(OUT.glob('*.mp4')):
            if '_pilot' not in movie.name:print(export(movie),flush=True)

if __name__=='__main__':main()
