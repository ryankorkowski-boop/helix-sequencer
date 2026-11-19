"""Prove a review APK coexists with the disposable emulator's baseline app."""
import json
import os
from pathlib import Path
import subprocess
from tools.android_upgrade_preflight import inspect_apk


def output(args):
    return subprocess.check_output(args, text=True).strip()


def main():
    if output(['adb', 'shell', 'getprop', 'ro.kernel.qemu']) != '1':
        raise RuntimeError('Review-install test is restricted to a disposable emulator')
    root = Path(__file__).resolve().parents[1]
    dest = root/'android/app/build/device-proof'
    apk = root/'android/app/build/outputs/apk/review/app-review.apk'
    build_tools = Path(os.environ['ANDROID_HOME'])/'build-tools/36.0.0'
    identity = inspect_apk(apk, build_tools/'apksigner', build_tools/'aapt')
    if identity['package_id'] != 'org.helixsequencer.android.review' or not identity['signature_verified']:
        raise ValueError('Review APK identity/signature failed')
    baseline = ['adb', 'shell', 'run-as', 'org.helixsequencer.android', 'cat', 'files/upgrade-marker']
    before = output(baseline)
    subprocess.run(['adb', 'install', str(apk)], check=True)
    launched = output(['adb', 'shell', 'am', 'start', '-W', '-n',
        'org.helixsequencer.android.review/org.helixsequencer.android.MainActivity'])
    if 'Status: ok' not in launched or 'Error:' in launched:
        raise RuntimeError('Review activity failed to launch: '+launched)
    pid = output(['adb', 'shell', 'pidof', 'org.helixsequencer.android.review'])
    after = output(baseline)
    if not pid or before != 'preserved' or before != after:
        raise ValueError('Review co-installation did not preserve the baseline marker')
    report = dict(schema='helix.android.review-coinstall.v1', apk=identity,
        fresh_review_install=True, launch_verified=True, baseline_marker_preserved=True,
        separate_package=True, historical_in_place_update=False,
        owner_phone_installation_verified=False, launch_output=launched,
        limitation='Disposable-emulator co-installation; private jobs/settings are not transferred between apps')
    (dest/'review-install.json').write_text(json.dumps(report, indent=2)+'\n')
    with (dest/'review-launch.png').open('wb') as image:
        subprocess.run(['adb', 'exec-out', 'screencap', '-p'], stdout=image, check=True)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
