import pytest
from core.effects_orchestrator_bridge import _layout_file_from_args

def test_no_explicit_layout():
    assert _layout_file_from_args([]) is None

def test_missing_explicit_layout(tmp_path):
    with pytest.raises(ValueError, match="not a file"):
        _layout_file_from_args(["--layout-file", str(tmp_path / "missing.xml")])

def test_directory_is_not_layout(tmp_path):
    with pytest.raises(ValueError, match="not a file"):
        _layout_file_from_args(["--layout-file", str(tmp_path)])

def test_existing_layout_path(tmp_path):
    path = tmp_path / "layout.xml"
    path.write_text("<xrgb/>")
    assert _layout_file_from_args(["--layout-file", str(path)]) == path
