from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from tools.shape_ac_spiral_trees import build

ROOT=Path(__file__).resolve().parents[1]


def test_original_256_addresses_and_other_props_survive_three_color_spiral_copy(tmp_path):
    source=ROOT/'xlights_rgbeffects.xml';before=source.read_bytes();target=tmp_path/'layout.xml'
    report=build(source,target)
    assert source.read_bytes()==before
    assert len(report)==27 and len({r['tree'] for r in report})==9
    old={m.get('name'):m for m in ET.fromstring(before).find('models')}
    new={m.get('name'):m for m in ET.parse(target).find('models')}
    assert set(old)==set(new) and len(new)==256
    changed={r['name'] for r in report}
    for name,m in old.items():
        assert new[name].get('StartChannel')==m.get('StartChannel')
        assert new[name].get('StringType')==m.get('StringType')
        if name not in changed:assert ET.tostring(new[name])==ET.tostring(m)
        else:
            assert new[name].get('DisplayAs')=='Custom'
            nodes=new[name].get('CustomModelCompressed').split(';')
            assert {e.split(',')[0] for e in nodes}=={'1'}
            assert len(nodes)==int(m.get('parm2'))
    for i in range(1,10):
        channels={r['start_channel'] for r in report if r['tree']==i}
        assert len(channels)==3
    with pytest.raises(ValueError,match='untouched'):build(source,source)
