"""Package exact, already-tested platform artifacts; never package music."""
from pathlib import Path
import argparse, hashlib, io, json, shutil, zipfile

SOURCE='b7576e28008b938b0f4d832ae3f2688bde996444'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--notes',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    root=a.source;inputs=a.inputs;out=a.output;out.mkdir(parents=True,exist_ok=True)
    folder=out/'Helix_Beta_v1.0_Installers';folder.mkdir(exist_ok=True)
    for name in ('Windows','Android','Validation'):(folder/name).mkdir(exist_ok=True)
    android=inputs/'android.zip';windows=inputs/'windows.zip'
    assert sha(android)=='d4c0d6b7c43ba3f5529465567adf5c6c1c3f5120daabe03736c97abffcc323f4'
    assert sha(windows)=='fe1962066855bd6c80e9ec8d9e0232bde1137956657e3df2dca0ba73f8f8f70b'
    with zipfile.ZipFile(android) as z:
        assert z.testzip() is None
        apk=z.read('outputs/apk/debug/app-debug.apk')
        (folder/'Android/Helix-Beta-v1.0.apk').write_bytes(apk)
        for src,dst in [('device-proof/decoded/decoded-verification.json','android-decoded-verification.json'),('device-proof/signing-certificate.txt','android-signing-certificate.txt')]:
            (folder/'Validation'/dst).write_bytes(z.read(src))
        with zipfile.ZipFile(io.BytesIO(apk)) as az:
            assert az.testzip() is None
            name=next(n for n in az.namelist() if n.endswith('helix-engine.zip'))
            with zipfile.ZipFile(io.BytesIO(az.read(name))) as ez:
                assert json.loads(ez.read('android-engine-manifest.json'))['commit']==SOURCE
                assert ez.read('LICENSE')==(root/'LICENSE').read_bytes()
                assert not any(n.endswith(('.mp3','.wav','.mp4')) for n in ez.namelist())
    with zipfile.ZipFile(windows) as z:
        assert z.testzip() is None
        portable=z.read('Helix-Windows-Portable.zip')
        original=portable;rebuilt=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(original)) as old,zipfile.ZipFile(rebuilt,'w') as new:
            for entry in old.infolist():
                data=old.read(entry)
                if entry.filename in ('Helix/README.txt','Helix/_internal/WINDOWS_PORTABLE_README.txt'):
                    text=data.decode('utf-8').replace('\r\n','\n')
                    text=text.replace('Source, bug reports and releases:\nhttps://github.com/ryankorkowski-boop/helix-sequencer',
                                      'Community and support:\nhttps://Facebook.com/helixsequencer')
                    data=text.encode('utf-8')
                new.writestr(entry,data)
        portable=rebuilt.getvalue()
        with zipfile.ZipFile(io.BytesIO(original)) as old,zipfile.ZipFile(io.BytesIO(portable)) as new:
            for name in ('Helix/Helix.exe','Helix/HelixCLI.exe'):
                assert hashlib.sha256(old.read(name)).digest()==hashlib.sha256(new.read(name)).digest()
        (folder/'Windows/Helix-Windows-Portable.zip').write_bytes(portable)
        with zipfile.ZipFile(io.BytesIO(portable)) as wz:
            assert wz.testzip() is None
            (folder/'Validation/windows-verification.json').write_bytes(wz.read('Helix/VALIDATION.json'))
            assert wz.read('Helix/LICENSE').decode().replace('\r\n','\n')==(root/'LICENSE').read_text()
            assert not any(n.lower().endswith(('.mp3','.wav','.mp4')) for n in wz.namelist())
    for p in ['LICENSE','NOTICE','COMMERCIAL_LICENSING.md','WELCOME_TO_HELIX.md','INSTALL_AND_TROUBLESHOOT.md']:
        shutil.copy2(root/p,folder/p)
    shutil.copytree(root/'LICENSES',folder/'LICENSES',dirs_exist_ok=True)
    shutil.copyfile(a.notes,folder/'BETA_RELEASE_NOTES.md')
    files=dict(sorted((str(p.relative_to(folder)),dict(bytes=p.stat().st_size,sha256=sha(p))) for p in folder.rglob('*') if p.is_file()))
    manifest={'release':'Helix Beta Release v1.0','source_commit':SOURCE,'source_tree':'407732d71ab0f38390e7202a7698596e29ae8503','integration_commit':'cb6cff6bcf0227386a244b4bf2ea369ee9bab228','post_build_docs':'Community contact only; executable bytes unchanged','windows_run':38517654958,'android_run':38517654938,'native_run':__import__('os').environ.get('GITHUB_RUN_ID'),'android_artifact':11872937055,'windows_artifact':11872766332,'android_debug_signed':True,'local_tests_passed':1470,'tests_skipped':5,'skip_reason':'Fixed 2.wav sandbox input unavailable','physical_phone_verified':False,'files':files}
    (folder/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (folder/'SHA256SUMS.txt').write_text(''.join(f"{v['sha256']}  {k}\n" for k,v in sorted(files.items())))
    archive=out/'Helix_Beta_v1.0_Installers.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():z.writestr(zipfile.ZipInfo(p.relative_to(folder).as_posix(),(2026,10,14,0,0,0)),p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,m in files.items():assert hashlib.sha256(z.read(n)).hexdigest()==m['sha256']
        extracted=out/'installer-extraction-check';z.extractall(extracted)
        for n,m in files.items():assert sha(extracted/n)==m['sha256'],n
        shutil.rmtree(extracted)
    shutil.copyfile(folder/'Android/Helix-Beta-v1.0.apk',out/'Helix-Beta-v1.0.apk')
    sums={p.name:sha(p) for p in (archive,out/'Helix-Beta-v1.0.apk')}
    (out/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in sums.items()))
    print(json.dumps({'source_commit':SOURCE,'files':sums},indent=2))


if __name__=='__main__':main()
