"""Exercise archive provenance, real byte hashes and atomic installer delivery."""
import hashlib
import io
import json
import subprocess
import zipfile

import pytest

from tools import collect_beta_installers as collector
from tools import package_beta_installers as package

SHA = 'a' * 40
REPO = 'test/helix'


def zipped(files):
    target = io.BytesIO()
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return target.getvalue()


def fixture_inputs(tmp_path, *, windows_commit=SHA, android_commit=SHA, corrupt_engine=False,
                   corrupt_windows=False, failed_decode=False):
    """Tiny synthetic archives test rejection contracts, not executable behavior."""
    runs = {role: {'id': i, 'run_number': i, 'run_attempt': 1, 'head_sha': SHA,
                   'path': path, 'status': 'completed', 'conclusion': 'success',
                   'repository': {'full_name': REPO}, 'event': 'push'}
            for i, (role, path) in enumerate(package.WORKFLOWS.items(), 1)}
    files = {name: b'guide ' + name.encode() for name in package.GUIDES}
    files.update({'Helix.exe': b'MZgui', 'HelixCLI.exe': b'MZworker'})
    manifest = {'schema': 'helix.windows.build.v1', 'commit': windows_commit,
                'github_run_id': runs['windows']['id'], 'github_repository': REPO,
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    smoke = {'source_lms_preserved': True, 'steps': [
        {'step': step, 'returncode': 0} for step in ('native_fseq', 'lor_engine', 'xlights_engine')]}
    files.update({'BUILD_PROVENANCE.json': json.dumps(manifest), 'VALIDATION.json': json.dumps(smoke)})
    if corrupt_windows:
        files['Helix.exe'] = b'MZchanged gui'
    windows = zipped({'Helix/' + name: data for name, data in files.items()})
    outer_windows = zipped({'Helix-Windows-Portable.zip': windows,
                            'Helix-Windows-Portable.sha256':
                            hashlib.sha256(windows).hexdigest() + '  Helix-Windows-Portable.zip\n'})
    engine_files = {'core/example.py': b'unchanged = True\n'}
    engine_manifest = {'schema': 'helix.android.engine.v1', 'commit': android_commit,
                       'files': {name: hashlib.sha256(data).hexdigest() for name, data in engine_files.items()}}
    if corrupt_engine:
        engine_files['core/example.py'] = b'changed = True\n'
    engine = zipped({**engine_files, 'android-engine-manifest.json': json.dumps(engine_manifest)})
    apk = zipped({'assets/helix-engine.zip': engine, 'AndroidManifest.xml': b'test fixture'})
    report = [{'mode': mode, 'audio_correlation': .99, 'audio_offset_ms': 0,
               'max_mean_pixel_error': 2, 'minimum_expected_lit_pixels_visible': .99,
               'full_song_preview_verified': mode == 'full-song', 'duration': '237.47'}
              for mode in ('xlights', 'lor', 'real-rgb', 'full-song')]
    if failed_decode:
        report[-1]['audio_offset_ms'] = 100
    outer_android = zipped({
        'outputs/apk/debug/app-debug.apk': apk,
        'device-proof/SHA256SUMS.txt': hashlib.sha256(apk).hexdigest() + '  app/build/outputs/apk/debug/app-debug.apk\n',
        'device-proof/status.json': json.dumps({'instrumentation_exit_code': 0, 'proof_errors': []}),
        'device-proof/decoded/decoded-verification.json': json.dumps(report),
        'device-proof/signing-certificate.txt': 'Signer #1 certificate SHA-256 digest: test\n',
    })
    archives, artifacts = {}, {}
    for role, data in [('windows', outer_windows), ('android30', outer_android), ('android36', outer_android)]:
        platform = 'android' if role.startswith('android') else role
        path = archives[role] = tmp_path / (role + '.zip')
        path.write_bytes(data)
        artifacts[role] = {'name': package.ARTIFACT_NAMES[role], 'expired': False, 'size_in_bytes': len(data),
                           'digest': 'sha256:' + hashlib.sha256(data).hexdigest(),
                           'workflow_run': {'head_sha': SHA, 'id': runs[platform]['id']}}
    return {'schema': 'helix.installer-inputs.v1', 'source_sha': SHA, 'repository': REPO,
            'runs': runs, 'artifacts': artifacts}, archives


def build(tmp_path, **kwargs):
    inputs, archives = fixture_inputs(tmp_path, **kwargs)
    return package.assemble(source_sha=SHA, repository=REPO, inputs=inputs,
                            archives=archives, output=tmp_path / 'delivery')


def test_bundle_checks_every_payload_and_keeps_release_gates_open(tmp_path):
    report = build(tmp_path)
    assert report['source_sha'] == SHA and report['release_ready'] is False
    assert report['verification']['android30']['engine_files_verified'] == 1
    assert len(report['open_gates']) == 6
    target = tmp_path / 'delivery/Helix_Beta_v1.0_Installers.zip'
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert names == {'Helix-Windows-Portable.zip', 'Helix-Android-Beta-debug.apk',
                         'VALIDATION_REPORT.json', 'RELEASE_STATUS.md', 'SHA256SUMS.txt', *package.GUIDES}
        for line in archive.read('SHA256SUMS.txt').decode().splitlines():
            digest, name = line.split('  ', 1)
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        assert b'Final release acceptance remains open' in archive.read('RELEASE_STATUS.md')
    assert (tmp_path / 'delivery/Helix_Beta_v1.0_Installers.sha256').read_text().split()[0] == package.sha256(target)


@pytest.mark.parametrize(('mutation', 'message'), [
    (lambda x: x['runs']['windows'].update(head_sha='b' * 40), 'mixed source'),
    (lambda x: x['runs']['native'].update(conclusion='failure'), 'did not succeed'),
    (lambda x: x['runs']['android'].update(status='in_progress'), 'did not succeed'),
    (lambda x: x['runs']['ci'].update(path='.github/workflows/helix-ci.yml'), 'wrong workflow'),
    (lambda x: x['runs']['ci'].update(event='pull_request'), 'unsupported run event'),
    (lambda x: x['artifacts']['android36']['workflow_run'].update(id=999), 'does not belong'),
    (lambda x: x['artifacts']['windows'].update(digest='sha256:' + '0' * 64), 'digest mismatch'),
    (lambda x: x['artifacts']['android30'].update(expired=True), 'expired artifact'),
    (lambda x: x['artifacts']['android36'].update(name='Helix-Android-stability-api-30'), 'wrong artifact name'),
])
def test_unverified_runs_or_artifact_bytes_never_produce_delivery(tmp_path, mutation, message):
    inputs, archives = fixture_inputs(tmp_path)
    mutation(inputs)
    with pytest.raises(ValueError, match=message):
        package.assemble(source_sha=SHA, repository=REPO, inputs=inputs,
                         archives=archives, output=tmp_path / 'delivery')
    assert not (tmp_path / 'delivery').exists()


@pytest.mark.parametrize(('kwargs', 'message'), [
    ({'windows_commit': 'c' * 40}, 'Windows embedded source mismatch'),
    ({'android_commit': 'c' * 40}, 'Android embedded source mismatch'),
    ({'corrupt_engine': True}, 'engine hash mismatch'),
    ({'corrupt_windows': True}, 'Windows embedded hash mismatch'),
    ({'failed_decode': True}, 'decoded image/audio proof failed'),
])
def test_embedded_source_and_engine_bytes_must_match(tmp_path, kwargs, message):
    with pytest.raises(ValueError, match=message):
        build(tmp_path, **kwargs)
    assert not (tmp_path / 'delivery').exists()
    assert not list(tmp_path.glob('helix-installers-*'))


def test_existing_delivery_is_preserved_on_rerun(tmp_path):
    build(tmp_path)
    target = tmp_path / 'delivery/Helix_Beta_v1.0_Installers.zip'
    before = target.read_bytes()
    with pytest.raises(ValueError, match='already exists'):
        build(tmp_path)
    assert target.read_bytes() == before


def test_windows_stamp_binds_clean_git_source_and_real_payload_hashes(tmp_path, monkeypatch):
    root = tmp_path / 'source'
    root.mkdir()
    (root / 'source.py').write_text('unchanged = True\n')
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', 'add', 'source.py'], cwd=root, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'test: fixture source'], cwd=root, check=True)
    distro = tmp_path / 'Helix'
    distro.mkdir()
    for name in ('Helix.exe', 'HelixCLI.exe', *package.GUIDES):
        (distro / name).write_bytes(b'fixture ' + name.encode())
    (distro / 'VALIDATION.json').write_text(json.dumps({'source_lms_preserved': True}))
    monkeypatch.setenv('GITHUB_RUN_ID', '123')
    monkeypatch.setenv('GITHUB_REPOSITORY', REPO)
    stamp = package.stamp_windows(distro, root)
    assert stamp['github_run_id'] == '123'
    assert stamp['commit'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert stamp['files']['Helix.exe'] == package.sha256(distro / 'Helix.exe')
    before = (distro / 'BUILD_PROVENANCE.json').read_bytes()
    (root / 'source.py').write_text('changed = True\n')
    with pytest.raises(ValueError, match='Tracked source changes'):
        package.stamp_windows(distro, root)
    assert (distro / 'BUILD_PROVENANCE.json').read_bytes() == before


def test_archive_member_traversal_and_duplicates_are_rejected():
    with pytest.raises(ValueError, match='Unsafe ZIP member'):
        package.checked_zip(io.BytesIO(zipped({'../outside': 'bytes'})))
    archive = io.BytesIO()
    with pytest.warns(UserWarning, match='Duplicate name'):
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('same', 'one')
            z.writestr('same', 'two')
    with pytest.raises(ValueError, match='Duplicate ZIP member'):
        package.checked_zip(io.BytesIO(archive.getvalue()))


def test_collector_rejects_failed_newer_attempt_instead_of_using_old_green(monkeypatch):
    old = {'id': 1, 'run_number': 1, 'run_attempt': 1, 'head_sha': SHA,
           'event': 'push', 'status': 'completed', 'conclusion': 'success'}
    new = dict(old, run_attempt=2, conclusion='failure')
    monkeypatch.setattr(collector, 'api', lambda *a: {'workflow_runs': [old, new]})
    with pytest.raises(ValueError, match='latest exact-source run did not succeed'):
        collector.select_runs(REPO, SHA)


def test_collector_waits_for_running_gates_and_ignores_other_source(monkeypatch):
    good = {'id': 1, 'run_number': 1, 'run_attempt': 1, 'head_sha': SHA,
            'event': 'push', 'status': 'completed', 'conclusion': 'success'}
    foreign = dict(good, head_sha='b' * 40, run_number=99)
    running = dict(good, status='in_progress', conclusion=None)
    monkeypatch.setattr(collector, 'api', lambda *a: {'workflow_runs': [good, foreign]})
    assert set(collector.select_runs(REPO, SHA)) == set(package.WORKFLOWS)
    monkeypatch.setattr(collector, 'api', lambda *a: {'workflow_runs': [running]})
    assert collector.select_runs(REPO, SHA) == {}
