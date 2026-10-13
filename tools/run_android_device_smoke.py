"""Run Android instrumentation and retain device proofs even on failure."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    dest=ROOT/'android/app/build/device-proof';dest.mkdir(parents=True,exist_ok=True)
    result=subprocess.run(['gradle','--no-daemon',':app:connectedDebugAndroidTest'],cwd=ROOT/'android')
    proof_errors=[]
    names=['xlights-show.zip','lor-show.zip','real-rgb-show.zip','failed-preview-show.zip','full-song-show.zip','launcher.png','remote-transport.json','screen-playback.png','cancellation.json']
    names += ['screen-'+page+'.png' for page in ('music','layout','style','advanced','generate','results')]
    for name in names:
        cmd=['adb','pull',f'/sdcard/Download/HelixAndroidSmoke/{name}',str(dest/name)]
        proof=subprocess.run(cmd,capture_output=True)
        if proof.returncode:proof_errors.append({'file':name,'error':proof.stderr.decode(errors='replace')})
    with (dest/'android.log').open('w') as log:
        subprocess.run(['adb','logcat','-d','-s','HelixSmoke','AndroidRuntime'],stdout=log,stderr=subprocess.STDOUT)
    (dest/'status.json').write_text(json.dumps({'instrumentation_exit_code':result.returncode,'proof_errors':proof_errors},indent=2))
    if result.returncode==0:
        apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
        subprocess.run(['adb','install',str(apk)],check=True)
        subprocess.run(['adb','shell','run-as','org.helixsequencer.android','sh','-c','echo preserved > files/upgrade-marker'],check=True)
        subprocess.run(['adb','install','-r',str(apk)],check=True)
        marker=subprocess.check_output(['adb','shell','run-as','org.helixsequencer.android','cat','files/upgrade-marker']).decode().strip()
        assert marker=='preserved'
        (dest/'install-upgrade.json').write_text(json.dumps({'fresh_install':True,'same_key_same_version_reinstall':True,'private_data_preserved':True,'old_beta_certificate_upgrade':'not tested'},indent=2))
    return result.returncode or (1 if proof_errors else 0)

if __name__=='__main__':raise SystemExit(main())

