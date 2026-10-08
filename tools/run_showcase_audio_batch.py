"""Run source-verified uploaded music through Helix Prime on six native layouts."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from contextlib import redirect_stdout
import hashlib
import html
import json
import math
import multiprocessing
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np

from core.audio_run_cache import AudioRunCache
from core import effect_engine as engine
from models.showcase_flavors import FLAVORS,build_flavor
from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.showcase_audio_native import prepare_template,native_music_xsq
from tools.showcase_audio_preview import render_native_song

TRACKS=(('Wire_Tree','Wire Tree'),('Tinsel_Sawtooth','Tinsel Sawtooth'),
        ('Frostbitten_Fingerboard','Frostbitten Fingerboard'),('Holly_Steel_Run','Holly Steel Run'),
        ('Bell_Circuit_Carol','Bell Circuit Carol'))


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_routes(g)->dict:
    """Explicit native-family pools include both sides, including -1 names."""
    pools={'mega':[],'arch':[],'canes_single':[],'sphere':[],'spinner':[],'matrix':[],'line':[],'snowflakes':[],'stars':[]}
    for m in g.models:
        if m.kind!='pixel':continue
        display=m.display
        category=('mega' if display.startswith('Tree') else 'arch' if display=='Arches' else
                  'canes_single' if display=='Candy Canes' else 'sphere' if display in ('Sphere','Circle','Wreath') else
                  'spinner' if display=='Spinner' else 'matrix' if display.startswith('Matrix') or display=='Cube' or m.details.get('double_helix') else
                  'stars' if display=='Star' else 'snowflakes' if 'SNOWFLAKE' in m.name else 'line')
        pools[category].append(m.name)
    pools['mega_models']=pools['mega'];pools['line_models']=pools['line']
    return {key:value for key,value in pools.items() if value}


def write_progress(root,manifest):
    temp=root/'batch_manifest.tmp';temp.write_text(json.dumps(manifest,indent=2)+'\n');temp.replace(root/'batch_manifest.json')


def generate(root:Path,audio_dir:Path,*,track:str|None=None,flavor:str|None=None)->dict:
    audios=sorted(audio_dir.glob('*.mp3'))
    if len(audios)!=5:raise ValueError('Expected exactly five uploaded MP3 tracks, ordered 1–5.')
    selected_flavors=[f for f in FLAVORS if flavor is None or f.key==flavor]
    selected_tracks=[(entry,source) for entry,source in zip(TRACKS,audios,strict=True) if track is None or entry[0]==track]
    templates={};gardens={}
    for f in selected_flavors:
        g=build_flavor(f.key);gardens[f.key]=g;templates[f.key]=prepare_template(g,root/'templates'/g.slug)
    manifest={'schema':'helix.showcase_audio_batch.v1','engine':'Helix Prime v27.3','requested_combinations':len(selected_flavors)*len(selected_tracks),
              'sources':[],'runs':[],'review_status':'pending_user_review','analysis_cache':{},'preserved_layouts_and_drummers':True}
    for (slug,title),source in selected_tracks:
        sha=digest(source);cache=AudioRunCache(sha);duration=None
        for f in selected_flavors:
            g=gardens[f.key];folder=root/'shows'/slug/g.slug;folder.mkdir(parents=True,exist_ok=True)
            template_dir=templates[f.key].parent
            for name in ('xlights_rgbeffects.xml','xlights_networks.xml','assets','models'):
                p=template_dir/name
                if p.is_dir():shutil.copytree(p,folder/name,dirs_exist_ok=True)
                else:shutil.copy2(p,folder/name)
            media=folder/(slug+'.mp3');shutil.copy2(source,media)
            if digest(media)!=sha:raise ValueError('Source audio changed while copying')
            raw=folder/(slug+'.prime_raw.xsq')
            tuning=engine.RuntimeTuning(layout_file=folder/'xlights_rgbeffects.xml',template_guidance=False,
                workspace_history_enabled=False,learning_memory_enabled=False,matrix_intelligence=False,
                polish_enabled=False,variant_count=1,birdsong_enabled=False,birdsong_auto=False,
                audio_reactive_profile='showcase',audio_reactive_intensity=1.6,spatial_awareness=.85,
                chase_style='radial_out',model_overrides=model_routes(g),max_layers_per_prop=3)
            with (folder/'engine.log').open('w') as log,redirect_stdout(log):
                engine.run_variant(engine.VARIANTS['v27.3'],templates[f.key],media,raw,engine.base.UserProfile(),tuning=tuning,analysis_cache=cache)
            duration=float(cache.values['audio'].dur_s)
            native=folder/(slug+'__'+g.slug+'.xsq')
            export=native_music_xsq(raw,native,g,media,duration)
            row={'track':slug,'title':title,'flavor':f.key,'layout':g.title,'folder':str(folder.relative_to(root)),
                 'audio':media.name,'audio_sha256':sha,'duration_seconds':duration,'xsq':native.name,
                 'export':export,'status':'sequence_generated'}
            manifest['runs'].append(row);write_progress(root,manifest)
            print(json.dumps({'stage':'generated','track':title,'layout':g.title,'effects':export['native_effects'],'runs':len(manifest['runs'])}),flush=True)
        manifest['sources'].append({'track':slug,'title':title,'original_name':source.name,'sha256':sha,'duration_seconds':duration})
        manifest['analysis_cache'][slug]={'cached_stages':list(cache.values),'reuse_hits':cache.hits,'layouts':len(selected_flavors)}
        write_progress(root,manifest)
    return manifest


def finish_one(root:Path,row:dict,xlights:Path)->dict:
    folder=root/row['folder'];g=build_flavor(row['flavor']);xsq=folder/row['xsq'];fseq=xsq.with_suffix('.fseq')
    proof_path=folder/'verification.json'
    if digest(folder/row['audio'])!=row['audio_sha256']:
        raise ValueError('Uploaded soundtrack no longer matches the verified source')
    if proof_path.exists():
        proof=json.loads(proof_path.read_text())
        movie=folder/proof.get('mp4','missing')
        if (proof.get('xsq_sha256')==digest(xsq) and proof.get('audio_sha256')==row['audio_sha256']
            and proof.get('layout_sha256')==digest(folder/'xlights_rgbeffects.xml')
            and fseq.is_file() and proof.get('fseq_sha256')==digest(fseq)
            and movie.is_file() and proof.get('mp4_sha256')==digest(movie)):
            return proof
    stamp=folder/'native_render_stamp.json'
    render_id={'xsq_sha256':digest(xsq),'layout_sha256':digest(folder/'xlights_rgbeffects.xml')}
    if not fseq.exists() or not stamp.exists() or json.loads(stamp.read_text())!=render_id:
        with (folder/'native_render.log').open('w') as log:
            subprocess.run([str(xlights.resolve()),'--headless','-q','-s',str(folder.resolve()),'-od',str(folder.resolve()),str(xsq.resolve())],
                env={**os.environ,'XL_NO_GPU_COMPUTE':'1'},stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
        stamp.write_text(json.dumps(render_id,indent=2)+'\n')
    frames,step=read_fseq(fseq)
    expected=int(math.ceil(row['duration_seconds']*1000/step))
    if len(frames)!=expected:raise ValueError(f'Native duration mismatch: {len(frames)} != {expected}')
    coverage=[];controls=[]
    for m in g.models:
        values=frames[:,m.start-1:m.start-1+m.channels]
        if m.kind=='pixel':
            coverage.append({'model':m.name,'active_frames':int(np.sum(values.max(axis=1)>0)),'peak':int(values.max())})
        elif values.any():controls.append(m.name)
    if controls:raise ValueError(f'RGB song activated control channels: {controls}')
    if not frames.any():raise ValueError('Native render is completely dark')
    lit=np.flatnonzero(frames.max(axis=1)>0)
    proof={'track':row['title'],'layout':g.title,'xsq_sha256':digest(xsq),'layout_sha256':render_id['layout_sha256'],'fseq_sha256':digest(fseq),
           'audio_sha256':digest(folder/row['audio']),'native_frames':len(frames),'native_frame_ms':step,
           'first_active_ms':int(lit[0])*step,'last_active_ms':int(lit[-1])*step,
           'active_rgb_models':sum(r['active_frames']>0 for r in coverage),'rgb_models':len(coverage),
           'models':coverage,'control_channels_dark':True,'native_channel_animation':bool(np.any(frames[1:]!=frames[:-1]))}
    del frames
    movie=xsq.with_suffix('.mp4')
    proof.update(render_native_song(g,fseq,folder/row['audio'],movie,row['duration_seconds']))
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height,r_frame_rate,nb_frames:format=duration','-of','json',str(movie)]))
    if not any(s['codec_type']=='audio' for s in probe['streams']):raise ValueError('Song soundtrack missing')
    if abs(float(probe['format']['duration'])-row['duration_seconds'])>.15:raise ValueError('Preview duration mismatch')
    proof['mp4']=movie.name;proof['probe']=probe;proof['mp4_sha256']=digest(movie)
    frames_dir=folder/'review_frames';frames_dir.mkdir(exist_ok=True)
    for second in (1,round(row['duration_seconds']/2,2),round(row['duration_seconds']-1,2)):
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(second),'-i',str(movie),'-frames:v','1',str(frames_dir/f'{second}s.png')],check=True)
    proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    return proof


def gallery(root:Path,manifest:dict):
    cards=[]
    for slug,title in TRACKS:
        links=[]
        for row in manifest['runs']:
            if row['track']!=slug:continue
            folder=row['folder'];xsq=row['xsq'];movie=Path(xsq).with_suffix('.mp4').name
            links.append(f'<div><b>{html.escape(row["layout"].removeprefix("Helix "))}</b><a href="{folder}/{movie}">Watch full song</a><a href="{folder}/{xsq}">XSQ</a><a href="{folder}/verification.json">Native proof</a></div>')
        if not links:continue
        review=manifest.get('review_reels',{}).get(slug)
        package=manifest.get('packages',{}).get(slug)
        extras=''
        if review:extras+=f'<p><a href="{review["file"]}">Watch six layouts together — 24-second comparison</a></p>'
        if package:extras+=f'<p><a href="{package["file"]}">Download all six importable shows</a> · {package["bytes"]/1e6:.1f} MB</p>'
        cards.append(f'<section><h2>{title}</h2>'+extras+''.join(links)+'</section>')
    page='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Helix — Five Songs, Six Worlds</title>
<style>body{background:#080e1a;color:#e4f4fc;font:16px system-ui;margin:0}main{max-width:1150px;margin:60px auto;padding:24px}h1{font-size:48px;font-weight:500}p{color:#9db9cc;line-height:1.6}section{margin:28px 0;padding:24px;background:#101d2c;border:1px solid #294358;border-radius:14px}section div{display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin:18px 0}b{min-width:230px}a{color:#76e9e5;text-decoration:none}h2{color:#ffd497}footer{color:#9ab3c5;margin-top:40px}</style>
<main><h1>Five songs. Six worlds.</h1><p>Thirty full-song Helix Prime sequences on the six artistic showcase layouts. Each preview uses actual native xLights channel values and its original uploaded song. Open a layout folder as a new xLights 2026.18+ show; retain its assets and media file.</p>__CARDS__<footer>Artistic and musical review remains yours. RGB lighting is sequenced; control and servo fixtures remain isolated. Custom grids match the export; stock review geometry is illustrative.</footer></main>'''
    (root/'index.html').write_text(page.replace('__CARDS__',''.join(cards)),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio-dir',type=Path)
    parser.add_argument('--output',type=Path,default=Path('outputs/showcase_audio'))
    parser.add_argument('--xlights',type=Path,required=True)
    parser.add_argument('--finish-existing',action='store_true')
    parser.add_argument('--track',choices=[entry[0] for entry in TRACKS])
    parser.add_argument('--flavor',choices=[f.key for f in FLAVORS])
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    if args.finish_existing:manifest=json.loads((args.output/'batch_manifest.json').read_text())
    else:
        if not args.audio_dir:parser.error('--audio-dir required for generation')
        manifest=generate(args.output,args.audio_dir,track=args.track,flavor=args.flavor)
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as executor:
        futures={executor.submit(finish_one,args.output,row,args.xlights):row for row in manifest['runs']}
        for future in as_completed(futures):
            row=futures[future];proof=future.result();row['status']='verified_preview';row['verification']=proof
            write_progress(args.output,manifest)
            print(json.dumps({'stage':'verified_preview','track':row['title'],'layout':row['layout'],'active_models':proof['active_rgb_models'],'complete':sum(r['status']=='verified_preview' for r in manifest['runs'])}),flush=True)
    gallery(args.output,manifest)
    print('Complete: '+str(args.output/'index.html'),flush=True)


if __name__=='__main__':main()
