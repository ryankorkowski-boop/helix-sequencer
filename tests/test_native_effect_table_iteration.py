import xml.etree.ElementTree as ET

from xlights.xml_io import materialize_native_effect_tables


def test_native_effect_table_iteration_preserves_order_and_ids():
    root = ET.fromstring("""
    <xsequence>
      <ElementEffects>
        <Element type="timing"><EffectLayer><Effect id="99"/></EffectLayer></Element>
        <Element type="model">
          <EffectLayer>
            <Effect id="8" settings="alpha" startTime="0" endTime="50"/>
            <Effect settings="beta" palette="red" startTime="50" endTime="100"/>
          </EffectLayer>
          <SubModelEffectLayer><Effect settings="alpha" palette="red"/></SubModelEffectLayer>
          <OtherLayer><Effect settings="ignored"/></OtherLayer>
        </Element>
      </ElementEffects>
    </xsequence>
    """)
    result = materialize_native_effect_tables(root)
    assert result == {"settings_added": 2, "palettes_added": 2, "effects": 3}
    assert [e.text for e in root.findall("./EffectDB/Effect")] == ["alpha", "beta"]
    assert [e.text for e in root.findall("./ColorPalettes/ColorPalette")] == [
        "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1", "red"
    ]
    model = root.findall("./ElementEffects/Element")[1]
    effects = model.findall("./EffectLayer/Effect") + model.findall("./SubModelEffectLayer/Effect")
    assert [e.get("id") for e in effects] == ["8", "9", "10"]
    assert [e.get("ref") for e in effects] == ["0", "1", "0"]
    assert [e.get("palette") for e in effects] == [None, "1", "1"]
    assert effects[0].get("startTime") == "0"
    assert effects[1].get("endTime") == "100"
    assert root.findtext("nextid") == "11"
    assert root.find("./ElementEffects/Element/EffectLayer/Effect").get("ref") is None
    assert model.find("./OtherLayer/Effect").get("ref") is None


def test_empty_native_model_effects():
    root = ET.fromstring("<xsequence><ElementEffects/></xsequence>")
    assert materialize_native_effect_tables(root) == {
        "settings_added": 0, "palettes_added": 0, "effects": 0
    }
    assert root.findtext("nextid") == "1"
