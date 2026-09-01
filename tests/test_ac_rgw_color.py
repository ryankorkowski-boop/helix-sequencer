from core.ac_rgw_color import RGWIntensity, nearest_rgw_palette, quantize_rgb_to_rgw


def test_quantizer_keeps_three_independent_ac_channels():
    value = quantize_rgb_to_rgw(1.0, 0.0, 0.0)
    assert isinstance(value, RGWIntensity)
    assert value.red > 0.9
    assert value.green == 0
    assert 0 <= value.white <= 1


def test_white_highlight_can_use_white_channel():
    value = quantize_rgb_to_rgw(1.0, 1.0, 1.0)
    assert value.white > 0
    assert value.red > 0
    assert value.green > 0


def test_nearest_palette_is_deterministic():
    assert nearest_rgw_palette((255, 0, 0)) == RGWIntensity(1, 0, 0)
    assert nearest_rgw_palette((0, 255, 0)) == RGWIntensity(0, 1, 0)
