"""Report signing separately from source-matched device installation evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def apk_digest(path: Path) -> str:
    # The Android build host intentionally uses Python3.10 (Chaquopy).
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def certificate_digest(details: str) -> str | None:
    for line in details.splitlines():
        if 'certificate SHA-256 digest:' in line:
            return line.split(':', 1)[1].strip()
    return None


def inspect(build: Path, apksigner: Path, *, run=subprocess.run) -> dict:
    proof = build / 'device-proof'
    evidence = proof / 'install-upgrade.json'
    installed = json.loads(evidence.read_text()) if evidence.is_file() else {}
    records = []
    for kind in ('debug', 'release'):
        candidates = sorted((build / 'outputs/apk' / kind).glob('*.apk'))
        if not candidates:
            records.append(dict(variant=kind, exists=False, installable=False, installation_verified=False))
        for apk in candidates:
            result = run([str(apksigner), 'verify', '--print-certs', str(apk)],
                         text=True, capture_output=True)
            sha = apk_digest(apk)
            device_verified = bool(result.returncode == 0 and installed.get('apk_sha256') == sha
                                   and installed.get('fresh_install') is True
                                   and installed.get('launch_verified') is True)
            records.append(dict(variant=kind, filename=apk.name, exists=True, apk_sha256=sha,
                                signature_verified=result.returncode == 0,
                                certificate_details=result.stdout.strip(), error=result.stderr.strip(),
                                installation_verified=device_verified,
                                installable=device_verified))
    debug = next((r for r in records if r['variant'] == 'debug'), {})
    release = next((r for r in records if r['variant'] == 'release' and r.get('signature_verified')), {})
    debug_sha = certificate_digest(debug.get('certificate_details', ''))
    release_sha = certificate_digest(release.get('certificate_details', ''))
    report = dict(package_id='org.helixsequencer.android', variants=records,
                  debug_to_release_certificate_match=bool(debug_sha and release_sha and debug_sha == release_sha),
                  debug_to_release_update_compatible=False, old_beta_upgrade_verified=False,
                  limitation='Only the exact installed and launched APK is verified. Cross-build/old-beta upgrades require the original installed signing key and an actual update test; unsigned APKs cannot install.')
    proof.mkdir(parents=True, exist_ok=True)
    (proof / 'apk-install-compatibility.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--apksigner', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.build, args.apksigner), indent=2))
