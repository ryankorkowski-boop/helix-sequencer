"""Rebuild exact-source sampler deliverables and the isolated issue132 experiment."""
from __future__ import annotations
import hashlib,json,math,os,shutil,subprocess,sys,zipfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path.cwd();OUT=ROOT/'outputs/Prior_Sampler_Review'
EXPECTED='0fc2ab5dfee87d4af3e2ab326f76c7ee9cb3a5a893644487d2e7350a48cefafb'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args,**kwargs):subprocess.run(list(map(str,args)),check=True,**kwargs)

def restore():
    private=Path(os.environ['RUNNER_TEMP'])/'helix_sampler_private_inputs'
    OUT.mkdir(parents=True,exist_ok=True);audio=OUT/'Helix_Six_Song_Sampler.wav'
    with zipfile.ZipFile(private/'sampler.zip') as z:
        assert z.testzip() is None
        names=[n for n in z.namelist() if Path(n).name=='Helix_Six_Song_Sampler.wav']
        assert len(names)==1
        audio.write_bytes(z.read(names[0]))
    assert sha(audio)==EXPECTED
    kit=private/'kit';kit.mkdir(exist_ok=True)
    with zipfile.ZipFile(private/'kit.zip') as z:
        assert z.testzip() is None
        for name in ('helix_256_rgb_showcase_runner.py','Helix_256_RGB_Showcase_HANDOFF.md'):
            matches=[n for n in z.namelist() if Path(n).name==name];assert len(matches)==1
            (kit/name).write_bytes(z.read(matches[0]))
    # The earlier layout/private package content is neither extracted nor published.
    (private/'sampler.zip').unlink();(private/'kit.zip').unlink()
    return audio,kit

def native():
    binary=Path(os.environ['RUNNER_TEMP'])/'xlights-native/squashfs-root/AppRun'
    for row in json.loads((OUT/'six_layouts/manifest.json').read_text())['runs']:
        folder=OUT/'six_layouts'/row['folder'];xsq=folder/row['xsq']
        with (folder/'native_render.log').open('w') as log:
            run([binary,'--headless','-q','-s',folder,'-od',folder,xsq],stdout=log,stderr=log,timeout=900)
        print('Native '+row['layout'],flush=True)
    from tools.export_refined_band_matrix import export
    movie=OUT/'Helix_Band_With_Singers_Same_Sampler.mp4'
    xsq=export(movie,OUT/'xlights/band_with_singers');shutil.copyfile(OUT/'Helix_Six_Song_Sampler.wav',xsq.parent/'media/soundtrack.wav')
    with (xsq.parent/'native_render.log').open('w') as log:
        run([binary,'--headless','-q','-s',xsq.parent,'-od',xsq.parent,xsq],stdout=log,stderr=log,timeout=900)
    import tools.audit_refined_band_native as audit
    audit.OUT=OUT;audit.audit()

def audit_movies():
    audio=OUT/'Helix_Six_Song_Sampler.wav'
    def pcm(p):
        return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-vn','-ar','8000','-ac','2','-f','f32le','-']),np.float32).reshape(-1,2)
    ref=pcm(audio);reports=[];encoded=[];decoded=OUT/'decoded';decoded.mkdir(exist_ok=True)
    for stem in ('Helix_Band_With_Singers_Same_Sampler','Helix_Six_Layouts_Same_Real_Sampler'):
        path=OUT/(stem+'.mp4');run(['ffmpeg','-v','error','-threads','1','-i',path,'-f','null','-'])
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height,nb_frames,duration,start_time:format=duration','-of','json',str(path)]))
        video=next(s for s in probe['streams'] if s['codec_type']=='video');assert int(video['nb_frames'])==3603
        assert abs(float(probe['format']['duration'])-180.15)<.01
        (OUT/(stem+'.probe.json')).write_text(json.dumps(probe,indent=2)+'\n')
        actual=pcm(path);windows=[]
        for start in (0,30,60,90,120,150,176):
            lo=start*8000;hi=min(len(ref),len(actual),lo+24000)
            corr=[float(np.corrcoef(ref[lo:hi,c],actual[lo:hi,c])[0,1]) for c in (0,1)]
            assert min(corr)>.995,(stem,start,corr);windows.append(dict(start_seconds=start,channel_correlations=corr))
        encoded.append(hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-acodec','copy','-f','adts','-'])).hexdigest())
        reports.append(dict(movie=path.name,sha256=sha(path),bytes=path.stat().st_size,windows=windows,minimum_correlation=min(min(w['channel_correlations']) for w in windows)))
        frames=[]
        for t in (0,2.5,14.5,29.95,30.1,41.9,59.95,75,89.95,120,150,161.4,173.8,179.9):
            p=decoded/(stem+f'_{t:06.2f}.jpg');run(['ffmpeg','-v','error','-y','-ss',t,'-i',path,'-frames:v','1',p]);frames.append(p)
        first=Image.open(frames[0]);h=round(640*first.height/first.width);rowh=h+30
        sheet=Image.new('RGB',(1280,math.ceil(len(frames)/2)*rowh),(7,14,24));draw=ImageDraw.Draw(sheet)
        for j,p in enumerate(frames):
            x=(j%2)*640;y=(j//2)*rowh;sheet.paste(Image.open(p).resize((640,h)),(x,y));draw.text((x+8,y+h+4),p.stem.rsplit('_',1)[-1]+'s',fill='white')
        sheet.save(OUT/(stem+'_Decoded_Review.jpg'))
    assert encoded[0]==encoded[1]
    for r in reports:r.update(AAC_bitstream_sha256=encoded[0],same_AAC_bitstream_in_both_movies=True)
    (OUT/'soundtrack_audit.json').write_text(json.dumps(reports,indent=2)+'\n')

def issue132(kit):
    temp=Path(os.environ['RUNNER_TEMP']);checkout=temp/'helix_issue132';destination=OUT/'issue132'
    run(['git','worktree','add','--detach',checkout,'1f66f5dfa09b3173f5cdfd33d28ab1b4421e11ad'])
    s=(kit/'helix_256_rgb_showcase_runner.py').read_text()
    s=s.replace('[sys.executable, "-m", "core.sequence_builder", "--profile", PROFILE, "--",','[sys.executable, str(repo / "main.py"), "--profile", PROFILE, "--",')
    s=s.replace('                ET.SubElement(effects, "Element", {"type": "model", "name": name})','                row = ET.SubElement(effects, "Element", {"type": "model", "name": name})\n                ET.SubElement(row, "EffectLayer")')
    marker='                cmd = [sys.executable, str(repo / "main.py")'
    start=s.index(marker)
    mapping="""                layout_models=ET.parse(layout).getroot().findall('./models/model')
                pools={k:[] for k in ('mega','arch','matrix','line','sphere','spinner','canes_single','stars','snowflakes')}
                for model in layout_models:
                    if 'rgb' not in model.get('StringType','').lower():continue
                    display=model.get('DisplayAs','').lower();model_name=model.get('name')
                    key='mega' if 'tree' in display else 'arch' if 'arch' in display else 'matrix' if 'matrix' in display else 'canes_single' if 'cane' in display else 'stars' if 'star' in display else 'sphere' if 'circle' in display else 'line'
                    pools[key].append(model_name)
                pools={k:v for k,v in pools.items() if v}
                pools['keyboard_lane']=list(dict.fromkeys(n for values in pools.values() for n in values))
                if 'mega' in pools:pools['mega_models']=pools['mega']
                if 'line' in pools:pools['line_models']=pools['line']
                mapping=out/label/'model_roles.json';mapping.write_text(json.dumps(pools,indent=2)+'\\n')
"""
    s=s[:start]+mapping+s[start:]
    s=s.replace('"--no-auto-timing-tracks", "--no-matrix-intelligence"]','"--no-auto-timing-tracks", "--no-matrix-intelligence", "--no-template-guidance", "--model-overrides-file", str(mapping)]')
    marker='                mp4 = xsq.with_suffix(".mp4")'
    s=s.replace(marker,marker+"""
                before=probe(ffprobe,mp4,repo)
                if before['duration']>15.1:
                    trimmed=mp4.with_name(mp4.stem+'.clipped.mp4')
                    run_cmd([ffmpeg,'-v','error','-y','-i',str(mp4),'-t','15','-map','0:v:0','-map','0:a:0','-c','copy','-movflags','+faststart',str(trimmed)],cwd=repo,logs=logs)
                    trimmed.replace(mp4)
""")
    script=kit/'helix_256_rgb_showcase_runner_executed.py';script.write_text(s)
    run([sys.executable,script,'--repo',checkout,'--output',destination])
    result=json.loads((destination/'verification_manifest.json').read_text());assert result['status'] in {'complete', 'rendered; manual visual frame inspection still required'} and not result['blocked']
    assert result['protected_sha256_before']==result['protected_sha256_after']
    assert subprocess.check_output(['git','status','--porcelain=v1'],cwd=checkout,text=True).strip()==''
    for name in ('Helix_Original_256_Montage.mp4','Helix_Experimental_256_Plus_RGB_Montage.mp4','Helix_256_Before_After_Comparison.mp4'):
        p=destination/name;run(['ffmpeg','-v','error','-i',p,'-f','null','-']);shutil.copyfile(p,OUT/name)
    shutil.copyfile(destination/'verification_manifest.json',OUT/'issue132_verification.json')
    shutil.copyfile(script,OUT/'issue132_executed_runner.py')

def package():
    paths=[]
    for directory in ('six_layouts','xlights'):
        paths.extend(p for p in (OUT/directory).rglob('*') if p.is_file() and p.suffix.lower() not in ('.log','.fseq') and '.prime_raw.' not in p.name and not p.name.endswith('_Showcase.xsq'))
    paths.extend(p for p in (OUT/'analysis').rglob('*') if p.is_file() and p.suffix in ('.json','.npz'))
    for pattern in ('*.verification.json','*.probe.json','*audit.json','*_Decoded_Review.jpg','native_verification.json','issue132_verification.json','issue132_executed_runner.py','Helix_Sampler_Recovery_Report.md'):
        paths.extend(OUT.glob(pattern))
    paths=sorted(set(paths));manifest={str(p.relative_to(OUT)):sha(p) for p in paths}
    (OUT/'portable_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');paths.append(OUT/'portable_manifest.json')
    archive=OUT/'Helix_Same_Sampler_XSQ_Layouts_And_Reports.zip';temporary=archive.with_suffix('.building.zip')
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in paths:z.write(p,p.relative_to(OUT),compress_type=zipfile.ZIP_STORED if p.suffix in ('.mp4','.png','.jpg') else zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
        entries=len(z.namelist());assert entries==len(set(z.namelist()))
    temporary.replace(archive)
    (OUT/'archive_verification.json').write_text(json.dumps(dict(file=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,entries=entries,CRC_verified=True,all_manifest_hashes_verified=True,portable_show_count=7,FSEQ_excluded_render_in_xlights=True),indent=2)+'\n')

def report():
    soundtrack=json.loads((OUT/'soundtrack_audit.json').read_text());bands=json.loads((OUT/'Helix_Band_With_Singers_Same_Sampler.verification.json').read_text())
    six=json.loads((OUT/'Helix_Six_Layouts_Same_Real_Sampler.verification.json').read_text())
    for row in six['layouts']:
        assert not row['control_activity'] and all(v>0 for v in row['active_model_frames'].values())
    (OUT/'Helix_Sampler_Recovery_Report.md').write_text(
        '# Helix exact-sampler review rebuild\n\n'
        'Source commit: '+os.environ['GITHUB_SHA']+'; isolated review branch, no primary merge.\n\n'
        'The local workspace went offline after verified renders; this independent Actions build restores only the same WAV from the authorized source package, with encrypted temporary access. No private source layout/package is published.\n\n'
        'Exact WAV SHA256: '+EXPECTED+'. Both movies have3603frames at20fps,180.15s video. Shared identical AAC stream: '+soundtrack[0]['AAC_bitstream_sha256']+'. Minimum sampled stereo correlation: '+str(min(r['minimum_correlation'] for r in soundtrack))+'. Both whole movies decode successfully.\n\n'
        'Six native xLights2026.18 shows use genuine Helix-generated effects and actual FSEQ channel bytes. All RGB models activate; controls staydark. Custom points are exact; stock projection geometry is illustrative. Seven portable XSQ show folders include local media/layouts/assets; the band show is Video on a384x216virtual matrix, not physical articulated performer parity.\n\n'
        'Source-bound Demucs/ADTOF and existing harmonic note-event logic drive the performers. Unknown tom identities abstain. Bass does not derive notes from kicks. Singers use screened word timings and authored duet casting, not verified voice separation or exact phone boundaries. Xylophone pitches are screened ringing estimates; identity/fundamental remain unverified. Detection predictions are not ground truth. Mallet evidence: '+json.dumps(bands['mallet_proof'])+'.\n\n'
        'Issue132 executes the real original-vs-added-RGB experiment in a clean detached1f66f5d checkout. Only external runner/template preparation changes: correct CLI invocation, empty EffectLayer discovery rows, explicit existing role mapping, and preview-only duration clipping. No manually fabricated effects or source modifications. The experiment movies are XSQ simulation, not native FSEQ equivalence.\n\n'
        'Current Windows GUI includes xLights/legacyLOR modes, corrected neon mapping, native FSEQ tools, guarded RGB controls and optional role mapping. Its final build and all seven CI workflows succeeded before this rebuild. Legacy loredit/hardware playback and optional source-only 3D/ML runtime are not bundled claims.\n')

def main():
    audio,kit=restore()
    run([sys.executable,'-m','demucs.separate','-n','htdemucs_6s','--device','cpu','--jobs','2','--out',OUT/'stems',audio])
    run([sys.executable,'-m','tools.transcribe_drummer_adtof',audio,'--analysis-audio',OUT/'stems/htdemucs_6s/Helix_Six_Song_Sampler/drums.wav','--output',OUT/'analysis/sampler/drums.json','--activations',OUT/'analysis/sampler/drum_activations.npy'])
    run([sys.executable,'-m','tools.analyze_prior_sampler',audio,'--output',OUT])
    run([sys.executable,'-m','tools.build_prior_sampler_layouts',audio,'--output',OUT/'six_layouts'])
    run([sys.executable,'-m','tools.render_prior_sampler_band',audio,'--output',OUT])
    native()
    run([sys.executable,'-m','tools.render_prior_sampler_comparison',audio,'--output',OUT])
    audit_movies();issue132(kit);report();package()

if __name__=='__main__':main()
