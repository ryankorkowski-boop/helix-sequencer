"""Render actual native xLights shows and compare their pixels with source movies."""
from __future__ import annotations
import argparse,json,os,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image
from tools.render_refined_helix_band import OUT
from tools.build_helpers.ultimate_showcase_preview import read_fseq


def native_render(binary,display=109):
    log=open(OUT/'native_xvfb.log','w')
    xserver=subprocess.Popen(['Xvfb',':'+str(display),'-screen','0','1280x720x24','-listen','tcp','-nolisten','unix','-ac'],stdout=log,stderr=log)
    env=dict(os.environ,DISPLAY=f'127.0.0.1:{display}')
    try:
        for folder in sorted((OUT/'xlights').iterdir()):
            xsq=next(folder.glob('*.xsq'))
            with (folder/'native_render.log').open('w') as stream:
                subprocess.run([str(binary),'--headless','-q','-s',str(folder),'-od',str(folder),str(xsq)],env=env,stdout=stream,stderr=stream,check=True)
            print('native render',folder.name,flush=True)
    finally:xserver.terminate();xserver.wait();log.close()


def audit():
    reports=[];screens=OUT/'native_frames';screens.mkdir(exist_ok=True)
    for folder in sorted((OUT/'xlights').iterdir()):
        xsq=next(folder.glob('*.xsq'));root=ET.parse(xsq).getroot();layout=ET.parse(folder/'xlights_rgbeffects.xml').getroot()
        models=layout.findall('./models/model');assert len(models)==1
        model=models[0];width,height=int(model.get('parm2')),int(model.get('parm1'))
        names={m.get('name') for m in models};assert {e.get('name') for e in root.findall('./ElementEffects/Element')}<=names
        for relative in ('media/soundtrack.wav','media/performance.mp4'):assert (folder/relative).is_file()
        frames,step=read_fseq(xsq.with_suffix('.fseq'));assert step==50
        duration=float(root.findtext('./head/sequenceDuration'));assert abs(len(frames)*step/1000-duration)<.001
        assert frames.shape[1]==width*height*3
        errors=[];energies=[]
        process=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-i',str(folder/'media/performance.mp4'),'-vf',f'fps=20,scale={width}:{height}:flags=bilinear','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
        size=width*height*3;index=0
        while True:
            data=process.stdout.read(size)
            if not data:break
            assert len(data)==size
            assert index<len(frames)
            expected=np.frombuffer(data,np.uint8).reshape(height,width,3)
            # Native model channel order starts at the bottom-left; xLights's
            # displayed matrix is upright. This is topology, not a video flip fix.
            actual=frames[index].reshape(height,width,3)[::-1]
            error=float(np.abs(actual.astype(float)-expected).mean());errors.append(error)
            energies.append(float(actual.mean()))
            if index in (0,len(frames)//3,2*len(frames)//3,len(frames)-2):Image.fromarray(actual).resize((1280,720)).save(screens/(folder.name+f'_{index:04}.png'))
            index+=1
        process.stdout.close();assert process.wait()==0
        # End rounding may add one native50ms frame beyond movie duration.
        assert abs(index-len(frames))<=1
        assert min(energies)>0 and np.mean(errors)<8
        report=dict(movie=folder.name,native_frames=len(frames),compared_frames=index,step_ms=step,channels=frames.shape[1],
            mean_pixel_error=float(np.mean(errors)),p95_frame_pixel_error=float(np.quantile(errors,.95)),max_frame_pixel_error=max(errors),
            minimum_frame_mean_light=min(energies),model_bindings_valid=True,all_media_paths_resolve=True,
            native_xlights_version='2026.18',virtual_matrix_export=True,individual_physical_prop_articulation=False)
        reports.append(report);print(report,flush=True)
    (OUT/'native_verification.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--binary',type=Path);p.add_argument('--display',type=int,default=109);args=p.parse_args()
    if args.binary:native_render(args.binary,args.display)
    audit()
