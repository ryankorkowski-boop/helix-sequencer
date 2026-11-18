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
