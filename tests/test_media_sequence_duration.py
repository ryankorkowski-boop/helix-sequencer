"""Changing songs must change native export length, including a shorter song."""
import xml.etree.ElementTree as ET

import pytest

from xlights.xml_io import set_sequence_duration, bound_media_effects


@pytest.mark.parametrize('template_length,audio_length,expected', [
    ('132.039', 260.2, '260.200'), ('500', 36., '36.000'),
    ('36', 36.00001, '36.000'), ('1', .0041, '0.004'),
])
def test_decoded_audio_replaces_template_duration_without_changing_effects(
        template_length, audio_length, expected):
    root = ET.fromstring('<xsequence><head><sequenceType>Animation</sequenceType>'
        f'<sequenceDuration>{template_length}</sequenceDuration><sequenceTiming>50 ms</sequenceTiming>'
        '<mediaFile>sampler.mp3</mediaFile></head><ElementEffects><Element name="Roof">'
        '<EffectLayer><Effect startTime="250000" endTime="260200"/></EffectLayer>'
        '</Element></ElementEffects></xsequence>')
    retained = ET.tostring(root.find('ElementEffects'))
    assert set_sequence_duration(root, audio_length) == round(float(expected) * 1000)
    assert root.findtext('head/sequenceDuration') == expected
    assert root.findtext('head/sequenceType') == 'Media'
    assert root.findtext('head/sequenceTiming') == '50 ms'
    assert root.findtext('head/mediaFile') == 'sampler.mp3'
    assert ET.tostring(root.find('ElementEffects')) == retained


def test_duration_can_create_a_missing_namespaced_head():
    root = ET.Element('{urn:xlights}xsequence')
    set_sequence_duration(root, 2.5)
    assert root.findtext('{urn:xlights}head/{urn:xlights}sequenceDuration') == '2.500'
    assert root.find('head') is None


@pytest.mark.parametrize('duration', [0, -1, float('nan'), float('inf')])
def test_bad_duration_leaves_sequence_untouched(duration):
    root = ET.fromstring('<xsequence><head><sequenceDuration>132.039</sequenceDuration></head></xsequence>')
    retained = ET.tostring(root)
    with pytest.raises(ValueError, match='duration'):
        set_sequence_duration(root, duration)
    assert ET.tostring(root) == retained


def test_generator_tail_stops_at_audio_end_and_interior_cues_are_unchanged():
    root = ET.fromstring('<xsequence><EffectDB><Effect>config</Effect></EffectDB>'
        '<ElementEffects><Element name="Roof"><EffectLayer>'
        '<Effect startTime="100" endTime="200" name="On"/>'
        '<Effect startTime="260150" endTime="260290" name="On"/>'
        '<Effect startTime="260200" endTime="260350" name="On"/>'
        '</EffectLayer></Element><Element type="timing"><EffectLayer>'
        '<Effect startTime="-10" endTime="50" label="Beat"/>'
        '</EffectLayer></Element></ElementEffects></xsequence>')
    interior = ET.tostring(root.find('.//EffectLayer/Effect'))
    assert bound_media_effects(root, 260200) == {'trimmed': 2, 'removed': 1}
    effects = root.findall('.//EffectLayer/Effect')
    assert len(effects) == 3
    assert ET.tostring(effects[0]) == interior
    assert [(int(e.get('startTime')), int(e.get('endTime'))) for e in effects] == [
        (100, 200), (260150, 260200), (0, 50)]
    assert root.findtext('EffectDB/Effect') == 'config'
