"""Verify the actual soundtrack and package the thirty native song/layout shows."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

import numpy as np
from PIL import Image,ImageDraw

from tools.build_helpers.ultimate_showcase_preview import _font
from tools.run_showcase_audio_batch import TRACKS,digest,gallery,write_progress
from tools.build_helpers.ultimate_showcase_preview import read_fseq


def decode_audio(path:Path,*,start:float=0,duration:float|None=None)->np.ndarray:
    command=['ffmpeg','-v','error']
    if start:command.extend(['-ss',str(start)])
    command.extend(['-i',str(path),'-map','0:a:0'])
    if duration is not None:command.extend(['-t',str(duration)])
    data=subprocess.check_output(command+['-ac','1','-ar','2000','-f','f32le','-'])
    return np.frombuffer(data,dtype='<f4')


def verify_soundtracks(root:Path,manifest:dict)->dict:
    """Compare decoded originals; identical AAC streams reuse the full audit."""
    sources={};audited={};rows=[]
    for row in manifest['runs']:
        folder=root/row['folder'];movie=folder/Path(row['xsq']).with_suffix('.mp4');source=folder/row['audio']
        if digest(source)!=row['audio_sha256']:raise ValueError('Source media bytes changed')
        encoded=subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-map','0:a:0','-c:a','copy','-f','adts','-'])
        audio_sha=hashlib.sha256(encoded).hexdigest();key=(row['audio_sha256'],audio_sha)
        if key not in audited:
            if row['track'] not in sources:sources[row['track']]=decode_audio(source)
            original=sources[row['track']]
            soundtrack=decode_audio(movie);size=min(len(original),len(soundtrack))
            correlation=float(np.corrcoef(original[:size],soundtrack[:size])[0,1])
            if not np.isfinite(correlation) or correlation<.97:
                raise ValueError(f'Soundtrack mismatch: {row["title"]} correlation={correlation}')
            if abs(len(soundtrack)-len(original))/2000>.15:
                raise ValueError('Decoded soundtrack duration differs from source')
            audited[key]={'correlation':correlation,'decoded_sample_rate':2000,'compared_seconds':size/2000,
                          'decoded_source_seconds':len(original)/2000,'decoded_preview_seconds':len(soundtrack)/2000}
        rows.append({'track':row['track'],'flavor':row['flavor'],'aac_stream_sha256':audio_sha,**audited[key]})
    report={'schema':'helix.showcase_soundtrack_verification.v1','comparisons':rows,
            'unique_originals':len(sources),'unique_aac_comparisons':len(audited),'all_sources_match':True}
    (root/'soundtrack_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def package_imports(root:Path,manifest:dict)->dict:
    packages={}
    for slug,title in TRACKS:
        rows=[row for row in manifest['runs'] if row['track']==slug]
        if not rows:continue
        path=root/(slug+'_Six_Layouts_Import.zip')
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            archive.writestr('README.txt',f'{title} — {len(rows)} native Helix layouts\n\nOpen one layout directory as a new xLights 2026.18+ show, then open its XSQ.\nKeep its assets and original MP3 alongside it. Render locally before output.\nFull-song review videos are linked from the accompanying batch gallery.\nControl/servo fixtures are present in the layouts but are not driven by RGB song effects.\nNo physical installation, controller allocation or musical acceptance is implied.\n')
            for row in rows:
                folder=root/row['folder'];show=Path(folder.name)
                names=[folder/row['xsq'],folder/row['audio'],folder/'xlights_rgbeffects.xml',
                       folder/'xlights_networks.xml',folder/'verification.json']
                for sub in ('assets','models'):
                    names.extend(p for p in (folder/sub).rglob('*') if p.is_file())
                for source in names:archive.write(source,show/source.relative_to(folder))
            archive.writestr('song_manifest.json',json.dumps({'source':next(s for s in manifest['sources'] if s['track']==slug),
                'layouts':[{'title':r['layout'],'xsq':r['xsq'],'folder':Path(r['folder']).name} for r in rows]},indent=2))
        with zipfile.ZipFile(path) as archive:
            if archive.testzip():raise ValueError('Import ZIP CRC check failed')
            if sum(n.endswith('.xsq') for n in archive.namelist())!=len(rows):raise ValueError('Missing packaged XSQ')
        packages[slug]={'file':path.name,'sha256':digest(path),'bytes':path.stat().st_size,'layouts':len(rows)}
    (root/'package_manifest.json').write_text(json.dumps(packages,indent=2)+'\n')
    return packages


def representative_times(root:Path,manifest:dict)->dict:
    """Choose a real bright native frame for review, without altering output."""
    chosen={}
    for slug,_ in TRACKS:
        row=next((r for r in manifest['runs'] if r['track']==slug),None)
        if row is None:continue
        frames,step=read_fseq(root/row['folder']/Path(row['xsq']).with_suffix('.fseq'))
        start=int(len(frames)*.15);end=max(start+1,int(len(frames)*.85))
        index=int(np.argmax(frames[start:end].sum(axis=1,dtype=np.uint64)))+start
        chosen[slug]=round(index*step/1000,2)
        del frames
    (root/'representative_times.json').write_text(json.dumps({'selection':'brightest native frame in middle 70% of first layout; all six shown at same song time','seconds':chosen},indent=2)+'\n')
    return chosen


def comparison_reels(root:Path,manifest:dict,times:dict|None=None):
    """One same-time/same-song six-layout view per track, full previews retained."""
    reels={}
    for slug,title in TRACKS:
        rows=[r for r in manifest['runs'] if r['track']==slug]
        if len(rows)!=6:continue
        center=(times or {}).get(slug,24)
        start=min(max(0,center-12),max(0,rows[0]['duration_seconds']-24));duration=min(24,rows[0]['duration_seconds']-start)
        output=root/(slug+'_Six_Layouts_Review.mp4')
        args=['ffmpeg','-v','error','-y','-threads','1','-filter_complex_threads','1']
        for row in rows:
            args.extend(['-threads','1','-ss',str(start),'-i',str(root/row['folder']/Path(row['xsq']).with_suffix('.mp4'))])
        source=root/rows[0]['folder']/rows[0]['audio']
        args.extend(['-ss',str(start),'-i',str(source)])
        filters=[f'[{i}:v]scale=640:360[v{i}]' for i in range(6)]
        filters.append(''.join(f'[v{i}]' for i in range(6))+'xstack=inputs=6:layout=0_0|640_0|1280_0|0_360|640_360|1280_360[v]')
        args.extend(['-filter_complex',';'.join(filters),'-map','[v]','-map','6:a:0','-t',str(duration),
            '-c:v','libx264','-preset','veryfast','-crf','22','-threads','1','-pix_fmt','yuv420p',
            '-c:a','aac','-b:a','192k','-movflags','+faststart',str(output)])
        subprocess.run(args,check=True)
        original=decode_audio(source,start=start,duration=duration);actual=decode_audio(output)
        size=min(len(original),len(actual));correlation=float(np.corrcoef(original[:size],actual[:size])[0,1])
        if correlation<.97 or not np.isfinite(correlation):raise ValueError('Comparison reel soundtrack mismatch')
        reels[slug]={'file':output.name,'song_start_seconds':start,'duration_seconds':duration,'sha256':digest(output),
                     'soundtrack_correlation':correlation}
    (root/'review_reels.json').write_text(json.dumps(reels,indent=2)+'\n')
    return reels


def contact_sheets(root:Path,manifest:dict,times:dict|None=None):
    for slug,title in TRACKS:
        rows=[r for r in manifest['runs'] if r['track']==slug]
        if not rows:continue
        image=Image.new('RGB',(1920,1160),(8,14,26));draw=ImageDraw.Draw(image)
        draw.text((32,20),title+' — six full-song native lighting previews',font=_font(30),fill=(225,244,255))
        for i,row in enumerate(rows):
            folder=root/row['folder'];second=(times or {}).get(slug,row['duration_seconds']/2)
            middle=folder/'review_frames'/'comparison.png'
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(second),'-i',str(folder/Path(row['xsq']).with_suffix('.mp4')),
                '-frames:v','1',str(middle)],check=True)
            thumb=Image.open(middle).resize((640,360),Image.Resampling.LANCZOS)
            x=(i%3)*640;y=80+(i//3)*400;image.paste(thumb,(x,y))
            draw.text((x+18,y+365),row['layout'],font=_font(22),fill=(167,211,229))
        image.crop((0,0,1920,900)).save(root/(slug+'_Six_Layouts.png'))


def package_review_bundle(root:Path,manifest:dict)->Path:
    """Offline gallery plus every full preview/native show; omit temporary runs."""
    files=[root/name for name in ('index.html','batch_manifest.json','soundtrack_verification.json','package_manifest.json',
        'review_reels.json','representative_times.json')]
    files.extend(root/name for name in ('native_alias_before_after.json','native_effect_probe.json') if (root/name).is_file())
    files.extend(root/p['file'] for p in manifest['packages'].values())
    files.extend(root/p['file'] for p in manifest['review_reels'].values())
    files.extend(root.glob('*_Six_Layouts.png'))
    for row in manifest['runs']:
        folder=root/row['folder'];xsq=folder/row['xsq']
        files.extend([xsq,xsq.with_suffix('.mp4'),xsq.with_suffix('.fseq'),folder/row['audio'],folder/'verification.json',
                      folder/'native_render_stamp.json',folder/'xlights_rgbeffects.xml',folder/'xlights_networks.xml'])
        for sub in ('assets','models','review_frames'):
            files.extend(p for p in (folder/sub).rglob('*') if p.is_file())
    output=root/'Helix_Five_Songs_Six_Layouts_Full_Review.zip'
    with zipfile.ZipFile(output,'w') as archive:
        for source in dict.fromkeys(files):
            compression=zipfile.ZIP_STORED if source.suffix.lower() in ('.mp4','.mp3','.fseq','.png','.zip') else zipfile.ZIP_DEFLATED
            archive.write(source,source.relative_to(root),compress_type=compression)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip():raise ValueError('Full review ZIP CRC check failed')
        assert sum(n.endswith('.xsq') for n in archive.namelist())==len(manifest['runs'])
    (root/'full_review_bundle.json').write_text(json.dumps({'file':output.name,'bytes':output.stat().st_size,'sha256':digest(output),
        'full_song_videos':len(manifest['runs']),'native_xsqs':len(manifest['runs']),'native_fseqs':len(manifest['runs'])},indent=2)+'\n')
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=Path('outputs/showcase_audio'))
    args=parser.parse_args();root=args.output;manifest=json.loads((root/'batch_manifest.json').read_text())
    if any(r['status']!='verified_preview' for r in manifest['runs']):raise ValueError('All requested previews must verify before packaging')
    verify_soundtracks(root,manifest);manifest['packages']=package_imports(root,manifest)
    times=representative_times(root,manifest)
    manifest['review_reels']=comparison_reels(root,manifest,times);contact_sheets(root,manifest,times)
    write_progress(root,manifest);gallery(root,manifest)
    package_review_bundle(root,manifest)
    print('Verified source audio and packaged review: '+str(root/'index.html'))


if __name__=='__main__':main()
