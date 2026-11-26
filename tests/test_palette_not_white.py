"""Regression: template palette index 0 must not paint the whole sequence white.

xLights paints the ColorPalettes row named by a numeric effect palette. An
inline palette string on the effect is ignored, so a fix that only rewrites
that string still renders palette 0.
"""

import xml.etree.ElementTree as ET
import random

from core.effect_engine import (
    PaletteContext,
    color_palette_table,
    enabled_palette_hexes,
    hex_is_near_white,
    musical_palette_string,
    palette_collapses_to_white,
    palette_for_output,
    pick_palette_for_effect,
    section_hues,
)


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


def _white_sequence() -> ET.Element:
    return ET.fromstring(
        "<xsequence><head></head><ColorPalettes>"
        f"<ColorPalette>{WHITE_ONLY}</ColorPalette>"
        "</ColorPalettes></xsequence>"
    )


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
    root = _white_sequence()
    verse = palette_for_output(
        choice,
        color_palette_table(root),
        section="VERSE",
        effect_index=0,
        effect_name="Bars",
        root=root,
    )
    chorus = palette_for_output(
        choice,
        color_palette_table(root),
        section="CHORUS",
        effect_index=0,
        effect_name="Bars",
        root=root,
    )
    assert verse is not None and verse.isdigit()
    assert chorus is not None and chorus.isdigit()
    assert verse != "0" and chorus != "0"
    assert verse != chorus
    tables = color_palette_table(root)
    for index in (verse, chorus):
        colors = enabled_palette_hexes(tables[int(index)])
        assert len(colors) >= 3
        assert any(not hex_is_near_white(color) for color in colors)
        assert not all(hex_is_near_white(color) for color in colors)


def test_white_is_only_an_accent_on_sparkle_effects():
    bars = musical_palette_string("VERSE", 0, "Bars")
    twinkle = musical_palette_string("VERSE", 0, "Twinkle")
    assert not any(hex_is_near_white(color) for color in enabled_palette_hexes(bars))
    accent = enabled_palette_hexes(twinkle)
    assert any(hex_is_near_white(color) for color in accent)
    assert any(not hex_is_near_white(color) for color in accent)
    root = _white_sequence()
    written = palette_for_output(
        "0",
        color_palette_table(root),
        section="VERSE",
        effect_index=0,
        effect_name="Twinkle",
        root=root,
    )
    assert written is not None and written.isdigit() and written != "0"
    stored = enabled_palette_hexes(color_palette_table(root)[int(written)])
    assert any(hex_is_near_white(color) for color in stored)
    assert any(not hex_is_near_white(color) for color in stored)


def test_distinct_songs_and_layouts_get_distinct_palettes():
    verse_fast = PaletteContext(key_pitch=0, mode="major", energy=0.8, tempo_bpm=132, layout_shift=0)
    chorus_minor = PaletteContext(key_pitch=7, mode="minor", energy=0.4, tempo_bpm=84, layout_shift=0)
    same_song_other_yard = PaletteContext(key_pitch=0, mode="major", energy=0.8, tempo_bpm=132, layout_shift=5)
    first = section_hues("VERSE", 0, verse_fast)
    second = section_hues("VERSE", 0, chorus_minor)
    third = section_hues("VERSE", 0, same_song_other_yard)
    assert first != second
    assert first != third
    for hues in (first, second, third):
        assert len(hues) >= 3
        assert all(not hex_is_near_white(color) for color in hues)
    bars = musical_palette_string("CHORUS", 1, "Bars", same_song_other_yard)
    twinkle = musical_palette_string("CHORUS", 1, "Twinkle", same_song_other_yard)
    assert not any(hex_is_near_white(color) for color in enabled_palette_hexes(bars))
    assert any(hex_is_near_white(color) for color in enabled_palette_hexes(twinkle))
