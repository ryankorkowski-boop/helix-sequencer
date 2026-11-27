"""Prevent nonmusical periodic illumination in native owner review exports."""
from types import SimpleNamespace
import xml.etree.ElementTree as ET

from tools.phoneme_vocal_export import export_static_materials


def test_static_material_is_one_constant_effect_not_400ms_pulses():
    root = ET.fromstring('<xsequence><DisplayElements/><ElementEffects/></xsequence>')
    model = SimpleNamespace(name='HX_SNOW_DRUMMER', submodels={'STATIC_RGB_90A0B0': [1, 2]})
    export_static_materials(root, SimpleNamespace(models=[model]), 30000)
    elements = root.findall('./ElementEffects/Element/EffectLayer/Effect')
    assert len(elements) == 1
    effect = elements[0]
    assert effect.get('startTime') == '0'
    assert effect.get('endTime') == '30000'
    assert 'Start=90' in effect.get('settings', '')
    assert 'End=90' in effect.get('settings', '')
