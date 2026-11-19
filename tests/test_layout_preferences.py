from pathlib import Path

from core import layout_preferences


def test_remember_and_restore_layout(tmp_path, monkeypatch):
    config = tmp_path / "settings.json"
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text("<xrgb/>", encoding="utf-8")
    monkeypatch.setenv("HELIX_SETTINGS_PATH", str(config))
    assert layout_preferences.load_layout() == ""
    layout_preferences.save_layout(str(layout))
    assert layout_preferences.load_layout() == str(layout.resolve())


def test_missing_layout_is_not_reloaded(tmp_path, monkeypatch):
    config = tmp_path / "settings.json"
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text("<xrgb/>", encoding="utf-8")
    monkeypatch.setenv("HELIX_SETTINGS_PATH", str(config))
    layout_preferences.save_layout(str(layout))
    layout.unlink()
    assert layout_preferences.load_layout() == ""


def test_reject_invalid_layout(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setenv("HELIX_SETTINGS_PATH", str(tmp_path / "settings.json"))
    with pytest.raises(ValueError):
        layout_preferences.save_layout(str(tmp_path / "missing.xml"))
