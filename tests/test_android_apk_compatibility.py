import hashlib
import json
from types import SimpleNamespace
from tools.android_apk_compatibility import inspect


def inputs(tmp_path, *, matching=True, launched=True):
    build = tmp_path / 'build'
    folder = build / 'outputs/apk/debug'
    folder.mkdir(parents=True)
    apk = folder / 'app-debug.apk'
    apk.write_bytes(b'test APK bytes')
    proof = build / 'device-proof'
    proof.mkdir()
    (proof / 'install-upgrade.json').write_text(json.dumps(dict(
        apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest() if matching else 'different',
        fresh_install=True, launch_verified=launched)))
    return build


def signed(*args, **kwargs):
    return SimpleNamespace(returncode=0, stdout='Signer #1 certificate SHA-256 digest: test-cert', stderr='')


def test_exact_installed_and_launched_apk_has_valid_json_report(tmp_path):
    build = inputs(tmp_path)
    result = inspect(build, tmp_path / 'apksigner', run=signed)
    saved = json.loads((build / 'device-proof/apk-install-compatibility.json').read_text())
    assert saved == result
    assert result['variants'][0]['installation_verified'] is True
    assert result['old_beta_upgrade_verified'] is False
    assert result['debug_to_release_update_compatible'] is False


def test_certificate_alone_cannot_prove_install_or_launch(tmp_path):
    for matching, launched in ((False, True), (True, False)):
        build = inputs(tmp_path / str(matching), matching=matching, launched=launched)
        result = inspect(build, tmp_path / 'apksigner', run=signed)
        assert result['variants'][0]['signature_verified'] is True
        assert result['variants'][0]['installable'] is False


def test_unsigned_release_is_reported_by_its_actual_filename(tmp_path):
    build = inputs(tmp_path)
    folder = build / 'outputs/apk/release'
    folder.mkdir()
    (folder / 'app-release-unsigned.apk').write_bytes(b'unsigned')
    def run(command, **kwargs):
        return signed() if command[-1].endswith('app-debug.apk') else SimpleNamespace(returncode=1, stdout='', stderr='No certificates')
    result = inspect(build, tmp_path / 'apksigner', run=run)
    release = result['variants'][1]
    assert release['exists'] is True and release['filename'] == 'app-release-unsigned.apk'
    assert release['signature_verified'] is False and release['installable'] is False
