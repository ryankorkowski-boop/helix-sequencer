"""New samplers covering every tracked song, using retained advanced native layouts."""
from __future__ import annotations
import argparse
from contextlib import redirect_stdout
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw
from core.audio_run_cache import AudioRunCache
from core import effect_engine as engine
from models.showcase_flavors import FLAVORS,build_flavor
from tools.run_showcase_audio_batch import model_routes
from tools.showcase_audio_native import prepare_template,native_music_xsq
from tools.showcase_audio_preview import NativeSongView,render_native_song
from tools.fseq_pixel_preview import FseqReader
from tools.build_helpers.ultimate_showcase_preview import _font

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'evidence/drummer/dry_drum_test.wav':'Synthetic dry-drum calibration fixture, not a song'}
AUDIO_SUFFIXES={'.mp3','.wav','.flac','.ogg','.m4a','.aac'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while data:=f.read(1024*1024):h.update(data)
    return h.hexdigest()


def inventory(output):
    result=[];duplicates=[];excluded=[];known={};sources=output/'sources';sources.mkdir(exist_ok=True)
    entries=subprocess.check_output(['git','ls-tree','-r','HEAD'],cwd=ROOT,text=True).splitlines()
    for line in entries:
        head,name=line.split('\t',1);blob=head.split()[2]
        if Path(name).suffix.lower() not in AUDIO_SUFFIXES:continue
        if name in EXCLUDED:excluded.append({'path':name,'reason':EXCLUDED[name]});continue
        if blob in known:duplicates.append({'path':name,'same_bytes_as':known[blob]});continue
        known[blob]=name;source=sources/(str(len(result)+1)+'-'+Path(name).name)
        with source.open('wb') as f:subprocess.run(['git','show','HEAD:'+name],cwd=ROOT,stdout=f,check=True)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(source)]))
        title=Path(name).stem
        if title[:1].isdigit():title=title.split('-',1)[1].replace('-1-','').replace('-',' ')
        title=title.replace(' (1)','')
        result.append({'path':name,'blob':blob,'sha256':sha(source),'title':title,'source':str(source.resolve()),'duration':float(probe['format']['duration'])})
    if not result:raise ValueError('No repository songs found')
    return {'songs':result,'duplicate_paths':duplicates,'excluded_audio':excluded}


def montage(root, sources, index):
    folder=root/('sampler_'+chr(65+index));folder.mkdir(exist_ok=True);pieces=[];timeline=[];clock=0
    ordered=sources if index==0 else list(reversed(sources)) if index==1 else sources[2:]+sources[:2]
    for i,track in enumerate(ordered):
        seconds=min(15,track['duration']-.05);start=max(0,(track['duration']-seconds)*(.2,.5,.75)[index]);piece=folder/('clip_%02d.wav'%i)
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(start),'-i',track['source'],'-t',str(seconds),'-ac','2','-ar','44100','-af',f'afade=t=in:d=0.03,afade=t=out:st={seconds-.03}:d=0.03','-c:a','pcm_s16le',str(piece)],check=True)
        data,rate=sf.read(piece,dtype='int16',always_2d=True);assert rate==44100;pieces.append(data)
        duration=len(data)/rate;timeline.append({'title':track['title'],'source_path':track['path'],'source_sha256':track['sha256'],'source_start_seconds':start,'montage_start_seconds':clock,'duration_seconds':duration});clock+=duration
        piece.unlink()
    audio=folder/('Helix_All_Songs_'+chr(65+index)+'.wav');sf.write(audio,np.concatenate(pieces),44100,subtype='PCM_16')
    row={'sampler':chr(65+index),'audio':str(audio.resolve()),'audio_sha256':sha(audio),'duration_seconds':sf.info(audio).duration,'clips':timeline,'runs':[]}
    (folder/'sampler.json').write_text(json.dumps(row,indent=2)+'\n');return folder,row


def sequence_and_native(folder,row,binary):
    audio=Path(row['audio']);cache=AudioRunCache(row['audio_sha256'])
    for flavor in FLAVORS:
        garden=build_flavor(flavor.key);show=folder/garden.slug;show.mkdir(exist_ok=True);template=prepare_template(garden,show);media=show/audio.name;shutil.copyfile(audio,media)
        raw=show/'sampler.prime_raw.xsq';native=show/(garden.slug+'_All_Songs.xsq')
        tuning=engine.RuntimeTuning(layout_file=show/'xlights_rgbeffects.xml',template_guidance=False,workspace_history_enabled=False,learning_memory_enabled=False,matrix_intelligence=False,polish_enabled=False,variant_count=1,birdsong_enabled=False,birdsong_auto=False,audio_reactive_profile='showcase',audio_reactive_intensity=1.6,spatial_awareness=.85,chase_style='radial_out',model_overrides=model_routes(garden),max_layers_per_prop=3)
        with (show/'engine.log').open('w') as log,redirect_stdout(log):engine.run_variant(engine.VARIANTS['v27.3'],template,media,raw,engine.base.UserProfile(),tuning=tuning,analysis_cache=cache)
        export=native_music_xsq(raw,native,garden,media,row['duration_seconds'])
        command=[str(binary),'--headless','-q','-s',str(show.resolve()),'-od',str(show.resolve()),str(native.resolve())]
        if shutil.which('xvfb-run'):command=['xvfb-run','-a',*command]
        with (show/'native_render.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900,env={**os.environ,'XL_NO_GPU_COMPUTE':'1','LIBGL_ALWAYS_SOFTWARE':'1'})
        fseq=native.with_suffix('.fseq');reader=FseqReader(fseq);expected=math.ceil(row['duration_seconds']*20)
        assert reader.info.step_ms==50 and reader.info.frames==expected
        proof={'flavor':flavor.key,'layout':garden.title,'folder':str(show.resolve()),'xsq':str(native.resolve()),'fseq':str(fseq.resolve()),'xsq_sha256':sha(native),'layout_sha256':sha(show/'xlights_rgbeffects.xml'),'fseq_sha256':sha(fseq),'frames':reader.info.frames,'export':export}
        row['runs'].append(proof);(folder/'sampler.json').write_text(json.dumps(row,indent=2)+'\n');print('Native',row['sampler'],flavor.key,reader.info.frames,flush=True)
    row['analysis_cache_hits']=cache.hits


def comparison(folder,row):
    readers=[FseqReader(Path(run['fseq'])) for run in row['runs']];views=[NativeSongView(build_flavor(run['flavor']),'ALL SIX REPO SONGS',640,360,halo_scale=2) for run in row['runs']];iterators=[r.iter_frames() for r in readers];gardens=[build_flavor(run['flavor']) for run in row['runs']]
    proof=[{'layout':run['layout'],'active_models':{},'control_activity':[]} for run in row['runs']];movie=folder/('Helix_All_Songs_'+row['sampler']+'_Six_Layouts.mp4');frames=readers[0].info.frames;duration=row['duration_seconds'];audio=Path(row['audio'])
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x900','-r','20','-i','-','-i',str(audio),'-map','0:v','-map','1:a','-t',str(duration),'-c:v','libx264','-preset','veryfast','-crf','22','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(movie)]
    writer=subprocess.Popen(command,stdin=subprocess.PIPE);font=_font(21);small=_font(15)
    try:
        for i in range(frames):
            t=i/20;clip=next((x for x in reversed(row['clips']) if t>=x['montage_start_seconds']),row['clips'][0]);image=Image.new('RGB',(1920,900),'#07101C');draw=ImageDraw.Draw(image);draw.text((24,17),'ALL REPO SONGS · SAMPLER '+row['sampler']+' · '+clip['title']+' · %.2fs'%t,font=font,fill='#DDF5FF')
            for j,(reader,it,view,garden) in enumerate(zip(readers,iterators,views,gardens)):
                packed=np.frombuffer(next(it),np.uint8);values=np.zeros(max(m.start-1+m.channels for m in garden.models),np.uint8)
                if reader.info.ranges:
                    offset=0
                    for start,count in reader.info.ranges:values[start:start+count]=packed[offset:offset+count];offset+=count
                else:values[:len(packed)]=packed
                for model in garden.models:
                    active=bool(values[model.start-1:model.start-1+model.channels].any())
                    if model.kind=='pixel':proof[j]['active_models'][model.name]=proof[j]['active_models'].get(model.name,0)+int(active)
                    elif active and model.name not in proof[j]['control_activity']:proof[j]['control_activity'].append(model.name)
                x=j%3*640;y=60+j//3*410;image.paste(view.frame(values),(x,y));draw.text((x+18,y+367),row['runs'][j]['layout'],font=font,fill='#BFDCE8')
            draw.text((24,878),'Native xLights FSEQ colors · Current retained layouts/engine · Stock geometry illustrative · Original song clips',font=small,fill='#AEC5D5');writer.stdin.write(image.tobytes())
            if i in (5,150,350,650,950,1250,1550,frames-2):image.save(folder/('decoded_source_%04d.png'%i))
            if i%200==0:print('Movie',row['sampler'],i,frames,flush=True)
    except BaseException:writer.terminate();raise
    finally:writer.stdin.close()
    if writer.wait():raise RuntimeError('Native comparison encoder failed')
    assert all(not r['control_activity'] for r in proof)
    assert all(any(r['active_models'].values()) for r in proof)
    row['comparison']=str(movie.resolve());row['native_activity']=proof
    if row['sampler']=='A':
        for index in (0,2):
            run=row['runs'][index];single=folder/('Helix_All_Songs_A_'+run['flavor']+'.mp4');render_native_song(gardens[index],Path(run['fseq']),audio,single,duration);row.setdefault('individual_movies',[]).append(str(single.resolve()))
    (folder/'sampler.json').write_text(json.dumps(row,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--xlights',type=Path,required=True);parser.add_argument('--batches',type=int,default=3);args=parser.parse_args()
    if not 1<=args.batches<=3:raise ValueError('Use1–3 batches')
    root=args.output.resolve();root.mkdir(parents=True,exist_ok=True);inv=inventory(root);manifest={'schema':'helix.all_repo_song_samplers.v1','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'inventory':inv,'samples':[],'engine':'retained current Helix Prime v27.3 advanced-native preset','layout_keys':[f.key for f in FLAVORS],'runner_sha256':sha(Path(__file__)),'lighting_source_sha256':{name:sha(ROOT/name) for name in ('core/effect_engine.py','core/sequence_builder.py','tools/showcase_audio_native.py','models/showcase_flavors.py','tools/showcase_audio_preview.py')}}
    for index in range(args.batches):
        folder,row=montage(root,inv['songs'],index);sequence_and_native(folder,row,args.xlights.resolve());comparison(folder,row);manifest['samples'].append(row);(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert all(sha(Path(t['source']))==t['sha256'] for t in inv['songs'])
    print('All-song native sampler batch complete',flush=True)

if __name__=='__main__':main()
