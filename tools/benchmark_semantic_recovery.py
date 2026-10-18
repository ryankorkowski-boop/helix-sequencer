"""Source-bound full-song native comparison against an immutable production tree.

The rhythm pass runs in a separate process importing the supplied baseline repo.
The semantic pass copies its native XSQ and appends scenic layers only. Movies
play actual xLights FSEQ samples at native model coordinates; they are not an
independent reconstruction of effects and are not labelled House Preview.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def garden():
    from models.ultimate_showcase import Garden
    g=Garden(title='Helix semantic recovery review',slug='Semantic_Review',
        description='Native scenic RGB layout used identically in both comparison panels.',
        palette=('#39c6ed','#d84d90','#ffd166'))
    for index,x in enumerate((-100,-50,0,50,100)):
        g.poly(f'SCENE_OUTLINE_{index}',[(x-18,0,0),(x-18,26,0),(x,43,0),(x+18,26,0),(x+18,0,0)],
               80,'OUTLINES','scenic outline',g.palette[index%3])
        g.poly(f'SCENE_PATH_{index}',[(x-18,0,-20),(x+18,0,-20)],40,'PATHS','foreground pixel line',g.palette[(index+1)%3])
    g.tree('SCENE_TREE',0,35,70,15,0,12,20,'TREES',color=g.palette[0])
    g.star('SCENE_STAR',0,81,35,16,'STARS',color=g.palette[2])
    start=1
    for model in g.models:
        model.start=start;start+=model.channels
    return g


def rhythm(args):
    from core import effect_engine as engine
    from tools.showcase_audio_native import prepare_template,native_music_xsq
    from tools.run_showcase_audio_batch import model_routes
    from core.audio_run_cache import AudioRunCache
    import soundfile as sf
    folder=args.output/'baseline';folder.mkdir(parents=True,exist_ok=True)
    g=garden();template=prepare_template(g,folder)
    media=folder/'source.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(args.audio),'-map','0:a:0','-vn',
                    '-ac','2','-ar','44100','-c:a','pcm_s16le',str(media)],check=True)
    duration=sf.info(media).duration
    raw=folder/'engine_raw.xsq'
    tuning=engine.RuntimeTuning(layout_file=folder/'xlights_rgbeffects.xml',template_guidance=False,
        workspace_history_enabled=False,learning_memory_enabled=False,matrix_intelligence=False,
        polish_enabled=False,variant_count=1,birdsong_enabled=False,birdsong_auto=False,
        audio_reactive_profile='showcase',audio_reactive_intensity=1.4,spatial_awareness=.85,
        chase_style='radial_out',model_overrides=model_routes(g),max_layers_per_prop=3)
    with (folder/'engine.log').open('w') as log,redirect_stdout(log):
        engine.run_variant(engine.VARIANTS['v27.3'],template,media,raw,engine.base.UserProfile(),
                           tuning=tuning,analysis_cache=AudioRunCache(digest(media)))
    export=native_music_xsq(raw,folder/'performance.xsq',g,media,duration)
    (args.output/'rhythm.json').write_text(json.dumps(dict(duration=duration,export=export,
        original_sha256=digest(args.audio),decoded_sha256=digest(media),
        baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.baseline,text=True).strip()),indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--audio',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--xlights',type=Path);p.add_argument('--instrumental',action='store_true')
    p.add_argument('--reuse-analysis',type=Path,help='Reuse source-bound native baseline and analysis from a verified prior artifact')
    p.add_argument('--song-key',default='')
    p.add_argument('--stage',choices=['all','rhythm'],default='all');args=p.parse_args()
    args.audio=args.audio.resolve();args.output=args.output.resolve();args.baseline=args.baseline.resolve()
    args.output.mkdir(parents=True,exist_ok=True)
    if args.stage=='rhythm':
        sys.path.insert(0,str(args.baseline));rhythm(args);return
    repo=Path(__file__).resolve().parents[1];sys.path.insert(0,str(repo))
    command=[sys.executable,str(Path(__file__).resolve()),'--audio',str(args.audio),
             '--output',str(args.output),'--baseline',str(args.baseline),'--stage','rhythm']
    if args.reuse_analysis:
        from types import SimpleNamespace
        from core.semantic_nli import maybe_enrich
        from core.semantic_story import direct
        reuse=args.reuse_analysis.resolve()
        meta=json.loads((reuse/'rhythm.json').read_text())
        media=reuse/'baseline'/'source.wav'
        if digest(media)!=meta['decoded_sha256']:
            raise ValueError('Reused analysis audio digest mismatch')
        args.audio=media
        shutil.copytree(reuse/'baseline',args.output/'baseline',dirs_exist_ok=True)
        shutil.copyfile(reuse/'rhythm.json',args.output/'rhythm.json')
        payload=json.loads((reuse/'analysis.json').read_text())
        if int(payload['metadata']['duration_ms'])!=round(meta['duration']*1000):
            raise ValueError('Reused transcript duration mismatch')
        original_direction=direct(payload['semantic_story'])
        payload['semantic_story']=maybe_enrich(payload['semantic_story'])
        if payload['semantic_story'].get('semantic_backend',{}).get('status')!='review_only':
            raise ValueError('Contextual model review was unavailable: '+str(payload['semantic_story'].get('semantic_backend')))
        payload['semantic_direction']=direct(payload['semantic_story'])
        if payload['semantic_direction']!=original_direction:
            raise ValueError('Unreviewed model changed production semantic direction')
        analysis=SimpleNamespace(semantic_story=payload['semantic_story'],
            semantic_direction=payload['semantic_direction'],lyric_timeline=payload['lyric_timeline'],
            to_dict=lambda:payload)
    else:
        subprocess.run(command,check=True,cwd=args.baseline)
        meta=json.loads((args.output/'rhythm.json').read_text())
        from core.audio_intelligence import analyze_audio_file
        analysis=analyze_audio_file(args.audio,enable_lyrics=not args.instrumental,
            cache_dir=args.output/'analysis_cache',log_fn=lambda msg:print(msg,flush=True))
    g=garden()
    (args.output/'analysis.json').write_text(json.dumps(analysis.to_dict(),indent=2,allow_nan=False)+'\n')
    recovered=args.output/'recovered';shutil.copytree(args.output/'baseline',recovered,dirs_exist_ok=True)
    from core.model_parser import parse_layout
    from core.semantic_xsq import append_direction
    tree=ET.parse(recovered/'performance.xsq')
    targets=[m.name for m in g.models if m.name.startswith('SCENE_OUTLINE')]
    original_rows={e.get('name'): [ET.tostring(layer) for layer in e.findall('EffectLayer')]
                   for e in tree.findall('./ElementEffects/Element') if e.get('type')=='model'}
    report=append_direction(tree.getroot(),analysis.semantic_direction,targets,
        parsed_layout=parse_layout(recovered/'xlights_rgbeffects.xml'),duration_ms=round(meta['duration']*1000))
    for name,layers in original_rows.items():
        after=tree.find(f'./ElementEffects/Element[@name="{name}"]')
        assert [ET.tostring(layer) for layer in list(after)[:len(layers)]]==layers
    tree.write(recovered/'performance.xsq',encoding='utf-8',xml_declaration=True)
    (args.output/'semantic_export.json').write_text(json.dumps(report,indent=2)+'\n')
    if not args.xlights:
        raise ValueError('Authentic comparison requires a real native xLights renderer')
    from tools.build_helpers.ultimate_showcase_preview import read_fseq
    frames=[]
    for folder in (args.output/'baseline',recovered):
        xsq=folder/'performance.xsq'
        with (folder/'native.log').open('w') as log:
            subprocess.run([str(args.xlights.resolve()),'--headless','-q','-s',str(folder),
                '-od',str(folder),str(xsq)],check=True,timeout=900,stdout=log,stderr=log,
                env={**os.environ,'XL_NO_GPU_COMPUTE':'1'})
        samples,step=read_fseq(xsq.with_suffix('.fseq'))
        if step!=50 or not samples.any() or len(samples)<math.floor(meta['duration']*20):
            raise ValueError('Incomplete or dark native FSEQ')
        frames.append(samples)
    # Native source samples outside the explicit scenic targets are identical.
    differences=[]
    for model in g.models:
        if model.name in targets:continue
        a,b=model.start-1,model.start-1+model.channels
        n=min(len(x) for x in frames)
        if not np.array_equal(frames[0][:n,a:b],frames[1][:n,a:b]):
            differences.append(model.name)
    if differences:
        raise ValueError('Semantic layer changed non-scenery channels: '+str(differences))
    if args.instrumental and not np.array_equal(*frames):
        raise ValueError('Instrumental fallback changed native samples')
    from tools.showcase_audio_preview import NativeSongView
    from tools.build_helpers.ultimate_showcase_preview import _font
    from PIL import Image, ImageDraw
    views=[NativeSongView(g,args.song_key or args.audio.stem,960,1080,halo_scale=2) for _ in range(2)]
    for view,label in zip(views,('PRODUCTION BASELINE','RECOVERED SEMANTIC SCENERY')):
        view.base=Image.new('RGB',(960,1080),(4,7,14));d=ImageDraw.Draw(view.base)
        d.text((35,45),label,font=_font(25),fill='#e3eaf4')
        d.text((35,88),(args.song_key or args.audio.stem).replace('_',' '),font=_font(22),fill='#6eb8d4')
        d.text((35,1000),'ACTUAL XLIGHTS FSEQ  /  DEVELOPMENT REVIEW',font=_font(15),fill='#89a3b7')
        view.scene_base=view.base.crop(view.box)
    movie=args.output/((args.song_key or args.audio.stem)+'_Full_Song_Comparison.mp4')
    encoder=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080',
        '-r','20','-i','-','-i',str(args.audio),'-map','0:v:0','-map','1:a:0','-t',str(meta['duration']),
        '-c:v','libx264','-preset','veryfast','-crf','22','-threads','2','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','192k','-movflags','+faststart',str(movie)],stdin=subprocess.PIPE)
    try:
        for index in range(math.ceil(meta['duration']*20)):
            canvas=Image.new('RGB',(1920,1080))
            for panel,view in enumerate(views):
                canvas.paste(view.frame(frames[panel][min(index,len(frames[panel])-1)]),(panel*960,0))
            encoder.stdin.write(canvas.tobytes())
    finally:
        encoder.stdin.close()
    if encoder.wait():raise RuntimeError('Comparison video encoding failed')
    subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True,timeout=900)
    # Source-clock correlation compares original PCM with decoded final audio.
    def pcm(path):
        return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0',
                             '-ac','1','-ar','16000','-f','f32le','-']),dtype='<f4')
    source,output=pcm(args.audio),pcm(movie);n=min(len(source),len(output))
    corr=float(np.corrcoef(source[:n],output[:n])[0,1])
    if corr < .98:raise ValueError('Original soundtrack not aligned at timeline zero')
    result=dict(schema='helix.semantic_benchmark.v1',source_sha256=meta['original_sha256'],
        decoded_audio_sha256=digest(args.audio),semantic_backend=analysis.semantic_story.get('semantic_backend',{'status':'contextual_rules'}),
        baseline_commit=meta['baseline_commit'],duration=meta['duration'],
        words=len(analysis.lyric_timeline.get('words',[])),semantic_effects=report['effects'],
        semantic_intents=len(analysis.semantic_direction.get('intents',[])),
        original_layers_preserved=True,non_scenic_native_samples_identical=True,
        instrumental_native_samples_identical=bool(args.instrumental),soundtrack_zero_lag_correlation=corr,
        full_video_decode=True,movie=str(movie.name),movie_sha256=digest(movie),
        visual_review='pending',independent_asr_accuracy='not_measured',
        scope='scenery comparison; does not establish a full-band or device release gate')
    (args.output/'benchmark.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
