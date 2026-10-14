"""Download exact successful workflow artifacts and assemble a no-music beta."""
import hashlib, io, json, os, shutil, subprocess, time, urllib.request, zipfile
from pathlib import Path

REPO='ryankorkowski-boop/helix-sequencer'
SOURCE='f38f489d1efed08e2e5007835a07213d00633c7a'
RUNS={'windows':38612866472,'android':38612866317,'native':38612866467,
      'unit_integration':38612866417,'beta':38612868376,'layout':38612866440}
API='https://api.github.com/repos/'+REPO
TOKEN=os.environ['GH_TOKEN']
def get(path, binary=False):
    req=urllib.request.Request(API+path,headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.urlopen(req,timeout=120) as r:data=r.read()
    return data if binary else json.loads(data)
def digest(b):return hashlib.sha256(b).hexdigest()
def pathsha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    out=Path('release-output');out.mkdir(exist_ok=True)
    statuses={}
    for attempt in range(160):
        statuses={k:get('/actions/runs/'+str(v)) for k,v in RUNS.items()}
        assert all(v['head_sha']==SOURCE and v['event']=='push' for v in statuses.values())
        failed={k:v['conclusion'] for k,v in statuses.items() if v['status']=='completed' and v['conclusion']!='success'}
        if failed:raise RuntimeError('Required verification failed: '+str(failed))
        pending=[k for k,v in statuses.items() if v['status']!='completed']
        print('Awaiting',pending,flush=True)
        if not pending:break
        time.sleep(15)
    else:raise TimeoutError('Exact-source gates did not complete')
    artifacts={};archives={}
    for key,names in {'windows':['Helix-Windows-Portable'],
                      'android':['Helix-Android-stability-api-30','Helix-Android-stability-api-36'],
                      'native':['Helix-Final-Completion-Native-Proof']}.items():
        available=get('/actions/runs/'+str(RUNS[key])+'/artifacts')['artifacts']
        for name in names:
            a=next(a for a in available if a['name']==name and not a['expired'])
            data=get('/actions/artifacts/'+str(a['id'])+'/zip',True)
            assert a.get('digest')=='sha256:'+digest(data),(name,a.get('digest'))
            z=zipfile.ZipFile(io.BytesIO(data));assert z.testzip() is None
            artifacts[name]={'id':a['id'],'bytes':len(data),'sha256':digest(data),'run':RUNS[key]}
            archives[name]=z
    folder=out/'Helix_Beta_v1.0_Installers';folder.mkdir(exist_ok=True)
    for d in ('Windows','Android','Validation'):(folder/d).mkdir(exist_ok=True)
    wz=archives['Helix-Windows-Portable'];portable=wz.read('Helix-Windows-Portable.zip')
    with zipfile.ZipFile(io.BytesIO(portable)) as z:
        assert z.testzip() is None
        assert not any(n.lower().endswith(('.mp3','.wav','.mp4')) for n in z.namelist())
        for n in ('Helix/Helix.exe','Helix/HelixCLI.exe','Helix/LICENSE','Helix/VALIDATION.json'):assert n in z.namelist()
        assert z.read('Helix/LICENSE').decode().replace('\r\n','\n')==Path('source/LICENSE').read_text()
        (folder/'Validation/windows-verification.json').write_bytes(z.read('Helix/VALIDATION.json'))
    (folder/'Windows/Helix-Windows-Portable.zip').write_bytes(portable)
    (out/'Helix-Windows-Portable.zip').write_bytes(portable)
    android_proofs={}
    for api in (30,36):
        z=archives['Helix-Android-stability-api-'+str(api)]
        apk=z.read(next(n for n in z.namelist() if n.endswith('outputs/apk/debug/app-debug.apk')))
        with zipfile.ZipFile(io.BytesIO(apk)) as a:
            assert a.testzip() is None
            with zipfile.ZipFile(io.BytesIO(a.read(next(n for n in a.namelist() if n.endswith('helix-engine.zip'))))) as engine:
                assert engine.testzip() is None
                assert json.loads(engine.read('android-engine-manifest.json'))['commit']==SOURCE
                assert engine.read('LICENSE')==Path('source/LICENSE').read_bytes()
                assert not any(n.lower().endswith(('.mp3','.wav','.mp4')) for n in engine.namelist())
        proof=z.read(next(n for n in z.namelist() if n.endswith('decoded-verification.json')))
        decoded=json.loads(proof);assert len(decoded)==4
        assert all(p['audio_correlation']>.97 and abs(p['audio_offset_ms'])<5 for p in decoded)
        (folder/f'Validation/android-api-{api}-decoded-verification.json').write_bytes(proof)
        cert=z.read(next(n for n in z.namelist() if n.endswith('signing-certificate.txt')))
        (folder/f'Validation/android-api-{api}-signing-certificate.txt').write_bytes(cert)
        android_proofs[str(api)]={'apk_sha256':digest(apk),'api':api,'debug_signed':True,'decoded':decoded}
        if api==30:
            (folder/'Android/Helix-Beta-v1.0.apk').write_bytes(apk)
            (out/'Helix-Beta-v1.0.apk').write_bytes(apk)
    nz=archives['Helix-Final-Completion-Native-Proof']
    native=json.loads(nz.read('VALIDATION.json'));assert native['source_commit']==SOURCE
    assert native['layout_native_import_verified'] and native['rung_output_verified']
    assert native['final_band_output']['native_performers_verified']==12
    assert native['six_real_sampler_layouts_verified']==6
    # Native package contains light cues and explicitly synthetic diagnostics;
    # never the private original sampler recording or sampler movies.
    with zipfile.ZipFile(out/'Helix_Beta_v1.0_Native_Verification.zip','w',zipfile.ZIP_DEFLATED,6) as z:
        for n in nz.namelist():
            if n.endswith('/'):continue
            if n.lower().endswith(('.mp3','.wav','.mp4')):
                assert '/Physical_Drummer_Diagnostic/' in '/'+n and ('Diagnostic_Only.wav' in n or 'Native_Physical_Channel_Diagnostic.mp4' in n),n
            z.writestr(n,nz.read(n))
    (folder/'Validation/native-verification.json').write_text(json.dumps(native,indent=2)+'\n')
    for n in ('LICENSE','NOTICE','THIRD_PARTY_LICENSES.md','COMMERCIAL_LICENSING.md','WELCOME_TO_HELIX.md','INSTALL_AND_TROUBLESHOOT.md'):
        shutil.copyfile(Path('source')/n,folder/n)
    shutil.copytree('source/LICENSES',folder/'LICENSES')
    shutil.copyfile('transport/BETA_RELEASE_NOTES.md',folder/'KNOWN_LIMITATIONS.md')
    files={str(p.relative_to(folder)):dict(bytes=p.stat().st_size,sha256=pathsha(p)) for p in sorted(folder.rglob('*')) if p.is_file()}
    manifest={'release':'HELIX BETA RELEASE v1.0','prerelease':True,'source_commit':SOURCE,
        'source_tree':'3db7569c2ee13887c4c00b2d25fdc43b9b4c9c5b','branch':'codex/beta-final-completion-20261014',
        'pull_request':147,'default_branch_merged':False,'run_ids':RUNS,'artifacts':artifacts,
        'android':android_proofs,'distributed_apk_tested_on_api':30,
        'api_36_same_source_companion_build_tested':True,'physical_phone_verified':False,
        'licensed_full_song_showcase_complete':False,'music_redistribution_cleared':False,
        'native_xlights':'2026.18','files':files}
    (folder/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    files['RELEASE_MANIFEST.json']={'bytes':(folder/'RELEASE_MANIFEST.json').stat().st_size,'sha256':pathsha(folder/'RELEASE_MANIFEST.json')}
    (folder/'SHA256SUMS.txt').write_text(''.join(f"{m['sha256']}  {n}\n" for n,m in files.items()))
    archive=out/'Helix_Beta_v1.0_Installers.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(folder).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,m in files.items():assert digest(z.read(n))==m['sha256']
    sums={p.name:dict(bytes=p.stat().st_size,sha256=pathsha(p)) for p in sorted(out.glob('*')) if p.is_file()}
    (out/'SHA256SUMS.txt').write_text(''.join(f"{m['sha256']}  {n}\n" for n,m in sums.items()))
    (out/'RELEASE_MANIFEST.json').write_text(json.dumps({**manifest,'assets':sums},indent=2)+'\n')
    print(json.dumps(sums,indent=2),flush=True)
if __name__=='__main__':main()
