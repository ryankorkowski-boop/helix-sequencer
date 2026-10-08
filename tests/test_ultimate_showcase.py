from pathlib import Path
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
import zlib
import zipfile

import numpy as np
import pytest

from models.ultimate_showcase import build_ultimate_garden, garden_manifest, NATIVE_TYPES, family
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_helpers.ultimate_showcase_preview import read_fseq


@pytest.fixture(scope="module")
def garden():
    return build_ultimate_garden()


@pytest.fixture(scope="module")
def exported(garden,tmp_path_factory):
    path=tmp_path_factory.mktemp("ultimate_showcase")
    write_layout(garden,path)
    return path,ET.parse(path/"xlights_rgbeffects.xml").getroot()


def test_factory_coverage_and_real_spiral_dna_topology(garden,exported):
    _,root=exported
    # Independently transcribed creatable families from pinned upstream factory.
    expected={"Arches","Candy Canes","Channel Block","Circle","Cube","Custom","DmxMovingHead",
              "DmxMovingHeadAdv","DmxFloodlight","DmxFloodArea","DmxGeneral","DmxSkull","DmxServo",
              "DmxServo3d","Image","Label","Window Frame","Wreath","Sphere","Single Line","Poly Line",
              "MultiPoint","Tree","Matrix","Spinner","Star","Icicles"}
    assert set(NATIVE_TYPES)==expected
    assert {family(m.get("DisplayAs")) for m in root.findall("models/model")}==expected
    spiral=[m for m in garden.models if m.details.get("spiral_tree")]
    dna=[m for m in garden.models if m.details.get("double_helix")]
    assert len(spiral)>=30 and len(dna)>=10
    assert all(float(m.attrs["TreeSpiralRotations"])>=2 for m in spiral)
    for m in dna:
        a,b,r=(set(m.submodels[s]) for s in ["STRAND_A","STRAND_B","RUNGS"])
        assert len(a)==len(b)>100
        assert a.isdisjoint(b) and r.isdisjoint(a|b)
        assert a|b|r==set(range(1,len(m.points)+1))
        assert len(r)>=5*m.details["rung_count"]  # Real illuminated bars, not midpoints.
        assert np.ptp(m.points[:,2])>4  # Genuine 3D depth, not a drawn sine wave.


def test_channel_map_and_group_references_are_importable(garden,exported):
    path,root=exported
    names={m.get("name") for m in root.findall("models/model")}
    assert len(names)==len(garden.models)
    expected=1
    for m,xml in zip(garden.models,root.findall("models/model"),strict=True):
        assert int(xml.get("StartChannel"))==expected
        # No Controller would make xLights reallocate the entire map alphabetically.
        assert xml.get("Controller")==""
        expected+=m.channels
        for key in ("WorldPosX","WorldPosY","WorldPosZ"):
            assert np.isfinite(float(xml.get(key)))
    lookup={m.name:m for m in garden.models}
    for group in root.findall("modelGroups/modelGroup"):
        for member in group.get("models").split(","):
            parent,_,sub=member.partition("/")
            assert parent in names
            if sub:assert sub in lookup[parent].submodels
    assert not ET.parse(path/"xlights_networks.xml").getroot().findall("Controller")


def test_custom_xyz_roundtrip_and_unique_occupied_cells(garden,exported):
    _,root=exported
    for m in garden.models:
        if m.display!="Custom":continue
        xml=next(x for x in root.findall("models/model") if x.get("name")==m.name)
        cells=np.array([[int(v) for v in entry.split(",")] for entry in xml.get("CustomModelCompressed").split(";")])
        assert list(cells[:,0])==list(range(1,len(m.points)+1))
        assert len(set(map(tuple,cells[:,1:])))==len(cells)
        # The native engine centers occupied cells and reverses row/layer axes.
        rows,cols,layers=cells[:,1],cells[:,2],cells[:,3]
        raw=np.c_[cols-(cols.min()+cols.max())/2,(rows.min()+rows.max())/2-rows,(layers.min()+layers.max())/2-layers]
        position=np.array([float(xml.get("WorldPos"+axis)) for axis in "XYZ"])
        scale=np.array([float(xml.get("Scale"+axis)) for axis in "XYZ"])
        np.testing.assert_allclose(raw*scale+position,m.points,atol=1e-6)
        assert m.details["max_snap_error_ft"]<=.44
        for sub in xml.findall("subModel"):
            assert sub.get("line0")


def test_native_proportions_use_engine_units_not_unit_circle(garden):
    lookup={m.name:m for m in garden.models}
    # Independent native dimensional checks: max ring layer96 means radius48;
    # 24-latitude sphere's diameter is24/1.8; frame width is48+2.
    assert float(lookup["HX_ORBIT_TRIPTYCH_-1"].attrs["ScaleX"])==pytest.approx(19/96,abs=1e-5)
    sphere=lookup["HX_ORRERY_MOON_-1"]
    assert .9<float(sphere.attrs["ScaleY"])<1.2
    assert float(lookup["HX_JEWEL_WINDOW_-1"].attrs["ScaleX"])==pytest.approx(30/50,abs=1e-5)
    assert float(lookup["HX_SOLAR_SPINNER_-1"].attrs["ScaleX"])<.5
    assert float(lookup["HX_FIBONACCI_ICICLES_-1"].attrs["Height"])<0
    for m in garden.models:
        assert np.isfinite(m.points).all()
        assert m.points[:,1].min()>=-.01
        assert np.abs(m.points[:,0]).max()<205


def test_demo_submodels_have_native_effect_layers_and_controls_are_isolated(garden,exported):
    path,_=exported;root=ET.parse(path/"Helix_Aurora_Showcase.xsq").getroot()
    elements={e.get("name"):e for e in root.findall("ElementEffects/Element")}
    for m in garden.models:
        if m.kind!="pixel":
            assert m.name not in elements
        elif m.details.get("double_helix"):
            # Nested SubModel/EffectLayer silently rendered black in native xLights.
            assert not elements[m.name].findall("SubModel")
            layers=elements[m.name].findall("SubModelEffectLayer")
            assert {s.get("name") for s in layers}=={"STRAND_A","STRAND_B","RUNGS"}
            assert all(len(s.findall("Effect"))==6 for s in layers)
    assert root.findtext("head/sequenceType")=="Animation"
    assert float(root.findtext("head/sequenceDuration"))==24


def test_assets_are_portable_and_original_show_is_not_inherited(garden,exported):
    path,root=exported
    for m in root.findall("models/model"):
        for e in m.iter():
            for key in ("Image","ObjFile"):
                if e.get(key):
                    file=Path(e.get(key));assert not file.is_absolute()
                    assert (path/file).is_file()
    assert not any("DRUMMER" in m.get("name") for m in root.findall("models/model"))
    assert len(list((path/"models").glob("*.xmodel")))==12
    assert garden_manifest(garden)["native_coverage_complete"]


def test_fseq_sparse_zlib_decodes_channels_without_shifting(tmp_path):
    # Two packed channels belong at absolute zero-based channels2 and3.
    payload=bytes([10,20,30,40]);packed=zlib.compress(payload)
    header=bytearray(46);header[:4]=b"PSEQ"
    struct.pack_into("<HBBHII",header,4,46,0,2,46,2,2)
    header[18]=50;header[20]=2;header[21]=1;header[22]=1
    struct.pack_into("<II",header,32,0,len(packed))
    header[40:43]=(2).to_bytes(3,"little");header[43:46]=(2).to_bytes(3,"little")
    p=tmp_path/"native.fseq";p.write_bytes(header+packed)
    frames,step=read_fseq(p)
    assert step==50
    np.testing.assert_array_equal(frames,[[0,0,10,20],[0,0,30,40]])
    p.write_bytes(header+packed[:-1])
    with pytest.raises(ValueError,match="Truncated"):read_fseq(p)


def test_review_bundle_hashes_late_evidence_and_excludes_autosaves(garden,tmp_path):
    from tools.build_ultimate_showcase_layout import package_showcase
    output=tmp_path/"show";write_layout(garden,output)
    (output/"native_verification.json").write_text('{"native_render_success":true}')
    (output/"Backup").mkdir();(output/"Backup"/"old-layout.xml").write_text("obsolete")
    (output/"xlights_rgbeffects.xbkp").write_text("obsolete")
    bundle=package_showcase(output)
    with zipfile.ZipFile(bundle) as archive:
        names=set(archive.namelist())
        assert "Helix_Aurora/native_verification.json" in names
        assert not any("Backup" in n or n.endswith(".xbkp") for n in names)
        checks=json.loads(archive.read("Helix_Aurora/bundle_checksums.json"))
        assert set(checks)=={n.removeprefix("Helix_Aurora/") for n in names if not n.endswith("bundle_checksums.json")}
        for name,digest in checks.items():
            assert hashlib.sha256(archive.read("Helix_Aurora/"+name)).hexdigest()==digest
