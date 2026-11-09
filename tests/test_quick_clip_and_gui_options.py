"""Exercise real shortened input, shared choices and independent face ownership."""
from pathlib import Path
import hashlib
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pytest
import soundfile as sf

from core.gui_options import OPTIONS, PALETTES, layout_options, palette_key, resolve_layout
from core.quick_clip import prepare_quick_clip
from core.snowman_band import preferred_face_routing, _face_target_for_instruction
from tools.desktop_remote import settings
from tools.desktop_remote_worker import build_args as remote_args

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "android/app/src/main/python"))
from helix_mobile import build_args as mobile_args


@pytest.mark.parametrize("seconds", [2, 13])
def test_quick_clip_preserves_samples_and_original_song(tmp_path, seconds):
    rate = 8000
    samples = np.random.default_rng(82).uniform(-.5, .5, (rate * seconds, 2)).astype("float32")
    source = tmp_path / "original.wav"
    sf.write(source, samples, rate, subtype="FLOAT")
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    clip = prepare_quick_clip(source, tmp_path / "outputs")
    actual, actual_rate = sf.read(clip, dtype="float32", always_2d=True)
    assert actual_rate == rate
    np.testing.assert_array_equal(actual, samples[:rate * 10])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original
    assert clip.with_suffix(".json").is_file()
    repeated = prepare_quick_clip(source, tmp_path / "outputs")
    assert repeated.stem == clip.stem and repeated.parent != clip.parent
    # libsndfile embeds a wall-clock timestamp in the WAV PEAK metadata chunk.
    # Two lossless clips can have identical audio but different file bytes when
    # written across a one-second boundary. Compare the audio payload instead.
    repeated_samples, repeated_rate = sf.read(repeated, dtype="float32", always_2d=True)
    assert repeated_rate == actual_rate
    np.testing.assert_array_equal(repeated_samples, actual)
    assert sf.info(repeated).subtype == sf.info(clip).subtype


def test_all_sample_choices_resolve_to_existing_native_layouts():
    assert {choice['key'] for choice in OPTIONS['layouts']} == {
        'greg256','helixville2','allmodels','helixville3','aurora','helixville4','greg256_spirals'}
    assert len(OPTIONS["stages"]) == 3
    for item in layout_options():
        layout = resolve_layout(ROOT, item["key"])
        assert ET.parse(layout).getroot().findall("./models/model"), item["key"]
    assert OPTIONS["default_layout"] == "helixville4"
    with pytest.raises(ValueError): resolve_layout(ROOT, "../../etc/passwd")


@pytest.mark.parametrize("palette", list(PALETTES.values()))
def test_phone_and_remote_reach_existing_engine_palette_and_quick_flag(tmp_path, palette):
    (tmp_path / "input").mkdir()
    request = {"palette": palette, "quick_clip": True, "preview_seconds": 30}
    assert settings(request)["quick_clip"] is True
    for args in (mobile_args(request, tmp_path, ROOT), remote_args(request, tmp_path)):
        assert "--helix-quick-clip" in args
        if palette != "default": assert args[args.index("--palette-mode") + 1] == palette
    assert palette_key(palette) == palette


def test_imported_layout_wins_over_sample_and_ac_ignores_rgb_palette(tmp_path):
    (tmp_path / "input").mkdir()
    imported = tmp_path / "input/xlights_rgbeffects.xml"
    request = {"sample_layout": "helixville4", "palette": "warm", "ac_compatible": True}
    args = mobile_args(request, tmp_path, ROOT)
    assert Path(args[args.index("--layout-file") + 1]) == resolve_layout(ROOT, "helixville4")
    imported.write_text("<xrgb/>")
    args = mobile_args(request, tmp_path, ROOT)
    assert Path(args[args.index("--layout-file") + 1]) == imported
    assert "--palette-mode" not in args


def test_harmony_has_stable_distinct_target_and_never_borrows_only_lead():
    routing = preferred_face_routing(["HX_SNOW_HARMONY", "HX_SNOW_LEAD", "Matrix"])
    assert routing["preferred_lead"] == "HX_SNOW_LEAD"
    for time in (0, 200, 700, 1900):
        assert _face_target_for_instruction({"performer": "female_singer", "start_ms": time}, routing) == "HX_SNOW_HARMONY"
    only_lead = preferred_face_routing(["HX_SNOW_LEAD", "Matrix"])
    assert _face_target_for_instruction({"performer": "female_singer"}, only_lead) == ""


def test_replacing_equals_audio_option_removes_the_original_value():
    from core.sequence_builder import _set_or_replace_arg
    assert _set_or_replace_arg(["--audio=original.mp3", "--variants", "1"], "--audio", "clip.wav") == ["--audio", "clip.wav", "--variants", "1"]


@pytest.mark.parametrize("value", [{"quick_clip": "yes"}, {"sample_layout": "../../etc/passwd"}, {"palette": "fake"}])
def test_remote_rejects_invalid_new_options(value):
    with pytest.raises(ValueError): settings(value)
