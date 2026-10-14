"""Render the retained articulated band and singers on the exact earlier sampler."""
from __future__ import annotations
import argparse,json,math,shutil
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import ImageDraw
from models.snowman_ensemble import build_ensemble
from models.refined_band_scene import RefinedBandScene
from tools.build_snowman_ensemble import NativeSequence,import_drummer
from tools.build_helpers.ultimate_showcase import write_layout
from tools.render_refined_helix_band import encoder,physical_hits,DynamicDry,REFINED_FRAGMENT,FONT,SMALL
from tools.render_intricate_band_samplers import SamplerView,SAMPLER_VERTEX,sha
from tools.refined_band_performance import RefinedPerformance
from animation.articulated_source_drummer import ArticulatedDrummer
from tools.build_prior_sampler_layouts import SAMPLER_SHA


TITLES=('Wire Tree','Tinsel Sawtooth','Frostbitten Fingerboard','Holly Steel Run','Bell Circuit Carol','Helix Audiolights')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audio',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--pilot',action='store_true')
    a=p.parse_args();assert sha(a.audio)==SAMPLER_SHA
    root=a.output.resolve();duration=sf.info(a.audio).duration;analysis=root/'analysis';folder=root/'drummer_source';folder.mkdir(parents=True,exist_ok=True)
    g=build_ensemble('band');write_layout(g,folder)
    seq=NativeSequence(g,duration,a.audio.name,'Recovered six-song sampler');seed=folder/'seed.xsq';seq.write(seed)
    report=import_drummer(seq,seed,a.audio,analysis/'sampler/drums.json',folder/'drummer_injected.xsq')
    source=folder/'Snowman_Band.xsq';seq.write(source)
    (folder/'drummer_report.json').write_text(json.dumps(report,indent=2)+'\n')
    row=dict(id='sampler',title='Original six-song sampler',path=str(a.audio),sha256=SAMPLER_SHA,duration=duration,drummer_xsq=str(source))
    scene=RefinedBandScene('prismatic_orrery');perf=RefinedPerformance(row,scene,analysis)
    view=SamplerView(scene,1280,720,SAMPLER_VERTEX.replace('activity[128]','activity[192]'),REFINED_FRAGMENT)
    player=ArticulatedDrummer(physical_hits(source));view.dry=DynamicDry(player)
    movie=root/('Helix_Band_With_Singers_Pilot.mp4' if a.pilot else 'Helix_Band_With_Singers_Same_Sampler.mp4')
    temp=movie.with_name(movie.stem+'.rendering.mp4');seconds=5 if a.pilot else duration
    writer=encoder(temp,1280,720,20,a.audio,0,seconds);contact=[];joints=[]
    try:
        for i in range(math.ceil(seconds*20)):
            levels=perf.pose(i);view.dry.time=i/20
            frame=view.frame(levels,perf.drums[i],perf.strikes[i],perf.hands[i],i/20,(i/20)%30)
            d=ImageDraw.Draw(frame);d.rectangle((0,0,1280,52),fill='#07101C')
            track=min(5,int(i/600));d.text((20,16),f'HELIX BAND + SINGERS  |  {TITLES[track]}  |  {i/20:06.2f}s',font=FONT,fill='#DDF5FF')
            d.rectangle((0,684,1280,720),fill='#07101C')
            d.text((18,695),'Same recovered sampler | stem-timed performance | authored duet | mallet candidates unverified',font=SMALL,fill='#ABC8D5')
            writer.stdin.write(frame.tobytes())
            assert all(np.isfinite(o['matrix']).all() for o in scene.instances)
            for role,points in perf.joint_targets.items():
                s,e,h=points;joints.append([float(np.linalg.norm(e-s)),float(np.linalg.norm(h-e))])
            if i in (0,350,1100,1810,2400,3150,3450):frame.save(root/f'Band_Frame_{i:04}.png')
            if i%200==0:print('band',i,math.ceil(seconds*20),flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();temp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
        view.close()
    if writer.wait():raise RuntimeError('Band encoder failed')
    temp.replace(movie)
    proof=dict(audio_sha256=SAMPLER_SHA,seconds=seconds,frames=math.ceil(seconds*20),fps=20,
        source_drums=perf.drum_proof,mallet_proof=perf.mallet_proof,mallet_schedule=perf.mallet_schedule,
        source_vocal_words=len(perf.vocals['words']),source_vocal_lines=perf.vocals['lines'],
        singers='authored exchange/shared phrases; no voice or gender separation claim',
        rendered_drums=len(player.hits),drum_motion_rejections=player.motion_rejections,
        limb_length_min=np.min(joints,axis=0).tolist(),limb_length_max=np.max(joints,axis=0).tolist(),
        sha256=sha(movie),bytes=movie.stat().st_size,independent_score_accuracy_verified=False)
    movie.with_suffix('.verification.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
