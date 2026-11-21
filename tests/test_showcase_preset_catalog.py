"""Ensure all nine showcase-era presets ship as real selectable native layouts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = ROOT / "config/gui_options.json"

SHOWCASE_KEYS = (
    "ac16", "ac64", "greg256", "pixel_starter", "pixel_classic",
    "band_stage_bench", "wow_moire", "wow_spirals", "wow_showcase",
)


def test_nine_showcase_preset_keys_resolve_to_real_layouts():
    options = json.loads(OPTIONS.read_text(encoding="utf-8"))
    catalog = options["layouts"] + options["stages"]
    keys = [item["key"] for item in catalog]
    assert len(keys) == len(set(keys))
    assert set(SHOWCASE_KEYS).issubset(keys)
    for key in SHOWCASE_KEYS:
        item = next(item for item in catalog if item["key"] == key)
        layout = ROOT / item["path"]
        assert layout.is_file(), (key, layout)
        assert "<" in layout.read_text(encoding="utf-8")[:300]


def test_shared_catalog_is_used_by_android_and_desktop():
    android = (ROOT / "android/app/src/main/java/org/helixsequencer/android/UiOptions.java").read_text(encoding="utf-8")
    desktop = (ROOT / "core/gui_options.py").read_text(encoding="utf-8")
    staging = (ROOT / "tools/stage_android_engine.py").read_text(encoding="utf-8")
    assert 'getAssets().open("gui-options.json")' in android
    assert 'config/gui_options.json' in desktop
    assert "sample_paths = {item['path'] for item in options['layouts'] + options['stages']}" in staging
