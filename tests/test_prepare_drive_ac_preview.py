from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from core.model_parser import parse_layout
from tools.phoneme_source import digest
from tools.prepare_drive_ac_preview import prepare

ROOT = Path(__file__).resolve().parents[1]


def test_native_preview_preserves_all_circuits_groups_and_sequence_bytes(tmp_path):
    source = ROOT / 'xlights_rgbeffects.xml'
    sequence = tmp_path / 'sequence.xsq'
    root = ET.Element('xsequence')
    effects = ET.SubElement(root, 'ElementEffects')
    original_tree = ET.parse(source)
    group = original_tree.find('modelGroups/modelGroup').get('name')
    for name in (original_tree.find('models/model').get('name'), group):
        element = ET.SubElement(effects, 'Element', type='model', name=name)
        ET.SubElement(ET.SubElement(element, 'EffectLayer'), 'Effect', name='On', startTime='113', endTime='137')
    ET.ElementTree(root).write(sequence)
    before = digest(source), digest(sequence)
    output = tmp_path / 'show'
    receipt = prepare(source, sequence, output)
    original, preview = [{n: m for n, m in parse_layout(p).models.items() if not m.is_submodel}
                         for p in (source, output / 'xlights_rgbeffects.xml')]
    assert set(preview) == set(original)
    assert {m.start_channel for m in preview.values()} == set(range(1, 257))
    for name, m in original.items():
        assert preview[name].start_channel == m.start_channel
        assert preview[name].is_single_color()
        if m.color_family in {'red', 'green', 'white'}:
            assert preview[name].color_family == m.color_family
    assert ET.tostring(ET.parse(source).find('modelGroups')) == ET.tostring(
        ET.parse(output / 'xlights_rgbeffects.xml').find('modelGroups'))
    assert (digest(source), digest(sequence)) == before
    assert receipt['musical_effects_unchanged']
    assert not list(output.glob('*Showcase.xsq'))
    # Legacy RGB/intensity metadata receives the existing AC preview mapping;
    # disclose every such fallback instead of claiming surveyed physical colors.
    assert any(m['name'] == 'merRy christmas 4' for m in receipt['inherited_preview_color_fallbacks'])


def test_unknown_sequence_model_cannot_silently_disappear(tmp_path):
    sequence = tmp_path / 'foreign.xsq'
    sequence.write_text('<xsequence><ElementEffects><Element type="model" name="foreign"><EffectLayer><Effect name="On"/></EffectLayer></Element></ElementEffects></xsequence>')
    with pytest.raises(ValueError, match='outside the original'):
        prepare(ROOT / 'xlights_rgbeffects.xml', sequence, tmp_path / 'show')
