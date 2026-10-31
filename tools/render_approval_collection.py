"""Render and package real native videos, retaining every failed acceptance gate."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import uuid
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from tools.native_preview import preview_run, probe_media
from tools.verify_showcase_luma import verify_mp4
from tools.phoneme_source import digest, EXPECTED_SHA256


def command(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)


def pcm(path):
    return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0',
        '-ac','1','-ar','16000','-f','f32le','-']),dtype='<f4')


def review_archive(folder):
    """Publish a CRC-checked archive without interrupted encoder staging files."""
    folder=Path(folder)
    target=folder.parent/(folder.name+'.zip')
    temporary=target.with_name('.approval-'+uuid.uuid4().hex+'.zip')
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for path in sorted(folder.rglob('*')):
                if (not path.is_file() or any(part.startswith('.') for part in path.relative_to(folder).parts)
                        or path.name.endswith('.graded.mp4')):
                    continue
                before=digest(path)
                z.write(path,str(Path(folder.name)/path.relative_to(folder)))
                if digest(path)!=before:raise RuntimeError('Artifact changed during packaging: '+path.name)
        with zipfile.ZipFile(temporary) as z:
            if z.testzip() is not None:raise ValueError('Approval ZIP integrity failed')
        temporary.replace(target)
        return str(target.resolve())
    finally:
        temporary.unlink(missing_ok=True)


def verify(path,audio, *, native, static_cast=False):
    probe=probe_media(path,'ffprobe')
    v=next(s for s in probe['streams'] if s['codec_type']=='video')
    a=next(s for s in probe['streams'] if s['codec_type']=='audio')
    command(['ffmpeg','-v','error','-xerror','-i',str(path),'-map','0:v:0','-map','0:a:0','-f','null','-'])
    source,decoded=pcm(audio),pcm(path);n=min(len(source),len(decoded))
    correlation=float(np.corrcoef(source[:n],decoded[:n])[0,1])
    if not np.isfinite(correlation) or correlation<.97:raise ValueError('Source soundtrack correlation failed')
    duration=len(source)/16000
    if abs(float(v['duration'])-duration)>.1 or abs(float(a['duration'])-duration)>.1:raise ValueError('Full-song duration failed')
    if v['codec_name']!='h264' or a['codec_name']!='aac' or int(v['width'])<1280 or int(v['height'])<720:
        raise ValueError('Required codec/resolution failed')
    readability=verify_mp4(path,static_cast=static_cast)
    return dict(file=path.name,sha256=digest(path),bytes=path.stat().st_size,native_xlights=native,
        dimensions=[v['width'],v['height']],fps=v['avg_frame_rate'],frames=v.get('nb_frames'),
        video_duration=float(v['duration']),audio_duration=float(a['duration']),
        full_decode=True,original_soundtrack_correlation=correlation,
        audio_start_time=float(a.get('start_time',0)),video_start_time=float(v.get('start_time',0)),
        readability=readability)


def label(source,target,title, *, gamma=None):
    # Native pixels receive only an explicitly recorded tone curve and caption.
    temporary=target.with_name('.label-'+uuid.uuid4().hex+'.mp4')
    if gamma is not None and (not math.isfinite(gamma) or not 1 <= gamma <= 3):
        raise ValueError('Presentation gamma must be finite in1..3')
    tone=('lutrgb='+':'.join(f"{c}='255*pow(val/255,{1/gamma})'" for c in ('r','g','b'))+',') if gamma is not None else ''
    try:
        command(['ffmpeg','-nostdin','-v','error','-y','-threads','2','-filter_threads','2','-i',str(source),'-vf',
            tone+"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='"+title+"':x=20:y=18:fontsize=23:fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=8",
            '-c:v','libx264','-preset','fast','-crf','19','-threads','2','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(temporary)])
        probe_media(temporary,'ffprobe')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def comparison(paths,labels,target,audio,cols,rows, *, duration=34.88):
    if not math.isfinite(duration) or duration<=0:raise ValueError('Positive source comparison duration required')
    width,height=(1280,540) if len(paths)==12 else (1280,720)
    args=['ffmpeg','-v','error','-y','-filter_complex_threads','2']
    for path in paths:args+=['-threads','1','-i',str(path)]
    args+=['-i',str(audio)]
    filters=[]
    for i,path in enumerate(paths):
        filters.append(f'[{i}:v]setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black[p{i}]')
    positions='|'.join(f'{(i%cols)*width}_{(i//cols)*height}' for i in range(len(paths)))
    filters.append(''.join(f'[p{i}]' for i in range(len(paths)))+f'xstack=inputs={len(paths)}:layout={positions}:fill=black[v]')
    temporary=target.with_name('.comparison-'+uuid.uuid4().hex+'.mp4')
    args+=['-filter_complex',';'.join(filters),'-map','[v]','-map',f'{len(paths)}:a:0',
           '-t',str(duration),'-c:v','libx264','-preset','fast','-crf','20','-threads','4',
           '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(temporary)]
    try:
        command(args)
        probe_media(temporary,'ffprobe')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def render(layouts,output,xlights, *, source_commit=None, audio_name='Phoneme_Test_Hook.mp3',
           expected_sha256=EXPECTED_SHA256, bundle_name='Helix_Final_Beta_Approval_Bundle', presentation_gamma=None):
    layouts,output=Path(layouts),Path(output)
    bundle=output/bundle_name
    for folder in ('00_START_HERE','01_Individual_Layouts','02_Comparison_Videos','03_Band_Features',
                   '04_XLights_Sequences/Matching_XSQ_Files','04_XLights_Sequences/Layouts',
                   '04_XLights_Sequences/Models','05_Verification'):(bundle/folder).mkdir(parents=True,exist_ok=True)
    manifest=json.loads((layouts/'Layout_Manifest.json').read_text())
    reports=[];failures=[];movies={};raw_reports=[]
    audio=layouts/('01_'+manifest[0]['name'])/'media'/audio_name
    if digest(audio)!=expected_sha256 or any(i['source_audio_sha256']!=expected_sha256 for i in manifest):
        raise ValueError('Collection source checksum mismatch')
    duration=len(pcm(audio))/16000
    for item in manifest:
        folder=layouts/f"{item['number']:02}_{item['name']}"
        print('RENDERING',item['number'],item['name'],flush=True)
        try:
            current=json.loads((folder/'run_manifest.json').read_text())
            native=current.get('native_preview',{})
            # Reuse only an exact matching successful native receipt.
            if not (native.get('status')=='success' and Path(native.get('mp4','')).is_file()
                    and native.get('mp4_sha256')==digest(Path(native['mp4']))
                    and native.get('xsq_sha256')==digest(folder/item['xsq'])
                    and native.get('layout_sha256')==digest(folder/'xlights_rgbeffects.xml')):
                native=preview_run(folder,xsq=folder/item['xsq'],audio=folder/'media'/audio_name,xlights=xlights)
            if native['status']!='success':raise ValueError('; '.join(native['warnings']))
            target=bundle/'01_Individual_Layouts'/f"{item['number']:02}_{item['name']}.mp4"
            raw_readability=verify_mp4(Path(native['mp4']),static_cast=item['number']==7)
            raw_reports.append(dict(number=item['number'],mp4_sha256=digest(Path(native['mp4'])),readability=raw_readability))
            gamma=(2.6 if item['number']==3 else presentation_gamma) if presentation_gamma is not None else None
            label(Path(native['mp4']),target,f"{item['number']:02} - {item['name'].replace('_',' ')} | native xLights"+
                  (f' | display gamma{gamma}' if gamma is not None else ''),gamma=gamma)
            report=verify(target,audio,native=True,static_cast=item['number']==7)
            report.update(presentation_gamma=gamma,native_before_presentation_sha256=digest(Path(native['mp4'])),
                          geometry_or_event_timing_changed=False)
            reports.append(report);movies[item['number']]=target
            item.update(native_render_status='complete',mp4=target.name,readability_passed=report['readability']['passed'])
            if not report['readability']['passed']:failures.append(dict(layout=item['number'],reason='Readability/motion acceptance failed',measurements=report['readability']))
            print('VERIFIED',target.name,report['readability']['passed'],flush=True)
        except Exception as exc:
            item.update(native_render_status='failed',error=str(exc))
            failures.append(dict(layout=item['number'],reason=str(exc)))
            print('FAILED',item['number'],str(exc),flush=True)
        (bundle/'05_Verification/MP4_Verification_Report.json').write_text(json.dumps(dict(complete=False,videos=reports,failures=failures),indent=2)+'\n')
        (bundle/'05_Verification/Layout_Manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        sequence_folder=bundle/'04_XLights_Sequences/Layouts'/f"{item['number']:02}_{item['name']}"
        shutil.copytree(folder,sequence_folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('native-preview-*','Backup','_media','*.mp4','*pre2026*'))
        shutil.copyfile(folder/item['xsq'],bundle/'04_XLights_Sequences/Matching_XSQ_Files'/f"{item['number']:02}_{item['xsq']}")
    if len(movies)==12:
        groups=[('Helix_6_Layout_Comparison.mp4',[1,3,4,6,9,12],3,2),
                ('Helix_12_Layout_Comparison.mp4',list(range(1,13)),3,4),
                ('Helix_Band_Integration_Comparison.mp4',[7,8,12],3,1)]
        for name,indexes,cols,rows in groups:
            print('COMPARISON',name,flush=True)
            target=bundle/'02_Comparison_Videos'/name
            comparison([movies[i] for i in indexes],[manifest[i-1]['name'] for i in indexes],target,audio,cols,rows,duration=duration)
            reports.append(verify(target,audio,native=False))
        closeup=bundle/'03_Band_Features/Helix_Final_Snowman_Band_Closeup.mp4'
        shutil.copyfile(movies[7],closeup);reports.append(verify(closeup,audio,native=True))
        feature=bundle/'03_Band_Features/Vocal_And_Instrument_Verification.mp4'
        label(movies[7],feature,'Source-timed native surface candidate - continuous mesh motion unverified')
        reports.append(verify(feature,audio,native=True))
    if 7 in movies:
        vocal=layouts/'07_Snowman_Band_Stage/vocal_lane_diagnostic.json'
        shutil.copyfile(vocal,bundle/'05_Verification/Vocal_Verification_Report.json')
    # Keep acceptance honest even if every file decodes successfully.
    status=dict(schema='helix.final_approval_bundle.v1',complete=False,public_beta_ready=False,
        mp4_count=len(reports),native_individuals=len(movies),source_audio_sha256=expected_sha256,
        technical_failures=failures,owner_visual_approval='pending',
        limitations=['Native surfaces and two-pose light banks are not continuous solid meshes',
                     'Preserved canonical drummer uses planar original artwork',
                     'Independent vocal identities and instrument source separation remain estimates',
                     'Hardware installation, Windows/Android current candidate and licensing gates remain open',
                     'Helix strands have independent native lighting; geometric rotation is not implemented'])
    (bundle/'05_Verification/MP4_Verification_Report.json').write_text(json.dumps(dict(**status,videos=reports),indent=2)+'\n')
    (bundle/'05_Verification/Before_Presentation_Grading.json').write_text(json.dumps(raw_reports,indent=2)+'\n')
    (bundle/'05_Verification/Source_Commit.txt').write_text((source_commit or 'uncommitted candidate; see module hashes')+'\n')
    start=bundle/'00_START_HERE'
    (start/'README.md').write_text('# Helix native video review candidate — INCOMPLETE\n\n'
        'Audio in. Lights out.\n\nAll display footage is freshly rendered by native xLights2026.18 from the checksum-verified owner sampler recording '+audio.name+'. '
        'Comparison videos synchronize the same musical time and use one soundtrack. Source video is20fps, not30fps.\n\n'
        '**This is an incomplete review candidate, not an approved beta or a claim that the final solid3D visuals have passed.** '
        'Pixel surface sampling and two-pose light banks differ from continuous solid-mesh animation. The original drummer artwork is planar. '
        'Failed readability gates remain recorded in05_Verification; no threshold was weakened.\n\n'
        'The matching standalone XSQ copies are indexes; open each full layout folder under04_XLights_Sequences/Layouts to retain relative media/assets.\n')
    (start/'APPROVAL_CHECKLIST.md').write_text('# Approval remains pending\n\n'
        '- [ ] Canonical visual likeness and all six performers\n- [ ] Readable faces, strings, keys and drum kit\n'
        '- [ ] Owner confirmation of retained backup singer behavior\n- [ ] All readability/motion failures repaired\n'
        '- [ ] Continuous contact/motion artistic review\n- [ ] Platform and final release gates\n\nNo public beta or PR merge has been performed.\n')
    (start/'VIDEO_INDEX.md').write_text('# Video index\n\n'+''.join(f"- {r['file']} — {r['video_duration']:.3f}s, {r['dimensions'][0]}×{r['dimensions'][1]}, decode passed\n" for r in reports))
    if presentation_gamma is not None:
        with (start/'README.md').open('a') as stream:
            stream.write(f'\nNative footage has an explicit display gamma{presentation_gamma} tone curve (gamma2.6 for sparseAC256), preserving black/highlight endpoints. '
                'No geometry, source events, frame times or soundtrack changed. Raw native readability failures remain in Before_Presentation_Grading.json; '
                'this display presentation does not pass unresolved source/visual release gates.\n')
    models=bundle/'04_XLights_Sequences/Models'
    for path in (layouts/'07_Snowman_Band_Stage/models').glob('*.xmodel'):shutil.copyfile(path,models/path.name)
    # Include source module hashes so an uncommitted render cannot masquerade as
    # an older clean commit. The committed checkpoint can be added separately.
    root=Path(__file__).resolve().parents[1]
    modules=['models/canonical_native_band.py','models/final_band_native.py','models/approval_layouts.py',
             'tools/build_approval_collection.py','tools/canonical_band_cues.py','tools/render_approval_collection.py',
             'tools/phoneme_vocal_export.py']
    (bundle/'05_Verification/Source_Module_Hashes.json').write_text(json.dumps({n:digest(root/n) for n in modules},indent=2)+'\n')
    with (bundle/'05_Verification/SHA256SUMS').open('w') as sums:
        for p in sorted(bundle.rglob('*')):
            if p.is_file() and p.name!='SHA256SUMS':sums.write(digest(p)+'  '+str(p.relative_to(bundle))+'\n')
    archive=review_archive(bundle)
    print(json.dumps(dict(archive=archive,**status),indent=2),flush=True)
    return status


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('layouts',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--xlights',required=True);p.add_argument('--source-commit')
    p.add_argument('--audio-name',default='Phoneme_Test_Hook.mp3')
    p.add_argument('--expected-sha256',default=EXPECTED_SHA256)
    p.add_argument('--bundle-name',default='Helix_Final_Beta_Approval_Bundle')
    p.add_argument('--presentation-gamma',type=float)
    a=p.parse_args();render(a.layouts,a.output,a.xlights,source_commit=a.source_commit,
        audio_name=a.audio_name,expected_sha256=a.expected_sha256,bundle_name=a.bundle_name,presentation_gamma=a.presentation_gamma)
