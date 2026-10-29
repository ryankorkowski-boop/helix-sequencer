"""Present actual native renders as compact review movies; never confer acceptance.

Inputs are immutable native movies plus separately hashed original soundtracks.
Only framing, a declared display curve, labels, and synchronized cuts are applied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import zipfile
import soundfile as sf
from tools.phoneme_source import digest


def caption(text, size=26, y=24):
    # Keep filter syntax separate from arbitrary external metadata.
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .+/-()' for c in text):
        raise ValueError('Caption requires plain safe text')
    return (f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{text}':"
            f"fontcolor=white:fontsize={size}:x=(w-tw)/2:y={y}:box=1:boxcolor=black@0.65:boxborderw=8")


def visual(spec, width=1280, height=720):
    gamma=float(spec['gamma'])
    if not 1 <= gamma <= 3:raise ValueError('Undeclared or excessive display curve')
    crop=spec.get('crop')
    crop_filter=''
    if crop:
        if len(crop)!=4 or any(not isinstance(v,int) or v<0 for v in crop):raise ValueError('Invalid framing')
        crop_filter='crop='+':'.join(map(str,crop))+','
    gain=float(spec.get('gain',1))
    if not 1<=gain<=2:raise ValueError('Display gain outside declared review limits')
    curve=f"min(255,pow(val/255,1/{gamma})*255*{gain})"
    # Apply the curve in RGB: gamma on limited-range luma lifts legal black
    # (16) into visible gray and falsely inflates readability measurements.
    return (f'{crop_filter}scale={width}:{height}:flags=lanczos,setsar=1,format=gbrp,'
            f"lutrgb=r='{curve}':g='{curve}':b='{curve}',format=yuv420p")


def encode(args, output, duration, *, copy_video=False):
    temporary=output.with_name(output.stem+'.encoding.mp4')
    video_options=(['-c:v','copy'] if copy_video else
        ['-c:v','libx264','-threads','4','-preset','fast','-crf','21','-pix_fmt','yuv420p','-r','20'])
    cmd=['ffmpeg','-v','error','-nostdin','-y','-filter_threads','2','-filter_complex_threads','2',*args,
         '-t',str(duration),*video_options,'-c:a','aac','-b:a','192k','-movflags','+faststart',str(temporary)]
    try:
        subprocess.run(cmd,check=True)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return cmd


def encode_montage(item, output, duration, encoder):
    """Encode bounded source intervals; never buffer several full HD timelines."""
    segments=item['segments'];position=0;commands=[];clips=[]
    cache=output.parent.parent/'montage-cache';cache.mkdir(exist_ok=True)
    for seg in segments:
        if abs(seg['start']-position)>.001 or seg['end']<=seg['start']:
            raise ValueError('Cuts must preserve source timeline')
        position=seg['end']
        source=item['sources'][seg['source']]
        recipe=dict(item,sources=[source],segments=[seg])
        key=assembly_key(recipe,encoder);clip=cache/(key+'.mp4');receipt=cache/(key+'.json')
        prior={}
        try:prior=json.loads(receipt.read_text())
        except (OSError,ValueError):pass
        if not (clip.is_file() and prior.get('decode_verified') is True and prior.get('sha256')==digest(clip)):
            args=['-ss',str(seg['start']),'-threads','1','-i',source['video'],'-map','0:v:0','-an','-vf',
                  visual(source,*item.get('dimensions',(1280,720)))+','+caption(source['title'])]
            cmd=encode(args,clip,seg['end']-seg['start'])
            subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-i',str(clip),
                            '-map','0:v:0','-f','null','-'],check=True)
            prior=dict(sha256=digest(clip),decode_verified=True,command=cmd)
            temporary=receipt.with_suffix('.tmp');temporary.write_text(json.dumps(prior)+'\n');temporary.replace(receipt)
        commands.append(prior['command']);clips.append(clip)
    if abs(position-duration)>.001:raise ValueError('Cuts must cover original soundtrack')
    listing=cache/(assembly_key(item,encoder)+'.ffconcat')
    listing.write_text('ffconcat version 1.0\n'+''.join("file '"+p.name+"'\n" for p in clips))
    commands.append(encode(['-f','concat','-safe','1','-i',str(listing),'-i',item['audio'],
                            '-map','0:v:0','-map','1:a:0'],output,duration,copy_video=True))
    return commands


def check_inputs(item):
    audio=Path(item['audio'])
    if digest(audio)!=item['audio_sha256']:raise ValueError('Original soundtrack hash mismatch')
    for spec in item['sources']:
        p=Path(spec['video'])
        if digest(p)!=spec['video_sha256']:raise ValueError('Native video hash mismatch')
    duration=sf.info(audio).duration
    if abs(duration-float(item['duration']))>0.001:raise ValueError('Soundtrack duration mismatch')
    return duration


def assembly_key(item, encoder_identity):
    """Bind presentation reuse to bytes and code, independently of audio DSP.

    Paths may change when restoring a checkpoint. They are locators, not input
    identity; check_inputs still hashes the bytes at every invocation.
    """
    recipe=dict(item)
    recipe.pop('audio',None)
    recipe['sources']=[{k:v for k,v in s.items() if k!='video'} for s in item['sources']]
    payload=dict(recipe=recipe,assembler_sha256=digest(Path(__file__)),encoder=encoder_identity)
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def assemble(config, output, *, force=False):
    output.mkdir(parents=True,exist_ok=True)
    names=[item['filename'] for item in config['movies']]
    if len(set(names))!=len(names):raise ValueError('Distinct movie basenames required')
    cache=output.parent/'assembly-cache';cache.mkdir(exist_ok=True)
    encoder=subprocess.check_output(['ffmpeg','-version'],text=True)
    reports=[]
    for item in config['movies']:
        started=time.perf_counter()
        duration=check_inputs(item);target=output/item['filename'];sources=item['sources']
        if target.name!=item['filename'] or target.suffix!='.mp4':raise ValueError('Plain MP4 basenames required')
        key=assembly_key(item,encoder);sidecar=cache/(target.name+'.json')
        previous={}
        try:previous=json.loads(sidecar.read_text())
        except (OSError,ValueError):pass
        if (not force and target.is_file() and previous.get('assembly_key')==key
                and previous.get('decode_verified') is True and previous.get('sha256')==digest(target)):
            report=dict(previous,source=item,cache_hit=True,elapsed_seconds=time.perf_counter()-started)
            reports.append(report)
            print('REUSING '+target.name,flush=True)
            continue
        print('ENCODING '+target.name,flush=True)
        args=[]
        for spec in sources:args+=['-threads','1','-i',spec['video']]
        args+=['-i',item['audio']]
        if item['kind']=='single':
            if len(sources)!=1:raise ValueError('One native source expected')
            args+=['-map','0:v:0','-map','1:a:0','-vf',visual(sources[0],*item.get('dimensions',(1280,720)))+','+caption(item['title'])]
        elif item['kind']=='vocal_duo':
            if len(sources)!=1:raise ValueError('Both vocal views require the same native frame clock')
            left=dict(sources[0],crop=item['face_crops'][0])
            right=dict(sources[0],crop=item['face_crops'][1])
            f='[0:v]split=2[a][b];[a]'+visual(left,640,640)+'[lead];[b]'+visual(right,640,640)+              '[harmony];[lead][harmony]hstack,pad=1280:720:0:72:black,'+caption(item['title'],24,12)+','+              caption('Lead',23,44).replace('x=(w-tw)/2','x=290')+','+              caption('Harmony',23,44).replace('x=(w-tw)/2','x=910')+'[out]'
            args+=['-filter_complex',f,'-map','[out]','-map','1:a:0']
        elif item['kind']=='comparison':
            if len(sources)!=6:raise ValueError('Exactly six synchronized sources required')
            f=[]
            for i,spec in enumerate(sources):
                f.append(f'[{i}:v]setpts=PTS-STARTPTS,'+visual(spec,640,360)+',pad=640:470:0:48:black,'+
                         caption(spec['title'],22,9)+f'[p{i}]')
            f.append(''.join(f'[p{i}]' for i in range(6))+
                     'xstack=inputs=6:layout=0_0|640_0|1280_0|0_470|640_470|1280_470:fill=black,'+
                     'pad=1920:1080:0:70:black,'+caption(item['title'],30,22)+
                     ','+caption('Identical original audio and source time in all six panels',22,1030)+'[out]')
            args+=['-filter_complex',';'.join(f),'-map','[out]','-map','6:a:0']
        elif item['kind']=='residential_pair':
            if len(sources)!=2:raise ValueError('Exactly two synchronized residential sources required')
            f=[]
            for i,spec in enumerate(sources):
                f.append(f'[{i}:v]setpts=PTS-STARTPTS,'+visual(spec,960,540)+
                         ',pad=960:660:0:60:black,'+caption(spec['title'],26,15)+f'[p{i}]')
            f.append('[p0][p1]hstack,pad=1920:1080:0:180:black,'+
                     caption(item['title'],30,30)+'[out]')
            args+=['-filter_complex',';'.join(f),'-map','[out]','-map','2:a:0']
        elif item['kind']=='montage':
            pass # Bounded per-segment encoding below avoids queued HD frames.
        else:raise ValueError('Unsupported presentation')
        cmd=(encode_montage(item,target,duration,encoder) if item['kind']=='montage'
             else encode(args,target,duration))
        # A completed encoder is not proof that the resulting file decodes.
        subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-i',str(target),
                        '-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
        report=dict(filename=target.name,bytes=target.stat().st_size,sha256=digest(target),
                    source=item,ffmpeg_command=cmd,visual_acceptance=False,assembly_key=key,
                    decode_verified=True,cache_hit=False,elapsed_seconds=time.perf_counter()-started)
        temporary=sidecar.with_suffix('.tmp')
        temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(sidecar)
        reports.append(report)
    receipt=output.parent/'assembly_receipt.json';temporary=receipt.with_suffix('.tmp')
    temporary.write_text(json.dumps(dict(
            schema='helix.native-review-assembly.v1',source_commit=config['source_commit'],movies=reports,
            beta_acceptance=False,limitations=config['limitations']),indent=2)+'\n')
    temporary.replace(receipt)
    return reports


def package(folder, target, expected_names, *, expected_count=6):
    if type(expected_count) is not int or expected_count<1:raise ValueError('Positive movie count required')
    if len(expected_names)!=expected_count or len(set(expected_names))!=expected_count:
        raise ValueError(f'Exactly {expected_count} distinct movies required')
    for name in expected_names:
        p=folder/name
        if p.name!=name or p.suffix!='.mp4':raise ValueError('MP4-only archive required')
        if not p.is_file():raise FileNotFoundError(p)
    temporary=target.with_name(target.name+'.packaging')
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_STORED) as z:
            for name in expected_names:z.write(folder/name,arcname=name)
        with zipfile.ZipFile(temporary) as z:
            if z.namelist()!=expected_names or z.testzip() is not None:raise ValueError('Archive inventory or CRC failed')
            for name in expected_names:
                with z.open(name) as stream:
                    h=hashlib.sha256()
                    for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
                if h.hexdigest()!=digest(folder/name):raise ValueError('Archived movie hash mismatch')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return dict(filename=target.name,sha256=digest(target),bytes=target.stat().st_size,entries=expected_names,crc_and_hashes_verified=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('config',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--package',type=Path);p.add_argument('--force',action='store_true')
    a=p.parse_args();c=json.loads(a.config.read_text())
    assemble(c,a.output,force=a.force)
    if a.package:print(json.dumps(package(a.output,a.package,[m['filename'] for m in c['movies']],
        expected_count=c.get('expected_movie_count',6)),indent=2))
