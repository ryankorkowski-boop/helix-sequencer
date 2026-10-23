import xml.etree.ElementTree as ET
import pytest
from xlights.xml_io import materialize_native_effect_tables


def test_inline_native_settings_and_colors_survive_serialization_without_retiming():
    root = ET.fromstring('<xsequence><ElementEffects><Element type="model" name="Singer"><EffectLayer>'
        '<Effect name="Faces" startTime="113" endTime="137" settings="E_CHOICE_Faces_Phoneme=E" palette="C_BUTTON_Palette1=#632D98,C_CHECKBOX_Palette1=1"/>'
        '</EffectLayer></Element><Element type="timing"><EffectLayer><Effect label="source" startTime="113" endTime="137"/></EffectLayer></Element></ElementEffects></xsequence>')
    effect = root.find('./ElementEffects/Element/EffectLayer/Effect')
    report = materialize_native_effect_tables(root)
    assert report['effects'] == 1
    assert (effect.get('name'), effect.get('startTime'), effect.get('endTime')) == ('Faces', '113', '137')
    assert root.findall('EffectDB/Effect')[int(effect.get('ref'))].text == 'E_CHOICE_Faces_Phoneme=E'
    assert '#632D98' in root.findall('ColorPalettes/ColorPalette')[int(effect.get('palette'))].text
    assert effect.get('settings') == 'E_CHOICE_Faces_Phoneme=E'
    previous = ET.tostring(root)
    materialize_native_effect_tables(root)
    assert ET.tostring(root) == previous


def test_duplicate_imported_tables_keep_indices_and_append_at_real_length():
    root = ET.fromstring('<xsequence><ColorPalettes><ColorPalette>old</ColorPalette><ColorPalette>old</ColorPalette></ColorPalettes>'
        '<EffectDB><Effect>old</Effect><Effect>old</Effect></EffectDB><ElementEffects><Element type="model"><EffectLayer>'
        '<Effect name="On" startTime="0" endTime="100" ref="0" palette="0" id="7"/>'
        '<Effect name="On" startTime="100" endTime="200" settings="new" palette="new"/>'
        '</EffectLayer></Element></ElementEffects></xsequence>')
    materialize_native_effect_tables(root)
    old, new = root.findall('./ElementEffects/Element/EffectLayer/Effect')
    assert old.get('ref') == old.get('palette') == '0'
    assert new.get('ref') == new.get('palette') == '2'
    assert old.get('id') == '7' and new.get('id') == '8'


@pytest.mark.parametrize('attribute', ['ref', 'palette'])
def test_missing_native_table_reference_does_not_silently_render_white(attribute):
    root = ET.fromstring(f'<xsequence><ElementEffects><Element type="model"><EffectLayer><Effect name="On" {attribute}="9"/></EffectLayer></Element></ElementEffects></xsequence>')
    with pytest.raises(ValueError, match='Invalid native'):
        materialize_native_effect_tables(root)


def test_native_serialization_preserves_missing_palette_for_explicit_neon_postpass(tmp_path):
    from tools.xsq_palette_repair import repair_xsq
    root = ET.fromstring('<xsequence><head><sequenceDuration>1</sequenceDuration></head><ElementEffects><Element type="model" name="Tree"><EffectLayer>'
        '<Effect name="On" startTime="100" endTime="200"/></EffectLayer></Element></ElementEffects></xsequence>')
    materialize_native_effect_tables(root)
    effect = root.find('./ElementEffects/Element/EffectLayer/Effect')
    assert effect.get('palette') is None
    assert '#FFFFFF' in root.findtext('ColorPalettes/ColorPalette')
    source, output = tmp_path/'source.xsq', tmp_path/'neon.xsq'
    ET.ElementTree(root).write(source)
    report = repair_xsq(source, output)
    assert report['changes']['palettes_assigned'] == 1
    result = ET.parse(output)
    assigned = result.find('./ElementEffects/Element/EffectLayer/Effect').get('palette')
    assert '#FF2ED1' in result.findall('ColorPalettes/ColorPalette')[int(assigned)].text


def test_native_template_import_resolves_authoritative_settings_and_color_tables(tmp_path):
    from xlights.xsq_writer import load_xsq, build_effect_template_library
    root = ET.fromstring('<xsequence><EffectDB><Effect>E_TEXTCTRL_Eff_On_Start=70</Effect></EffectDB>'
        '<ColorPalettes><ColorPalette>C_BUTTON_Palette1=#632D98,C_CHECKBOX_Palette1=1</ColorPalette></ColorPalettes>'
        '<ElementEffects><Element type="model" name="Singer"><EffectLayer>'
        '<Effect name="On" startTime="0" endTime="100" ref="0" palette="0" settings="stale inline setting"/>'
        '</EffectLayer></Element></ElementEffects></xsequence>')
    path = tmp_path/'native.xsq'
    ET.ElementTree(root).write(path)
    parsed = load_xsq(path)
    assert parsed.on_tpl.settings == 'E_TEXTCTRL_Eff_On_Start=70'
    assert '#632D98' in parsed.on_tpl.palette
    library = build_effect_template_library(root)
    assert library['on'].settings == parsed.on_tpl.settings
    assert library['on'].palette == parsed.on_tpl.palette
