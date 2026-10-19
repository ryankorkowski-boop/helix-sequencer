"""Verify exact-source CI installers and assemble a beta review ZIP (no music)."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import zipfile

WORKFLOWS = {
    'windows': '.github/workflows/windows-portable.yml',
    'android': '.github/workflows/android-offline.yml',
    'native': '.github/workflows/beta-completion-native.yml',
    'ci': '.github/workflows/unit-tests.yml',
}
ARTIFACT_NAMES = {'windows': 'Helix-Windows-Portable',
                  'android30': 'Helix-Android-stability-api-30',
                  'android36': 'Helix-Android-stability-api-36'}
GUIDES = ('WELCOME_TO_HELIX.md', 'INSTALL_AND_TROUBLESHOOT.md', 'LICENSE',
          'NOTICE', 'THIRD_PARTY_LICENSES.md', 'COMMERCIAL_LICENSING.md')
OPEN_GATES = [
    'Independent listening, uncertain tom labels and source-separated duet acceptance',
    'Complete original LightsOutTheme and track-specific redistribution permissions',
    'Physical Samsung/ARM64, controller and vendor LOR checks',
    'Production Android signing, cross-build upgrade continuity and 16KB/store readiness',
    'Contributor/asset relicensing authority and reviewed branch integration',
    'Authorized full-song showcase package and final release acceptance',
]


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_zip(source) -> zipfile.ZipFile:
    archive = zipfile.ZipFile(source)
    try:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Duplicate ZIP member')
        for name in names:
            path = PurePosixPath(name)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in name,
                    f'Unsafe ZIP member: {name}')
        require(archive.testzip() is None, 'ZIP CRC failure')
        return archive
    except BaseException:
        archive.close()
        raise


def member(archive, suffix):
    matches = [name for name in archive.namelist()
               if name == suffix or name.endswith('/' + suffix)]
    require(len(matches) == 1, f'Expected exactly one {suffix}')
    return matches[0]


def read_json(archive, suffix):
    return json.loads(archive.read(member(archive, suffix)))


def stamp_windows(directory: Path, root: Path) -> dict:
    """Called after the actual packaged worker/GUI smoke, before ZIP creation."""
    require(not subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=root).strip(),
            'Tracked source changes prevent a clean Windows source receipt')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    files = {name: sha256(directory / name) for name in ('Helix.exe', 'HelixCLI.exe', *GUIDES)}
    require(json.loads((directory / 'VALIDATION.json').read_text())['source_lms_preserved'],
            'Windows smoke did not preserve the input LMS')
    receipt = {'schema': 'helix.windows.build.v1', 'commit': commit, 'files': files,
               'github_run_id': os.environ.get('GITHUB_RUN_ID'),
               'github_repository': os.environ.get('GITHUB_REPOSITORY')}
    (directory / 'BUILD_PROVENANCE.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def verify_inputs(inputs: dict, source_sha: str, repository: str, archives: dict):
    require(bool(re.fullmatch('[0-9a-f]{40}', source_sha)), 'Expected a full source SHA')
    require(inputs.get('schema') == 'helix.installer-inputs.v1', 'Unknown input schema')
    require(inputs.get('source_sha') == source_sha and inputs.get('repository') == repository,
            'Input source/repository mismatch')
    for role, workflow in WORKFLOWS.items():
        run = inputs['runs'][role]
        require(run['head_sha'] == source_sha, f'{role}: mixed source SHA')
        require(run['status'] == 'completed' and run['conclusion'] == 'success',
                f'{role}: workflow did not succeed')
        require(run['path'] == workflow, f'{role}: wrong workflow')
        require(run['repository']['full_name'] == repository, f'{role}: wrong repository')
        # PR merge commits are not interchangeable with the tested branch head.
        require(run['event'] in ('push', 'workflow_dispatch'), f'{role}: unsupported run event')
    for role, path in archives.items():
        artifact = inputs['artifacts'][role]
        platform = 'android' if role.startswith('android') else role
        require(artifact['name'] == ARTIFACT_NAMES[role], f'{role}: wrong artifact name')
        require(not artifact['expired'], f'{role}: expired artifact')
        require(artifact['workflow_run']['head_sha'] == source_sha and
                artifact['workflow_run']['id'] == inputs['runs'][platform]['id'],
                f'{role}: artifact does not belong to verified run')
        require(path.stat().st_size == artifact['size_in_bytes'], f'{role}: artifact size mismatch')
        require(artifact.get('digest') == 'sha256:' + sha256(path), f'{role}: artifact digest mismatch')


def verify_windows(outer: Path, destination: Path, source_sha: str, run: dict) -> dict:
    with checked_zip(outer) as artifact:
        name = member(artifact, 'Helix-Windows-Portable.zip')
        with artifact.open(name) as src, destination.open('wb') as dst:
            shutil.copyfileobj(src, dst)
        checksum = artifact.read(member(artifact, 'Helix-Windows-Portable.sha256')).decode().split()
        require(checksum == [sha256(destination), 'Helix-Windows-Portable.zip'],
                'Windows build checksum mismatch')
    with checked_zip(destination) as windows:
        receipt = read_json(windows, 'BUILD_PROVENANCE.json')
        require(receipt.get('schema') == 'helix.windows.build.v1' and receipt['commit'] == source_sha,
                'Windows embedded source mismatch')
        require(str(receipt['github_run_id']) == str(run['id']) and
                receipt['github_repository'] == run['repository']['full_name'],
                'Windows embedded build-run mismatch')
        for name in ('Helix.exe', 'HelixCLI.exe', *GUIDES):
            data = windows.read(member(windows, 'Helix/' + name))
            require(hashlib.sha256(data).hexdigest() == receipt['files'][name],
                    f'Windows embedded hash mismatch: {name}')
            if name.endswith('.exe'):
                require(data[:2] == b'MZ', f'Windows executable header missing: {name}')
        smoke = read_json(windows, 'Helix/VALIDATION.json')
        require(smoke['source_lms_preserved'] is True, 'Windows source preservation failed')
        require({s['step'] for s in smoke['steps'] if s['returncode'] == 0} ==
                {'native_fseq', 'lor_engine', 'xlights_engine'}, 'Windows packaged smoke incomplete')
        return {'build': receipt, 'smoke': smoke}


def verify_android(outer: Path, destination: Path, source_sha: str) -> dict:
    with checked_zip(outer) as artifact:
        apk_name = member(artifact, 'apk/debug/app-debug.apk')
        with artifact.open(apk_name) as src, destination.open('wb') as dst:
            shutil.copyfileobj(src, dst)
        apk_hash = sha256(destination)
        sums = artifact.read(member(artifact, 'device-proof/SHA256SUMS.txt')).decode().splitlines()
        matching = [line.split() for line in sums if line.split()[-1].endswith('/apk/debug/app-debug.apk')]
        require(len(matching) == 1 and matching[0][0] == apk_hash, 'APK build checksum mismatch')
        status = read_json(artifact, 'device-proof/status.json')
        require(status['instrumentation_exit_code'] == 0 and not status['proof_errors'],
                'Android instrumentation proof incomplete')
        reports = read_json(artifact, 'device-proof/decoded/decoded-verification.json')
        require(len(reports) == 4 and {r['mode'] for r in reports} ==
                {'xlights', 'lor', 'real-rgb', 'full-song'}, 'Android decode proof incomplete')
        for report in reports:
            require(report['audio_correlation'] > .97 and abs(report['audio_offset_ms']) < 5 and
                    report['max_mean_pixel_error'] < 12 and
                    report['minimum_expected_lit_pixels_visible'] > .8,
                    'Android decoded image/audio proof failed')
        full = next(r for r in reports if r['mode'] == 'full-song')
        require(full['full_song_preview_verified'] is True and float(full['duration']) > 120,
                'Android full-song proof missing')
        signing = artifact.read(member(artifact, 'device-proof/signing-certificate.txt')).decode()
        require('certificate SHA-256 digest:' in signing, 'Android signing receipt missing')
    with checked_zip(destination) as apk:
        # Android's engine is small; unlike decoded movies, it can be verified in memory.
        with checked_zip(io.BytesIO(apk.read('assets/helix-engine.zip'))) as engine:
            manifest = read_json(engine, 'android-engine-manifest.json')
            require(manifest.get('schema') == 'helix.android.engine.v1' and
                    manifest['commit'] == source_sha, 'Android embedded source mismatch')
            require(set(engine.namelist()) == set(manifest['files']) | {'android-engine-manifest.json'},
                    'Android engine inventory mismatch')
            for name, digest in manifest['files'].items():
                require(hashlib.sha256(engine.read(name)).hexdigest() == digest,
                        f'Android engine hash mismatch: {name}')
    return {'apk_sha256': apk_hash, 'engine_commit': source_sha,
            'engine_files_verified': len(manifest['files']), 'decoded': reports,
            'signing_certificate': signing, 'signing_status': 'debug beta; production upgrade not verified'}


def assemble(*, source_sha: str, repository: str, inputs: dict, archives: dict,
             output: Path) -> dict:
    """Never overwrite a prior delivery; publish only a fully verified temporary ZIP."""
    require(not output.exists(), 'Output already exists; choose a new delivery directory')
    require(set(archives) == {'windows', 'android30', 'android36'}, 'Both Android API proofs required')
    verify_inputs(inputs, source_sha, repository, archives)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='helix-installers-', dir=output.parent) as temporary:
        stage = Path(temporary)
        windows = stage / 'Helix-Windows-Portable.zip'
        apk = stage / 'Helix-Android-Beta-debug.apk'
        verification = {'windows': verify_windows(archives['windows'], windows, source_sha, inputs['runs']['windows']),
                        'android30': verify_android(archives['android30'], apk, source_sha),
                        'android36': verify_android(archives['android36'], stage / 'api36-proof.apk', source_sha)}
        (stage / 'api36-proof.apk').unlink()  # Ship the tested API30 APK; record each independently built APK.
        with checked_zip(windows) as archive:
            for name in GUIDES:
                (stage / name).write_bytes(archive.read('Helix/' + name))
        report = {'schema': 'helix.installers.review.v1', 'source_sha': source_sha,
                  'repository': repository, 'release_ready': False, 'distribution': 'beta review',
                  'open_gates': OPEN_GATES, 'inputs': inputs, 'verification': verification,
                  'files': {p.name: {'sha256': sha256(p), 'bytes': p.stat().st_size}
                            for p in sorted(stage.iterdir())}}
        (stage / 'VALIDATION_REPORT.json').write_text(json.dumps(report, indent=2) + '\n')
        (stage / 'RELEASE_STATUS.md').write_text(
            '# Helix Beta Release v1.0 — installer review\n\n'
            f'Source: {source_sha}\n\nSoftware checks passed. Final release acceptance remains open.\n\n'
            'Extract Helix-Windows-Portable.zip fully before running Helix.exe. The Android APK '
            'is a debug beta; preserve existing app data and signing continuity. '
            'Read INSTALL_AND_TROUBLESHOOT.md before installing.\n\n'
            'These installers contain dependencies and layouts, with no soundtrack/showcase media. '
            'The API30 APK is included; both API30/API36 builds were independently verified.\n\n'
            + '\n'.join('- ' + gate for gate in OPEN_GATES) + '\n')
        (stage / 'SHA256SUMS.txt').write_text(''.join(
            f'{sha256(p)}  {p.name}\n' for p in sorted(stage.iterdir())))
        deliver = stage / 'delivery'
        deliver.mkdir()
        target = deliver / 'Helix_Beta_v1.0_Installers.zip'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as archive:
            for path in sorted(stage.iterdir()):
                if path.is_file():
                    archive.write(path, path.name)
        with checked_zip(target) as archive:
            for line in archive.read('SHA256SUMS.txt').decode().splitlines():
                digest, name = line.split('  ', 1)
                with archive.open(name) as stream:
                    require(hashlib.file_digest(stream, 'sha256').hexdigest() == digest,
                            f'Delivery hash mismatch: {name}')
        (deliver / 'Helix_Beta_v1.0_Installers.sha256').write_text(f'{sha256(target)}  {target.name}\n')
        (deliver / 'VALIDATION_REPORT.json').write_text(json.dumps(report, indent=2) + '\n')
        # Keep the old delivery untouched even when verification raises above.
        shutil.move(str(deliver), str(output))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    stamp = sub.add_parser('stamp-windows')
    stamp.add_argument('--directory', type=Path, required=True)
    build = sub.add_parser('assemble')
    build.add_argument('--source-sha', required=True)
    build.add_argument('--repository', required=True)
    build.add_argument('--inputs', type=Path, required=True)
    for role in ('windows', 'android30', 'android36'):
        build.add_argument('--' + role, type=Path, required=True)
    build.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'stamp-windows':
        stamp_windows(args.directory, Path(__file__).resolve().parents[1])
    else:
        assemble(source_sha=args.source_sha, repository=args.repository,
                 inputs=json.loads(args.inputs.read_text()), output=args.output,
                 archives={role: getattr(args, role) for role in ('windows', 'android30', 'android36')})


if __name__ == '__main__':
    main()
