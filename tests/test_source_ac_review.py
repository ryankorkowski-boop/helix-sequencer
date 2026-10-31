from pathlib import Path
import hashlib
from tools.build_source_ac_review import geometry

ROOT=Path(__file__).resolve().parents[1]


def test_original_addresses_and_fixed_spiral_circuits_remain_literal():
    source=ROOT/'xlights_rgbeffects.xml';before=hashlib.sha256(source.read_bytes()).hexdigest()
    g=geometry(source)
    assert len(g.models)==256 and sum(m.channels for m in g.models)==256
    assert {m.start for m in g.models}==set(range(1,257))
    trees=[m for m in g.models if m.name.startswith('Line Tree ')]
    assert len(trees)==27
    assert all(m.channels==1 and len(m.points)>=25 for m in trees)
    assert all({int(c.split(',')[0]) for c in m.attrs['CustomModelCompressed'].split(';')}=={1} for m in g.models)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before


def test_rgb_additions_never_overlap_original_controller_addresses():
    g=geometry(ROOT/'xlights_rgbeffects.xml',include_rgb=True)
    original=g.models[:256];added=g.models[256:]
    assert {m.start for m in original}==set(range(1,257))
    assert added and min(m.start for m in added)==257
    assert all(m.kind=='pixel' for m in added)
    ranges=[set(range(m.start,m.start+m.channels)) for m in g.models]
    assert sum(map(len,ranges))==len(set.union(*ranges))
