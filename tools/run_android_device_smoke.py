"""Run Android instrumentation and retain device proofs even on failure."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    # This fresh-install smoke resets app data. It is restricted to disposable
    # emulators; never let this path uninstall the owner's historical beta.
    emulator=subprocess.check_output(['adb','shell','getprop','ro.kernel.qemu'],text=True).strip()
    if emulator!='1':
        raise RuntimeError('Fresh-install smoke requires a disposable emulator; historical phone updates must use install -r and preserve data')
    dest=ROOT/'android/app/build/device-proof';dest.mkdir(parents=True,exist_ok=True)
    result=subprocess.run(['gradle','--no-daemon',':app:connectedDebugAndroidTest'],cwd=ROOT/'android')
    proof_errors=[]
    names=['xlights-show.zip','lor-show.zip','real-rgb-show.zip','failed-preview-show.zip','full-song-show.zip','launcher.png','remote-transport.json','screen-playback.png','cancellation.json']
    names += ['screen-'+page+'.png' for page in ('music','layout','style','advanced','generate','results')]
    names += ['screen-instructions.png', 'instructions-band-ui.json', 'band-off-show.zip']
    for name in names:
        cmd=['adb','pull',f'/sdcard/Download/HelixAndroidSmoke/{name}',str(dest/name)]
        proof=subprocess.run(cmd,capture_output=True)
        if proof.returncode:proof_errors.append({'file':name,'error':proof.stderr.decode(errors='replace')})
    with (dest/'android.log').open('w') as log:
        subprocess.run(['adb','logcat','-d','-s','HelixSmoke','AndroidRuntime'],stdout=log,stderr=subprocess.STDOUT)
    (dest/'status.json').write_text(json.dumps({'instrumentation_exit_code':result.returncode,'proof_errors':proof_errors},indent=2))
    if result.returncode==0:
        apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
        subprocess.run(['adb','uninstall','org.helixsequencer.android'],capture_output=True)
        subprocess.run(['adb','install',str(apk)],check=True)
        launched=subprocess.check_output(['adb','shell','am','start','-W','-n',
            'org.helixsequencer.android/.MainActivity'],text=True)
        if 'Status: ok' not in launched or 'Error:' in launched:
            raise RuntimeError('Installed beta did not launch: '+launched)
        pid=subprocess.check_output(['adb','shell','pidof','org.helixsequencer.android'],text=True).strip()
        if not pid:raise RuntimeError('Installed beta has no live application process')
        subprocess.run(['adb','shell','run-as','org.helixsequencer.android','mkdir','-p','files'],check=True)
        subprocess.run(['adb','shell',"run-as org.helixsequencer.android sh -c 'echo preserved > files/upgrade-marker'"],check=True)
        subprocess.run(['adb','install','-r',str(apk)],check=True)
        marker=subprocess.check_output(['adb','shell','run-as','org.helixsequencer.android','cat','files/upgrade-marker']).decode().strip()
        assert marker=='preserved'
        (dest/'install-upgrade.json').write_text(json.dumps({'fresh_install':True,'launch_verified':True,
            'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'launch_output':launched,
            'same_key_same_version_reinstall':True,'private_data_preserved':True,
            'old_beta_certificate_upgrade':'not tested'},indent=2)+'\n')
    return result.returncode or (1 if proof_errors else 0)

if __name__=='__main__':raise SystemExit(main())

