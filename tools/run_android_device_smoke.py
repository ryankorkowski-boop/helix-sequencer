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
    for name in ('xlights-show.zip','lor-show.zip','launcher.png','remote-transport.json'):
        cmd=['adb','pull',f'/sdcard/Download/HelixAndroidSmoke/{name}',str(dest/name)]
        proof=subprocess.run(cmd,capture_output=True)
        if proof.returncode:proof_errors.append({'file':name,'error':proof.stderr.decode(errors='replace')})
    with (dest/'android.log').open('w') as log:
        subprocess.run(['adb','logcat','-d','-s','HelixSmoke','AndroidRuntime'],stdout=log,stderr=subprocess.STDOUT)
    (dest/'status.json').write_text(json.dumps({'instrumentation_exit_code':result.returncode,'proof_errors':proof_errors},indent=2))
    return result.returncode or (1 if proof_errors else 0)

if __name__=='__main__':raise SystemExit(main())
