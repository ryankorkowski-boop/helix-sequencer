from __future__ import annotations
import hashlib
import json
import xml.etree.ElementTree as ET

from tools.build_infinity_showcase_layout import FAMILIES, make_layout

def test_extreme_scale_has_2048_models_and_overlapping_groups(tmp_path):
    xml=tmp_path/'full.xml'
    manifest=tmp_path/'full.json'
    meta=make_layout(xml,manifest,2048)
    assert meta['model_count']==2048
    assert meta['group_count']>2048
    assert meta['pixel_count']>100_000
    assert meta['rgb_channel_count']==3*meta['pixel_count']
    root=ET.parse(xml).getroot()
    assert len(root.findall('./models/model'))==2048
    assert len(root.findall('./modelGroups/modelGroup'))==meta['group_count']
    assert len(meta['families'])==len(FAMILIES)
    assert manifest.exists()
    assert meta['sha256']==hashlib.sha256(xml.read_bytes()).hexdigest()

def test_channel_allocation_is_gapless_unique_and_rgb_aligned(tmp_path):
    meta=make_layout(tmp_path/'a.xml',tmp_path/'a.json',512)
    rows=meta['channel_map']
    assert rows[0]['start_channel']==1
    for a,b in zip(rows,rows[1:]):
        assert a['end_channel']+1==b['start_channel']
    assert rows[-1]['end_channel']==meta['rgb_channel_count']
    assert all((r['end_channel']-r['start_channel']+1)==3*r['nodes'] for r in rows)

def test_geometry_is_truly_volumetric_and_reproducible(tmp_path):
    a=tmp_path/'a.xml'
    b=tmp_path/'b.xml'
    one=make_layout(a,tmp_path/'a.json',128)
    two=make_layout(b,tmp_path/'b.json',128)
    assert one['sha256']==two['sha256']
    root=ET.parse(a).getroot()
    names={m.get('name'):m for m in root.findall('./models/model')}
    for family in ('VOXEL_GRID_3D','TUNNEL_3D','DOUBLE_HELIX'):
        m=next(v for k,v in names.items() if family in k)
        coords=[float(x) for x in m.get('PointData').split(',')]
        zs=coords[2::3]
        assert max(zs)-min(zs)>10
        assert int(m.get('parm2'))==len(zs)
    known=set(names)
    group_names={g.get("name") for g in root.findall("./modelGroups/modelGroup")}
    assert all(set(g.get("models").split(","))<=(known|group_names) for g in root.findall("./modelGroups/modelGroup"))
    districts=next(g for g in root.findall("./modelGroups/modelGroup") if g.get("name")=="HX_INFINITY_DISTRICTS")
    assert set(districts.get("models").split(","))=={f"HX_INFINITY_FAMILY_{family}" for family, *_ in FAMILIES}
    face=next(v for k,v in names.items() if "SINGING_FACE" in k)
    assert {child.get("name") for child in face.findall("subModel")}=={"Mouth","Eyes"}


def test_magical_extreme_scale(tmp_path):
    meta=make_layout(tmp_path/'extreme.xml',tmp_path/'extreme.json',10240)
    assert meta['model_count']==10240
    assert meta['pixel_count']==790080
    assert meta['rgb_channel_count']==2370240
    root=ET.parse(tmp_path/'extreme.xml').getroot()
    groups=root.findall('./modelGroups/modelGroup')
    assert sum(g.get('name','').startswith('HX_INFINITY_MAGIC_') for g in groups)==6
    assert len({r['name'] for r in meta['channel_map']})==10240
