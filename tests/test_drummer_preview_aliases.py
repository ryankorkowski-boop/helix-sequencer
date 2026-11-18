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
