"""Present actual native renders as compact review movies; never confer acceptance.

Inputs are immutable native movies plus separately hashed original soundtracks.
Only framing, a declared display curve, labels, and synchronized cuts are applied.
"""
import argparse
import json
from pathlib import Path
import subprocess
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


def encode(args, output, duration):
    temporary=output.with_name(output.stem+'.encoding.mp4')
    cmd=['ffmpeg','-v','error','-nostdin','-y','-filter_threads','2','-filter_complex_threads','2',*args,
         '-t',str(duration),'-c:v','libx264','-threads','4','-preset','fast','-crf','21','-pix_fmt','yuv420p',
         '-r','20','-c:a','aac','-b:a','192k','-movflags','+faststart',str(temporary)]
    try:
        subprocess.run(cmd,check=True)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return cmd


def check_inputs(item):
    audio=Path(item['audio'])
    if digest(audio)!=item['audio_sha256']:raise ValueError('Original soundtrack hash mismatch')
    for spec in item['sources']:
        p=Path(spec['video'])
        if digest(p)!=spec['video_sha256']:raise ValueError('Native video hash mismatch')
    duration=sf.info(audio).duration
    if abs(duration-float(item['duration']))>0.001:raise ValueError('Soundtrack duration mismatch')
    return duration


def assemble(config, output):
    output.mkdir(parents=True,exist_ok=True)
    reports=[]
    for item in config['movies']:
        duration=check_inputs(item);target=output/item['filename'];sources=item['sources']
        if target.name!=item['filename'] or target.suffix!='.mp4':raise ValueError('Plain MP4 basenames required')
        print('ENCODING '+target.name,flush=True)
        args=[]
        for spec in sources:args+=['-i',spec['video']]
        args+=['-i',item['audio']]
        if item['kind']=='single':
            if len(sources)!=1:raise ValueError('One native source expected')
            args+=['-map','0:v:0','-map','1:a:0','-vf',visual(sources[0])+','+caption(item['title'])]
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
        elif item['kind']=='montage':
            f=[];segments=item['segments'];position=0
            for i,seg in enumerate(segments):
                if abs(seg['start']-position)>0.001 or seg['end']<=seg['start']:raise ValueError('Cuts must preserve source timeline')
                position=seg['end'];s=seg['source']
                f.append(f'[{s}:v]trim=start={seg["start"]}:end={seg["end"]},setpts=PTS-STARTPTS,'+
                         visual(sources[s])+','+caption(sources[s]['title'])+f'[s{i}]')
            if abs(position-duration)>0.001:raise ValueError('Cuts must cover original soundtrack')
            f.append(''.join(f'[s{i}]' for i in range(len(segments)))+f'concat=n={len(segments)}:v=1:a=0[out]')
            args+=['-filter_complex',';'.join(f),'-map','[out]','-map',f'{len(sources)}:a:0']
        else:raise ValueError('Unsupported presentation')
        cmd=encode(args,target,duration)
        reports.append(dict(filename=target.name,bytes=target.stat().st_size,sha256=digest(target),
                            source=item,ffmpeg_command=cmd,visual_acceptance=False))
        (output.parent/'assembly_receipt.json').write_text(json.dumps(dict(
            schema='helix.native-review-assembly.v1',source_commit=config['source_commit'],movies=reports,
            beta_acceptance=False,limitations=config['limitations']),indent=2)+'\n')
    return reports


def package(folder, target, expected_names):
    if len(expected_names)!=6 or len(set(expected_names))!=6:raise ValueError('Exactly six distinct movies required')
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
        for name in expected_names:
            p=folder/name
            if p.name!=name or p.suffix!='.mp4':raise ValueError('MP4-only archive required')
            z.write(p,arcname=name)
    with zipfile.ZipFile(target) as z:
        if z.namelist()!=expected_names or z.testzip() is not None:raise ValueError('Archive inventory or CRC failed')
        import hashlib
        for name in expected_names:
            with z.open(name) as stream:
                h=hashlib.sha256()
                for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
            if h.hexdigest()!=digest(folder/name):raise ValueError('Archived movie hash mismatch')
    return dict(filename=target.name,sha256=digest(target),bytes=target.stat().st_size,entries=expected_names,crc_and_hashes_verified=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('config',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--package',type=Path);a=p.parse_args();c=json.loads(a.config.read_text())
    assemble(c,a.output)
    if a.package:print(json.dumps(package(a.output,a.package,[m['filename'] for m in c['movies']]),indent=2))
