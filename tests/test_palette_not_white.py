"""Regression: template palette index 0 must not paint the whole sequence white."""

from core.effect_engine import (
    enabled_palette_hexes,
    hex_is_near_white,
    musical_palette_string,
    palette_collapses_to_white,
    palette_for_output,
    pick_palette_for_effect,
)
import random


WHITE_ONLY = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
CHRISTMAS = (
    "C_BUTTON_Palette1=#FF0000,C_BUTTON_Palette2=#00FF00,C_BUTTON_Palette3=#FFFFFF,"
    "C_CHECKBOX_Palette1=1,C_CHECKBOX_Palette2=1,C_CHECKBOX_Palette3=1"
)


def test_template_index_zero_is_white_only():
    assert palette_collapses_to_white("0", [WHITE_ONLY, CHRISTMAS])
    assert enabled_palette_hexes(WHITE_ONLY) == ["#FFFFFF"]
    assert hex_is_near_white("#FFFFFF")
    assert not hex_is_near_white("#DC2626")


def test_checked_chromatic_palette_is_kept():
    assert not palette_collapses_to_white(CHRISTMAS, [])
    kept = palette_for_output(CHRISTMAS, [], section="VERSE", effect_index=0, effect_name="Bars")
    assert kept == CHRISTMAS


def test_white_template_palette_is_replaced_with_section_hues():
    choice = pick_palette_for_effect(
        mode="template",
        template_palette="0",
        template_pool=["0"],
        history_pool=[],
        rng=random.Random(1),
        effect_index=0,
    )
    assert choice == "0"
    verse = palette_for_output(choice, [WHITE_ONLY], section="VERSE", effect_index=0, effect_name="Bars")
    chorus = palette_for_output(choice, [WHITE_ONLY], section="CHORUS", effect_index=0, effect_name="Bars")
    assert verse != chorus
    for palette in (verse, chorus):
        colors = enabled_palette_hexes(palette)
        assert len(colors) >= 3
        assert not all(hex_is_near_white(color) for color in colors)
        assert any(not hex_is_near_white(color) for color in colors)


def test_white_is_only_an_accent_on_sparkle_effects():
    bars = musical_palette_string("VERSE", 0, "Bars")
    twinkle = musical_palette_string("VERSE", 0, "Twinkle")
    assert not any(hex_is_near_white(color) for color in enabled_palette_hexes(bars))
    accent = enabled_palette_hexes(twinkle)
    assert any(hex_is_near_white(color) for color in accent)
    assert any(not hex_is_near_white(color) for color in accent)
