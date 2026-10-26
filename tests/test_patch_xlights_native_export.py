"""Test all-or-nothing pinned source transformation, not native render quality."""
from pathlib import Path

import pytest
from tools import patch_xlights_native_export as patcher


def source(tmp_path, size, camera):
    paths = []
    for relative, replacements in patcher.PATCHES.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = "\n".join(before for before, _ in replacements)
        if relative.endswith('xLightsMain.cpp'): content = size
        if relative.endswith('TabSequence.cpp'): content = camera
        path.write_text('prefix\n' + content + '\nsuffix\n')
        paths.append(path)
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


def test_export_size_event_is_dispatched_before_cached_dimensions_are_used():
    assert patcher.SIZE_NEW.index('ProcessEvent(exportSizeEvent)') < patcher.SIZE_NEW.index('int width =')
    assert 'exportSizeEvent.SetEventObject(housePreview)' in patcher.SIZE_NEW
    assert 'desiredWidth / contentScaleFactor' in patcher.SIZE_NEW


def test_late_capture_source_drift_leaves_every_file_unchanged(tmp_path):
    paths = source(tmp_path, patcher.SIZE_OLD, patcher.CAMERA_OLD)
    paths[-1].write_text('different upstream capture implementation')
    before = [p.read_bytes() for p in paths]
    with pytest.raises(ValueError, match='Pinned'):
        patcher.apply(tmp_path)
    assert [p.read_bytes() for p in paths] == before


def test_framebuffer_is_bound_before_clear_and_restored_after_readback():
    assert 'GL_FRAMEBUFFER_COMPLETE' in patcher.PREPARE_NEW
    assert 'GL_DEPTH_COMPONENT24' in patcher.PREPARE_NEW
    assert 'glBindFramebuffer(GL_FRAMEBUFFER, m_exportFramebuffer)' in patcher.PREPARE_NEW
    assert 'mWindowWidth = ' in patcher.PREPARE_NEW
    assert 'releaseExportFramebuffer();' in patcher.RELEASE_NEW
    assert 'GL_DRAW_FRAMEBUFFER, m_exportPreviousDraw' in patcher.RELEASE_NEW
    assert 'GL_READ_FRAMEBUFFER, m_exportPreviousRead' in patcher.RELEASE_NEW
