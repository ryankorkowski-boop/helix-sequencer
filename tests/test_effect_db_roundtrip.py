from __future__ import annotations

import xml.etree.ElementTree as ET

from xlights.xml_io import (
    add_effect,
    effect_palette_text,
    effect_settings_text,
    unresolved_effect_references,
)
from xlights.xsq_writer import EffectTemplate, build_effect_template_library


def _root() -> ET.Element:
    return ET.fromstring(
        """
        <xsequence>
          <ColorPalettes>
            <ColorPalette>C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1</ColorPalette>
          </ColorPalettes>
          <EffectDB>
            <Effect>E_TEXTCTRL_Eff_On_Start=100</Effect>
          </EffectDB>
          <ElementEffects>
            <Element type="model" name="Arch">
              <EffectLayer>
                <Effect ref="0" name="On" startTime="0" endTime="500" palette="0"/>
              </EffectLayer>
            </Element>
          </ElementEffects>
        </xsequence>
        """
    )


def test_every_effect_ref_and_palette_resolves_after_round_trip() -> None:
    root = _root()
    layer = root.find(".//EffectLayer")
    assert layer is not None
    known = EffectTemplate(settings="E_TEXTCTRL_Eff_On_Start=100", palette="C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1")
    added_known = add_effect(layer, 500, 800, "On", known, root=root)
    fresh = EffectTemplate(
        settings="E_CHECKBOX_OverlayBkg=0,E_SLIDER_Brightness=70",
        palette="C_BUTTON_Palette1=#FF0000,C_BUTTON_Palette2=#00FF00,C_CHECKBOX_Palette1=1",
    )
    added_fresh = add_effect(layer, 800, 1200, "Bars", fresh, root=root)

    assert added_known.attrib["ref"] == "0"
    assert added_known.attrib["palette"] == "0"
    assert "settings" not in added_known.attrib
    assert added_fresh.attrib["ref"] == "1"
    assert added_fresh.attrib["palette"] == "1"
    assert effect_settings_text(added_fresh, root) == fresh.settings
    assert effect_palette_text(added_fresh, root) == fresh.palette

    library = build_effect_template_library(root)
    assert library["on"].settings == "E_TEXTCTRL_Eff_On_Start=100"
    assert library["on"].palette == "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
    assert library["bars"].settings == fresh.settings
    assert library["bars"].palette == fresh.palette

    reparsed = ET.fromstring(ET.tostring(root, encoding="unicode"))
    assert unresolved_effect_references(reparsed) == []
    for effect in reparsed.findall(".//ElementEffects//Effect"):
        assert effect.attrib["ref"].isdigit()
        assert effect.attrib["palette"].isdigit()
        assert effect_settings_text(effect, reparsed) is not None
        assert effect_palette_text(effect, reparsed)
