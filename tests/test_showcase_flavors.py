import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import zipfile

import numpy as np
import pytest

from models.showcase_flavors import FLAVORS, build_flavor
from models.ultimate_showcase import NATIVE_TYPES, family, build_ultimate_garden
from tools.build_helpers.ultimate_showcase import write_layout


@pytest.fixture(scope="module",params=[f.key for f in FLAVORS])
def exported(request,tmp_path_factory):
    g=build_flavor(request.param);path=tmp_path_factory.mktemp(g.slug);write_layout(g,path)
    return request.param,g,path,ET.parse(path/"xlights_rgbeffects.xml").getroot()


def test_each_flavor_has_all_native_families_and_many_genuine_sculptures(exported):
    _,g,path,root=exported
    assert {family(m.get("DisplayAs")) for m in root.findall("models/model")}==set(NATIVE_TYPES)
    assert len({m.name for m in g.models})==len(g.models)
    assert sum(bool(m.details.get("spiral_tree")) for m in g.models)>=36
    assert sum(bool(m.details.get("double_helix")) for m in g.models)>=12
    assert len(list((path/"models").glob("*.xmodel")))>=12
    for m in g.models:
        assert np.isfinite(m.points).all() and m.points[:,1].min()>=-1e-6
        assert np.abs(m.points[:,0]).max()<205


def test_affine_moves_reach_native_custom_vertices_lines_and_channels(exported):
    _,g,_,root=exported;start=1
    for m,node in zip(g.models,root.findall("models/model"),strict=True):
        assert int(node.get("StartChannel"))==start and node.get("Controller")=="";start+=m.channels
        if m.display=="Custom":
            cells=np.array([[int(v) for v in e.split(",")] for e in node.get("CustomModelCompressed").split(";")])
            assert len(set(map(tuple,cells[:,1:])))==len(cells)
            rows,cols,layers=cells[:,1],cells[:,2],cells[:,3]
            raw=np.c_[cols-(cols.min()+cols.max())/2,(rows.min()+rows.max())/2-rows,(layers.min()+layers.max())/2-layers]
            anchor=np.array([float(node.get("WorldPos"+k)) for k in "XYZ"])
            scale=np.array([float(node.get("Scale"+k)) for k in "XYZ"])
            np.testing.assert_allclose(raw*scale+anchor,m.points,atol=2e-6)
        elif m.display=="MultiPoint":
            points=np.array(list(map(float,node.get("PointData").split(",")))).reshape(-1,3)
            np.testing.assert_allclose(points,m.points,atol=1e-6)
        elif m.display=="Poly Line":
            points=np.array(list(map(float,node.get("PointData").split(",")))).reshape(-1,3)
            np.testing.assert_allclose(points[[0,-1]],m.points[[0,-1]],atol=1e-6)
        elif m.display=="Single Line":
            anchor=np.array([float(node.get("WorldPos"+k)) for k in "XYZ"])
            end=anchor+np.array([float(node.get(k+"2")) for k in "XYZ"])
            np.testing.assert_allclose([anchor,end],m.points[[0,-1]],atol=1e-6)


def test_dna_palettes_and_control_isolation_are_native_not_preview_only(exported):
    _,g,path,_=exported;root=ET.parse(path/(g.slug+"_Showcase.xsq")).getroot()
    elements={e.get("name"):e for e in root.findall("ElementEffects/Element")}
    palettes=[p.text for p in root.findall("ColorPalettes/ColorPalette")]
    for m in g.models:
        if m.kind!="pixel":assert m.name not in elements
        elif m.details.get("double_helix"):
            parts=m.submodels
            for layer in elements[m.name].findall("SubModelEffectLayer"):
                color=m.colors[parts[layer.get("name")][0]-1]
                assert all(color in palettes[int(e.get("palette"))] for e in layer.findall("Effect"))
            assert set(parts["STRAND_A"])|set(parts["STRAND_B"])|set(parts["RUNGS"])==set(range(1,len(m.points)+1))
    manifest=json.loads((path/"showcase_manifest.json").read_text())
    assert manifest["file_prefix"]==g.slug and g.title in manifest["name"]


def test_six_compositions_differ_in_topology_placement_and_elemental_colours():
    shows={f.key:build_flavor(f.key) for f in FLAVORS}
    # Ignore names/colours: distinct geometry fingerprints prove these aren't
    # six copies with different branding. Ring/bridge counts protect structure.
    fingerprints=[]
    for g in shows.values():
        points=np.concatenate([m.points for m in g.models if m.details.get("double_helix")])
        fingerprints.append(hashlib.sha256(points.round(3).tobytes()).hexdigest())
    assert len(set(fingerprints))==6
    assert sum(bool(m.details.get("ring")) for m in shows["celestial_orrery"].models)==3
    assert sum(m.details.get("axis")=="horizontal" for m in shows["crystal_lagoon"].models)==2
    fire=shows["fire_and_ice"]
    west={m.colors[0] for m in fire.models if m.details.get("spiral_tree") and m.points[:,0].mean()<0}
    east={m.colors[0] for m in fire.models if m.details.get("spiral_tree") and m.points[:,0].mean()>0}
    assert west.isdisjoint(east)
    assert all(m.name.startswith("HX_"+f.code+"_") for f in FLAVORS for m in shows[f.key].models)


def test_aurora_native_export_remains_identical_to_delivered_show(tmp_path):
    write_layout(build_ultimate_garden(),tmp_path)
    original=Path(__file__).resolve().parents[1]/"showcase/Helix_Aurora"
    for p in tmp_path.rglob("*"):
        if p.is_file() and p.name!="preview_geometry.json":
            assert p.read_bytes()==(original/p.relative_to(tmp_path)).read_bytes(),p.name


def test_compact_collection_has_working_links_hashes_and_no_native_caches(tmp_path):
    from PIL import Image
    from tools.build_showcase_flavors import collection_gallery
    from tools.build_ultimate_showcase_layout import package_showcase

    summaries=[]
    for f in FLAVORS:
        folder=tmp_path/f.slug;folder.mkdir()
        (folder/'showcase_manifest.json').write_text(json.dumps({'file_prefix':f.slug}))
        for name in ('xlights_rgbeffects.xml','xlights_networks.xml',f.slug+'_Showcase.xsq','README.txt','model_inventory.csv'):
            (folder/name).write_text('portable fixture')
        (folder/(f.slug+'_3D.html')).write_text('<p>Offline viewer</p>')
        Image.new('RGB',(160,90),f.colors[0]).save(folder/(f.slug+'_Night.png'))
        (folder/'unrelated_native_backup.bak').write_text('must not be included')
        (folder/(f.slug+'_Showcase.mp4')).write_bytes(b'movie belongs to individual archive')
        package_showcase(folder)
        summaries.append({'slug':f.slug,'title':f.title,'description':f.description,'palette':f.colors,
                          'models':100,'spiral_trees':36,'double_helices':12,'mp4_seconds':24})
    collection_gallery(tmp_path,summaries,tour=False)
    with zipfile.ZipFile(tmp_path/'Helix_Six_Flavors_Layouts.zip') as z:
        names=set(z.namelist());prefix='Helix_Six_Flavors/'
        page=z.read(prefix+'index.html').decode()
        for href in re.findall(r'(?:href|src)="([^"]+)"',page):
            assert prefix+href in names,href
        assert not any(n.endswith(('.mp4','.bak')) for n in names)
        for f in FLAVORS:
            sub=prefix+f.slug+'/'
            hashes=json.loads(z.read(sub+'bundle_checksums.json'))
            assert hashes
            for name,digest in hashes.items():
                assert hashlib.sha256(z.read(sub+name)).hexdigest()==digest
