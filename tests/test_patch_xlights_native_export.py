"""Test all-or-nothing pinned source transformation, not native render quality."""
from pathlib import Path

import pytest
from tools import patch_xlights_native_export as patcher


def source(tmp_path, size, camera):
    paths = [tmp_path / 'src-ui-wx/xLightsMain.cpp',
             tmp_path / 'src-ui-wx/app-shell/TabSequence.cpp']
    for path, text in zip(paths, (size, camera)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('prefix\n' + text + '\nsuffix\n')
    return paths


def test_repairs_both_sites_and_preserves_surrounding_source(tmp_path):
    paths = source(tmp_path, patcher.SIZE_OLD, patcher.CAMERA_OLD)
    patcher.apply(tmp_path)
    assert paths[0].read_text() == 'prefix\n' + patcher.SIZE_NEW + '\nsuffix\n'
    assert paths[1].read_text() == 'prefix\n' + patcher.CAMERA_NEW + '\nsuffix\n'


@pytest.mark.parametrize('camera', ['upstream changed', patcher.CAMERA_OLD * 2])
def test_drift_does_not_partially_patch_other_file(tmp_path, camera):
    paths = source(tmp_path, patcher.SIZE_OLD, camera)
    before = [p.read_bytes() for p in paths]
    with pytest.raises(ValueError, match='Pinned'):
        patcher.apply(tmp_path)
    assert [p.read_bytes() for p in paths] == before


def test_second_application_refused_without_corrupting_patched_source(tmp_path):
    paths = source(tmp_path, patcher.SIZE_OLD, patcher.CAMERA_OLD)
    patcher.apply(tmp_path)
    before = [p.read_bytes() for p in paths]
    with pytest.raises(ValueError, match='Pinned'):
        patcher.apply(tmp_path)
    assert [p.read_bytes() for p in paths] == before
