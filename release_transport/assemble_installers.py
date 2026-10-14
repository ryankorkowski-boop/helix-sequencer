"""Package exact, already-tested platform artifacts; never package music."""
from pathlib import Path
import argparse, hashlib, io, json, shutil, zipfile

SOURCE='2b295284ae2c0d33fc40e8c3d54a9dbea0677fcc'


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
    assert sha(android)=='16f3f3b84ea41b21b2d3f9a0a61cd7dbfe69f234ae261f96b2698ba4dcf2dc89'
    assert sha(windows)=='b0bb35acb1d6a440c88629db4f7b1a57dc5c5655f312b8c5680ad72c2e37396a'
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
    manifest={'release':'Helix Beta Release v1.0','source_commit':SOURCE,'source_tree':'6e352ebab44cbdb1a9630cc4aab94e1a88838e9d','windows_run':38513380999,'android_run':38513381015,'native_run':38513916526,'android_artifact':11871054526,'windows_artifact':11869944063,'android_debug_signed':True,'local_tests_passed':185,'physical_phone_verified':False,'files':files}
    (folder/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (folder/'SHA256SUMS.txt').write_text(''.join(f"{v['sha256']}  {k}\n" for k,v in sorted(files.items())))
    archive=out/'Helix_Beta_v1.0_Installers.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():z.writestr(zipfile.ZipInfo(p.relative_to(folder).as_posix(),(2026,10,14,0,0,0)),p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,m in files.items():assert hashlib.sha256(z.read(n)).hexdigest()==m['sha256']
    shutil.copyfile(folder/'Android/Helix-Beta-v1.0.apk',out/'Helix-Beta-v1.0.apk')
    sums={p.name:sha(p) for p in (archive,out/'Helix-Beta-v1.0.apk')}
    (out/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in sums.items()))
    print(json.dumps({'source_commit':SOURCE,'files':sums},indent=2))


if __name__=='__main__':main()
