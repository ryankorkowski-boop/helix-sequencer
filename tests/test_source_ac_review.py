from pathlib import Path
import hashlib
from tools.build_source_ac_review import ACTIVE_AC_CHANNELS, RETIRED_APEX_CHANNELS, geometry

ROOT=Path(__file__).resolve().parents[1]


def test_original_addresses_and_fixed_spiral_circuits_remain_literal():
    source=ROOT/'xlights_rgbeffects.xml';before=hashlib.sha256(source.read_bytes()).hexdigest()
    g=geometry(source)
    assert len(g.models)==252 and sum(m.channels for m in g.models)==252
    assert {m.start for m in g.models}==set(ACTIVE_AC_CHANNELS)
    assert RETIRED_APEX_CHANNELS.isdisjoint(m.start for m in g.models)
    arches={}
    for model in g.models:
        if model.name.startswith("Arch ") and " Sec " in model.name:
            arch, sec = model.name.split(" Sec ")
            arches.setdefault(arch, set()).add(int(sec))
    assert set(arches)=={f"Arch {i}" for i in range(1,5)}
    assert all(secs=={1,2,3,4,6,7,8,9} for secs in arches.values())
    starts={model.name: model.start for model in g.models}
    assert starts["Arch 1 Sec 1"]==129 and starts["Arch 1 Sec 6"]==134
    assert starts["Arch 4 Sec 6"]==2 and starts["Arch 4 Sec 9"]==25
    trees=[m for m in g.models if m.name.startswith('Line Tree ')]
    assert len(trees)==27
    assert all(m.channels==1 and len(m.points)>=25 for m in trees)
    assert all({int(c.split(',')[0]) for c in m.attrs['CustomModelCompressed'].split(';')}=={1} for m in g.models)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before


def test_rgb_additions_never_overlap_original_controller_addresses():
    g=geometry(ROOT/'xlights_rgbeffects.xml',include_rgb=True)
    original=g.models[:252];added=g.models[252:]
    assert {m.start for m in original}==set(ACTIVE_AC_CHANNELS)
    assert added and min(m.start for m in added)==257
    assert all(m.kind=='pixel' for m in added)
    ranges=[set(range(m.start,m.start+m.channels)) for m in g.models]
    assert sum(map(len,ranges))==len(set.union(*ranges))
    assert RETIRED_APEX_CHANNELS.isdisjoint(set.union(*ranges))
