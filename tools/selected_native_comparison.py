"""Native comparison of one SHA-verified source and its actual master outputs."""
from pathlib import Path
import argparse,gzip,hashlib,json,math,shutil,subprocess,xml.etree.ElementTree as ET
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont
from tools.phoneme_source import digest

EVIDENCE=Path(__file__).resolve().parents[1]/'evidence/beta_completion/selected_native_comparison_20261105'


def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def stage(root):
    root=Path(root);source=root/'source';(source/'sequence').mkdir(parents=True,exist_ok=True);(source/'media').mkdir(exist_ok=True)
    receipt=json.loads((EVIDENCE/'source_manifest.json').read_text())
    original=root/'Helix_Motion_original.mp3'
    if digest(original)!=receipt['original_sha256']:raise ValueError('Foreign original Drive audio')
    audio=source/'media'/receipt['audio_name']
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-ss','39','-i',str(original),'-t','36','-ar','48000','-ac','2','-c:a','pcm_s16le',str(audio)],check=True)
    wave,rate=sf.read(audio,dtype='int16',always_2d=True)
    pcm=hashlib.sha256(wave.astype('<i2').tobytes()).hexdigest()
    if pcm!=receipt['pcm_s16le_sha256'] or rate!=48000 or len(wave)!=36*48000:raise ValueError('Master/source PCM mismatch')
    receipt['render_audio_sha256']=digest(audio)
    receipt['audio_container_note']='PCM hash matches the exact master input; FFmpeg WAV metadata may differ across runtimes'
    for p in EVIDENCE.glob('*.gz'):
        if not p.name.endswith('.report.json.gz'):(source/'sequence'/p.name[:-3]).write_bytes(gzip.decompress(p.read_bytes()))
    save(source/'run_manifest.json',receipt)
    plan=json.loads(next((source/'sequence').glob('*.snowman_band.json')).read_text())
    # This particular production result has no supported face activation.
    # Do not drive mouths with instrumental energy or copy a mixed bus twice.
    if plan['cues']['lead_singer'] or plan['cues']['background_face_activations']:raise ValueError('Review source face cues before adapting another production result')
    fixture=root/'vocals';fixture.mkdir(exist_ok=True)
    np.savez_compressed(fixture/'acoustic_vocal_clocks.npz',estimated_lead_energy=np.zeros(3600,'f4'),estimated_lead_shapes=np.zeros(3600,'i1'),estimated_backing_energy=np.zeros(3600,'f4'),estimated_backing_shapes=np.zeros(3600,'i1'))
    save(fixture/'diagnostic.json',dict(audio_sha256=digest(audio),clock_sha256=digest(fixture/'acoustic_vocal_clocks.npz'),clock_hop_seconds=.01,
         method='No supported singing-face events in this actual Helix production result; both mouths remain REST',
         effect_source_method='helix_production_no_supported_face_activity',independent_backing_verified=False,
         tracks={k:dict(sha256=digest(audio),evidence='mixed original, no independent vocal source') for k in ('estimated_lead','estimated_backing')}))
    from tools.build_current_comparison import build
    items=build(source,fixture,root/'layouts')
    # The AC panel uses the actual master XSQ, without replacement choreography.
    folder=root/'layouts/01';xsq=next((source/'sequence').glob('*.xsq'))
    tree=ET.parse(xsq);tree.find('head/mediaFile').text='media/'+audio.name
    tree.write(folder/'Performance.xsq',encoding='utf-8',xml_declaration=True)
    from tools.prepare_drive_ac_preview import prepare
    ac=prepare(Path(__file__).resolve().parents[1]/'xlights_rgbeffects.xml',folder/'Performance.xsq',folder)
    save(folder/'Actual_Master_Provenance.json',dict(master_xsq_sha256=digest(xsq),render_xsq_sha256=digest(folder/'Performance.xsq'),
          effects=sum(1 for _ in tree.iter('Effect')),only_media_path_changed=True,source=receipt))
    save(root/'BUILD.json',dict(source=receipt,layouts=items,ac_mapping=ac,supported_singer_activity=False))
    return items


def render(root,xlights):
    from tools.native_preview import preview_run
    from tools.verify_showcase_luma import verify_mp4
    root=Path(root);items=json.loads((root/'layouts/Layout_Manifest.json').read_text());results=[]
    for item in items:
        folder=root/'layouts'/f"{item['number']:02}"
        result=preview_run(folder,xsq=folder/'Performance.xsq',audio=folder/'media'/item['audio_name'],xlights=xlights,port=49913)
        if result['status']!='success':raise RuntimeError(str(result['warnings']))
        readability=verify_mp4(Path(result['mp4']),static_cast=item['number']==2)
        if not all(readability['checks'][key] for key in ('visible_stage_width','visible_stage_height','median_stage_luminance')):
            # One bounded preview-only correction. The complete original
            # native movie, failed gate and layout are retained as evidence.
            save(folder/'FIRST_NATIVE_READABILITY.json',readability)
            save(folder/'FIRST_NATIVE_RECEIPT.json',result)
            layout_path=folder/'xlights_rgbeffects.xml'
            shutil.copyfile(layout_path,folder/'layout_before_visibility_fit.xml')
            tree=ET.parse(layout_path)
            for model in tree.findall('./models/model'):
                old=float(model.get('PixelSize','8'))
                model.set('PixelSize',str(round(min(64 if item['number']==1 else 32,old*1.4))))
            for camera in tree.findall('./Viewpoints/*'):
                if camera.get('distance'):camera.set('distance',str(float(camera.get('distance'))*.8))
            tree.write(layout_path,encoding='utf-8',xml_declaration=True)
            result=preview_run(folder,xsq=folder/'Performance.xsq',audio=folder/'media'/item['audio_name'],xlights=xlights,port=49913)
            if result['status']!='success':raise RuntimeError(str(result['warnings']))
            readability=verify_mp4(Path(result['mp4']),static_cast=item['number']==2)
        save(folder/'NATIVE_READABILITY.json',readability)
        results.append(dict(number=item['number'],name=item['name'],movie=result['mp4'],native=result,readability=readability))
        save(root/'RENDER_PROGRESS.json',results)
        print('SELECTED_NATIVE_PANEL',item['number'],item['name'],readability['measurements'],flush=True)
    return results


def presentation(root):
    """Uniform display transfer only; never synthesize a pixel or musical event."""
    root=Path(root);results=json.loads((root/'RENDER_PROGRESS.json').read_text());out=root/'presentation';out.mkdir(exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    from tools.verify_showcase_luma import verify_mp4
    for r in results:
        label=Image.new('RGB',(480,30),'#101c2b');ImageDraw.Draw(label).text((9,5),f"{r['number']:02}  {r['name']}",font=small,fill='#e4eef8')
        label.save(out/f"label_{r['number']:02}.png")
        # Every panel is actual native xLights footage. Gamma is an explicit
        # common display transfer, with no bloom, extra patterns or retiming.
        path=out/f"panel_{r['number']:02}.mp4"
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-threads','2','-filter_threads','2','-i',r['movie'],
            '-vf','eq=gamma=1.8,scale=480:270:flags=lanczos','-an','-c:v','libx264','-preset','fast','-crf','17','-threads','2','-pix_fmt','yuv420p',str(path)],check=True)
        r['presentation']=dict(movie=str(path),display_gamma=1.8,readability=verify_mp4(path,static_cast=r['number']==2))
    save(root/'PANEL_PRESENTATION.json',results)
    background=Image.new('RGB',(1920,1080),'#07111f');draw=ImageDraw.Draw(background)
    draw.text((18,6),'HELIX | Audio in. Lights out. | Real audio / native xLights / 16 layouts',font=font,fill='#edf6ff')
    draw.text((18,1055),'Helix Motion 00:39–01:15 | Same source clock in every panel | Instrumental preview: no supported singer events',font=small,fill='#b9cada')
    background.save(out/'background.png')
    # Render four bounded row streams, then stack them. Avoid opening sixteen
    # full-HD decoders together and keep composition memory predictable.
    for row in range(4):
        cmd=['ffmpeg','-nostdin','-v','error','-y','-filter_complex_threads','2']
        for r in results[row*4:row*4+4]:cmd+=['-threads','1','-i',str(out/f"panel_{r['number']:02}.mp4")]
        for r in results[row*4:row*4+4]:cmd+=['-loop','1','-i',str(out/f"label_{r['number']:02}.png")]
        filters=[]
        for col in range(4):filters.append(f'[{col}:v]scale=480:225:force_original_aspect_ratio=decrease,pad=480:225:(ow-iw)/2:(oh-ih)/2:color=0x07111f[vid{col}];[{col+4}:v][vid{col}]vstack=inputs=2[cell{col}]')
        filters.append('[cell0][cell1][cell2][cell3]hstack=inputs=4[row]')
        cmd+=['-filter_complex',';'.join(filters),'-map','[row]','-t','36','-r','30','-c:v','libx264','-preset','fast','-crf','18','-threads','2','-pix_fmt','yuv420p',str(out/f'row_{row}.mp4')]
        subprocess.run(cmd,check=True)
    cmd=['ffmpeg','-nostdin','-v','error','-y','-filter_complex_threads','2']
    for row in range(4):cmd+=['-threads','1','-i',str(out/f'row_{row}.mp4')]
    cmd+=['-loop','1','-i',str(out/'background.png'),'-i',str(root/'source/media/Helix_Motion_39_75.wav')]
    filters='[0:v][1:v][2:v][3:v]vstack=inputs=4[grid];[4:v][grid]overlay=0:30:shortest=1[out]'
    movie=root/'HELIX_MOTION_16_LAYOUT_NATIVE_COMPARISON.mp4'
    cmd+=['-filter_complex',filters,'-map','[out]','-map','5:a:0','-t','36','-r','30','-c:v','libx264','-preset','fast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-movflags','+faststart',str(movie)]
    subprocess.run(cmd,check=True)
    from tools.verify_recovery_media import verify
    audio=root/'source/media/Helix_Motion_39_75.wav'
    report=verify(movie,audio,digest(audio))
    report.update(panels=16,native_xlights_panels=16,grid=[4,4],display_gamma=1.8,owner_approved=False,
                  supported_singer_activity=False,native_raw_readability_passed=all(r['readability']['passed'] for r in results),
                  presentation_readability_passed=all(r['presentation']['readability']['passed'] for r in results),
                  full_beta_acceptance=False)
    save(root/'VIDEO_VERIFICATION.json',report)
    # Contact sheets are taken from the final encoded movie, not mocked scenes.
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(movie),'-vf','fps=1/12,scale=960:540,tile=1x3','-frames:v','1',str(root/'FINAL_CONTACT_SHEET.jpg')],check=True)
    print(json.dumps(report,indent=2),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['stage','render','compose']);p.add_argument('root',type=Path);p.add_argument('--xlights')
    a=p.parse_args()
    if a.mode=='stage':stage(a.root)
    elif a.mode=='render':render(a.root,a.xlights)
    else:presentation(a.root)
