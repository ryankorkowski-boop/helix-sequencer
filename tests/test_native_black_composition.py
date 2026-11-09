import xml.etree.ElementTree as ET

from models.ultimate_showcase import Garden
from tools.build_helpers.ultimate_showcase import model_xml, write_layout
from tools.native_prop_visibility import prepare_review_visibility
from tools.canonical_band_cues import refresh_models


def test_unlit_generated_nodes_do_not_occlude_an_independent_prop(tmp_path):
    garden = Garden()
    for name, color in [('bass', '#FF0000'), ('keys', '#00FF00')]:
        garden.custom(name, [(0,0,0), (1,1,0)], 'STAGE', 'independent notes',
                      [color, color], {'NOTE': [1]})
    garden.models[0].start = 1
    garden.models[1].start = 7
    prepare_review_visibility(garden)
    write_layout(garden, tmp_path, include_demo=False, export_all_custom=True)
    refresh_models(garden, tmp_path/'xlights_rgbeffects.xml')
    models = ET.parse(tmp_path/'xlights_rgbeffects.xml').findall('./models/model')
    assert len(models) == 2
    assert all(m.get('BlackTransparency') == '100' and m.get('Transparency') == '0'
               for m in models)
    assert [m.get('StartChannel') for m in models] == ['1','7']
    assert [m.get('CustomModelCompressed') for m in models] == [
        m.attrs['CustomModelCompressed'] for m in garden.models]


def test_explicit_matte_opacity_remains_owned_by_the_model():
    garden = Garden()
    model = garden.custom('matte', [(0,0,0)], 'STAGE', 'intentional occluder', ['#000000'], {})
    model.attrs.update(BlackTransparency='0', Transparency='35')
    prepare_review_visibility(garden)
    exported = model_xml(model)
    assert exported.get('BlackTransparency') == '0'
    assert exported.get('Transparency') == '35'


def test_legacy_export_keeps_the_original_black_transparency_default():
    garden = Garden()
    model = garden.custom('legacy', [(0,0,0)], 'STAGE', 'retained legacy', ['#FFFFFF'], {})
    assert model_xml(model).get('BlackTransparency') is None
