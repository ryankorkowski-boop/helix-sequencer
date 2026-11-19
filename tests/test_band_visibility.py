from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from core.band_visibility import apply, is_band_model

ROOT = Path(__file__).resolve().parents[1]


def test_enabled_preserves_actual_layout_bytes(tmp_path):
    layout = tmp_path/'layout.xml'
    shutil.copyfile(ROOT/'helixville4/xlights_rgbeffects.xml', layout)
    before = layout.read_bytes()
    assert apply(layout, enabled=True)['removed_models'] == []
    assert layout.read_bytes() == before


def test_disabled_removes_real_band_preserving_every_other_prop_and_address(tmp_path):
    layout = tmp_path/'layout.xml'
    shutil.copyfile(ROOT/'helixville4/xlights_rgbeffects.xml', layout)
    before = ET.parse(layout).findall('./models/model')
    retained = {m.get('name'): dict(m.attrib) for m in before if not is_band_model(m)}
    report = apply(layout, enabled=False)
    assert 'HX_SNOWMAN_DRUMMER_BODY' in report['removed_models']
    after = ET.parse(layout).findall('./models/model')
    assert {m.get('name'): dict(m.attrib) for m in after} == retained
    assert not any(is_band_model(m) for m in after)
    assert 'HX_SNOWMAN_BAND_STAGE_CUSTOM' in retained


def test_nested_groups_and_template_cannot_reintroduce_hidden_band(tmp_path):
    layout = tmp_path/'layout.xml'
    layout.write_text('<xrgb><models><model name="HX_SNOW_LEAD"/>'
        '<model name="Generic singing face" StartChannel="37"/></models><modelGroups>'
        '<modelGroup name="All" models="Band,Generic singing face"/>'
        '<modelGroup name="Band" models="HX_SNOW_LEAD/MOUTH_AI"/>'
        '</modelGroups></xrgb>')
    template = tmp_path/'template.xsq'
    template.write_text('<xsequence><DisplayElements><Element name="Band"/>'
        '<Element name="Generic singing face"/></DisplayElements><ElementEffects>'
        '<Element name="HX_SNOW_LEAD/MOUTH_AI"/><Element name="Generic singing face"/>'
        '</ElementEffects></xsequence>')
    report = apply(layout, template, enabled=False)
    assert report['removed_empty_groups'] == ['Band']
    assert ET.parse(layout).find('./modelGroups/modelGroup').get('models') == 'Generic singing face'
    assert report['removed_template_rows'] == 2
    assert [e.get('name') for e in ET.parse(template).find('ElementEffects')] == ['Generic singing face']
