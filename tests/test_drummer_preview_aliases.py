from tools.render_drummer_v3_preview import parse_effects, light_component
from PIL import Image, ImageDraw


def test_current_export_names_are_recognized(tmp_path):
    xsq = tmp_path / "test.xsq"
    xsq.write_text('<xsequence><ElementEffects><Element name="HX_SNOWMAN_DRUMMER_KICK"><EffectLayer><Effect startTime="100" endTime="200"/></EffectLayer></Element></ElementEffects></xsequence>')
    assert parse_effects(xsq) == [(100, 200, "HX_SNOWMAN_DRUMMER_V3_KICK")]


def test_component_light_does_not_brighten_remote_pixels():
    base = Image.new("RGBA", (128, 128), (60, 60, 60, 255))
    mask = Image.new("L", base.size)
    ImageDraw.Draw(mask).rectangle((10, 10, 20, 20), fill=255)
    result = light_component(base, mask, 1)
    assert result.getpixel((127, 127)) == base.getpixel((127, 127))
    assert result.getpixel((15, 15))[0] > 60


def test_preview_reads_independent_snare_hand_masks(tmp_path):
    xsq = tmp_path / "hands.xsq"
    xsq.write_text('<xsequence><ElementEffects><Element name="HX_SNOWMAN_DRUMMER_SNARE"><EffectLayer><Effect startTime="100" endTime="200" sourceHand="L"/><Effect startTime="300" endTime="400" sourceHand="R"/></EffectLayer></Element></ElementEffects></xsequence>')
    hands = [event for event in parse_effects(xsq, include_hands=True) if event[2].startswith("SNARE_HAND_")]
    assert hands == [(100, 200, "SNARE_HAND_L"), (300, 400, "SNARE_HAND_R")]


def test_strike_light_decays_and_respects_rest():
    from tools.render_drummer_v3_preview import strike_intensity
    assert strike_intensity(100, 200, 99) == 0
    assert strike_intensity(100, 200, 100) == 1
    assert strike_intensity(100, 200, 150) == .25
    assert strike_intensity(100, 200, 200) == 0


def test_active_frame_sweep_matches_full_history_scan():
    from tools.render_drummer_v3_preview import active_frames, strike_intensity
    events = [(0, 120, "a"), (25, 80, "b"), (70, 200, "a"), (300, 400, "b"), (10, 20, "unknown")]
    times = range(0, 500, 13)
    for time, active in active_frames(events, times, ("a", "b")):
        expected = {name: max([0.0] + [strike_intensity(start, end, time) for start, end, target in events if target == name]) for name in ("a", "b")}
        assert active == expected


def test_prepared_frame_assets_preserve_pixels():
    from PIL import Image, ImageFont
    from tools.render_drummer_v3_preview import draw_frame, prepare_frame_assets
    source = Image.new("RGBA", (160, 120), (20, 30, 40, 255))
    masks = {"test": Image.new("L", source.size, 128)}
    args = (source, masks, {"test": .7}, 480, 270, 100, 1000, ImageFont.load_default())
    expected = draw_frame(*args)
    actual = draw_frame(*args, prepared=prepare_frame_assets(source, masks, 480, 270))
    assert actual.tobytes() == expected.tobytes()
