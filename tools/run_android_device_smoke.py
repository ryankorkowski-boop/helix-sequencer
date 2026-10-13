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
    for mode in ('xlights','lor'):
        cmd=['adb','exec-out','run-as','org.helixsequencer.android','cat',f'files/smoke-{mode}/Helix-show.zip']
        proof=subprocess.run(cmd,capture_output=True)
        if proof.returncode==0 and proof.stdout.startswith(b'PK'):
            (dest/f'{mode}-show.zip').write_bytes(proof.stdout)
    with (dest/'android.log').open('w') as log:
        subprocess.run(['adb','logcat','-d','-s','HelixSmoke','AndroidRuntime'],stdout=log,stderr=subprocess.STDOUT)
    subprocess.run(['adb','shell','am','start','-n','org.helixsequencer.android/.MainActivity'],stdout=subprocess.DEVNULL)
    shot=subprocess.run(['adb','exec-out','screencap','-p'],capture_output=True)
    if shot.returncode==0 and shot.stdout.startswith(b'\x89PNG'):(dest/'launcher.png').write_bytes(shot.stdout)
    (dest/'status.json').write_text(json.dumps({'instrumentation_exit_code':result.returncode},indent=2))
    return result.returncode

if __name__=='__main__':raise SystemExit(main())
