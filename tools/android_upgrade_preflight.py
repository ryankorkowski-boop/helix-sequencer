"""Compare a retained historical APK with a candidate, without touching a phone.

Passing cryptographic/manifest checks is necessary, never proof of an actual
data-preserving baseline update. A certificate cannot recover a private key.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import zipfile
from tools.android_apk_compatibility import apk_digest


def inspect_apk(path, apksigner, aapt, *, run=subprocess.run):
    path=Path(path)
    signature=run([str(apksigner),'verify','--print-certs',str(path)],capture_output=True,text=True)
    metadata=run([str(aapt),'dump','badging',str(path)],capture_output=True,text=True)
    if metadata.returncode:
        raise ValueError('Cannot inspect APK manifest: '+path.name)
    package=re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']*)'",metadata.stdout,re.M)
    if package is None:raise ValueError('APK package/version metadata missing')
    certs=re.findall(r'^Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]{64})$',signature.stdout,re.M)
    with zipfile.ZipFile(path) as archive:
        abis=sorted({name.split('/')[1] for name in archive.namelist() if name.startswith('lib/') and name.endswith('.so')})
        splits=any(name.startswith('splits/') for name in archive.namelist())
    sdk=re.search(r"^sdkVersion:'(\d+)'",metadata.stdout,re.M)
    return dict(filename=path.name,sha256=apk_digest(path),package_id=package[1],versionCode=int(package[2]),
        versionName=package[3],min_sdk=int(sdk[1]) if sdk else None,abis=abis,
        signature_verified=signature.returncode==0 and bool(certs),signer_sha256=sorted(set(certs)),
        has_embedded_splits=splits)


def compare(baseline,candidate, *, device_sdk=None,device_abi=None):
    checks=dict(package_identity=baseline['package_id']==candidate['package_id'],
        both_signatures_verified=baseline['signature_verified'] and candidate['signature_verified'],
        established_signer=candidate['signer_sha256']==baseline['signer_sha256'] and bool(baseline['signer_sha256']),
        increasing_versionCode=candidate['versionCode']>baseline['versionCode'],
        device_sdk=(device_sdk is None or (candidate['min_sdk'] is not None and candidate['min_sdk']<=device_sdk)),
        device_abi=(device_abi is None or not candidate['abis'] or device_abi in candidate['abis']))
    failures=[name for name,passed in checks.items() if not passed]
    return dict(schema='helix.android-historical-upgrade-preflight.v1',baseline=baseline,candidate=candidate,
        checks=checks,preflight_passed=not failures,failures=failures,
        actual_baseline_update_verified=False,user_data_preservation_verified=False,
        device_compatibility_verified=device_sdk is not None and device_abi is not None and not failures,
        key_recovery_required='established_signer' in failures,
        expected_failure_if_installed='INSTALL_FAILED_UPDATE_INCOMPATIBLE' if 'established_signer' in failures else None,
        package_manager_failure_observed=False,
        limitation='Different signer requires the legitimate original private key or separately verified Android signing lineage. This tool does not infer lineage, install, uninstall, clear data, or count a same-APK reinstall as an upgrade.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--apksigner',required=True,type=Path);p.add_argument('--aapt',required=True,type=Path)
    p.add_argument('--device-sdk',type=int);p.add_argument('--device-abi');p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    report=compare(inspect_apk(a.baseline,a.apksigner,a.aapt),inspect_apk(a.candidate,a.apksigner,a.aapt),
                   device_sdk=a.device_sdk,device_abi=a.device_abi)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return 0 if report['preflight_passed'] else 2


if __name__=='__main__':raise SystemExit(main())
