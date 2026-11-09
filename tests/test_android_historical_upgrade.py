from tools.android_upgrade_preflight import compare


def apk(**changes):
    return dict(dict(package_id='org.helixsequencer.android',signature_verified=True,
        signer_sha256=['a'*64],versionCode=6,versionName='1.0-beta',min_sdk=26,abis=['arm64-v8a','x86_64']),**changes)


def test_matching_version_name_cannot_hide_changed_signer_or_same_code():
    result=compare(apk(),apk(signer_sha256=['b'*64]))
    assert result['failures']==['established_signer','increasing_versionCode']
    assert result['key_recovery_required']
    assert result['expected_failure_if_installed']=='INSTALL_FAILED_UPDATE_INCOMPATIBLE'
    assert result['package_manager_failure_observed'] is False
    assert result['actual_baseline_update_verified'] is False


def test_preflight_never_promotes_checks_to_device_or_data_proof():
    result=compare(apk(),apk(versionCode=7),device_sdk=36,device_abi='arm64-v8a')
    assert result['preflight_passed']
    assert result['actual_baseline_update_verified'] is False
    assert result['user_data_preservation_verified'] is False


def test_package_unsigned_sdk_and_abi_fail_independently():
    result=compare(apk(),apk(package_id='org.different',signature_verified=False,
        versionCode=7,min_sdk=35,abis=['x86_64']),device_sdk=30,device_abi='arm64-v8a')
    assert set(result['failures'])=={'package_identity','both_signatures_verified','device_sdk','device_abi'}
