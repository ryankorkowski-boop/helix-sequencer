import json
import xml.etree.ElementTree as ET

import numpy as np
import pytest
import trimesh

from tools.infinity_park.export import export, native_xyz
from tools.infinity_park.site import DISTRICTS


@pytest.fixture(scope="module")
def park(tmp_path_factory):
    output = tmp_path_factory.mktemp("infinity_park")
    report=export(output,include_band=False)
    manifest=json.loads((output/"scene_manifest.json").read_text())
    root=ET.parse(output/"xlights_rgbeffects.xml").getroot()
    return output, report, manifest, root


def test_geometry_and_views(park):
    output, report, manifest, root=park
    assert report["districts"]==7 and report["triangles"]>400_000
    mesh=trimesh.load_scene(output/"assets/Infinity_Park.glb",process=False)
    assert all(any(name.startswith(f"{district}_") for name in mesh.geometry) for district in DISTRICTS)
    assert np.all(mesh.extents > (250,40,220))
    assert {"overview","plan","side","front","Arena","Arena_wing"} <= set(manifest["cameras"])
    for obj in root.findall("./view_objects/view_object"):
        assert (output/obj.attrib["ObjFile"]).is_file()
    assert root.find("./Viewpoints/DefaultCamera3D").get("is_3d")=="1"


def test_native_channel_binding_and_density(park):
    output, report, manifest, root=park
    counts=manifest["prop_counts"]
    for family,target in {"Spiral_Tree":320,"Arch":400,"Tower_Tree":48,"Mega_Tree":24,
                          "Monumental_Mega_Tree":4,"Star":180,"Matrix":80,"Spinner":160}.items():
        assert counts[family]>=target
    rows=manifest["models"]
    assert len(rows)>=2000
    assert rows[0]["first_channel"]==1
    assert rows[-1]["last_channel"]==report["channels"]
    assert all(a["last_channel"]+1==b["first_channel"] for a,b in zip(rows,rows[1:]))
    positions=np.load(output/"rgb_bindings.npz")["positions"]
    for model,row in zip(root.findall("./models/model"),rows,strict=True):
        assert model.get("name")==row["model"]
        n=int(model.get("parm2"))
        assert row["nodes"]==n
        assert int(model.get("StartChannel"))==row["first_channel"]
        assert model.get(f"Seg{n}")=="1" and model.get(f"Corner{n}")=="Trailing Segment"
        nodes=np.fromstring(model.get("PointData"),sep=",").reshape(-1,3)[:n]
        origin=np.array([float(model.get(f"WorldPos{axis}")) for axis in "XYZ"])
        start=(row["first_channel"]-1)//3
        np.testing.assert_allclose(nodes+origin,native_xyz(positions[start:start+n]),atol=2e-5)
    assert manifest["owner_approved"] is False


def test_district_routes_preserve_source_rests_and_native_ownership(park):
    from tools.infinity_park.arrange import DISTRICT_ROLES, park_models
    from tools.source_spatial_direction import onset_index, schedule

    output, _, manifest, _ = park
    with np.load(output/"rgb_bindings.npz") as bindings:
        models=park_models(manifest,bindings["positions"])
    assert DISTRICT_ROLES["Motor"]["Wheel"]=="drummer"
    assert DISTRICT_ROLES["Gothic"]["Spires"]=="bassist"
    assert DISTRICT_ROLES["Jungle"]["Flower"]=="keyboardist"
    cue={"start_ms":100,"end_ms":290,"section":"PRECHORUS","kind":"snare","velocity":.9}
    plan={"cues":{"drummer":[cue]}}
    wheel=[m for m in models if m.name.startswith("Motor_Wheel_")]
    hits=[schedule(model,plan,{},800,shared_onsets={"drummer":onset_index([cue])}) for model in wheel]
    assert 0<sum(bool(h) for h in hits)<=4<len(wheel)
    assert all(100<=event["start_ms"]<event["end_ms"]<=290 for group in hits for event in group)
    grand=[m for m in models if m.name.startswith("Grand_Window_")]
    assert not any(schedule(model,plan,{},800) for model in grand)


def test_canonical_band_binding_stays_at_the_arena(tmp_path):
    from tools.infinity_park.export import canonical_band, site_xyz

    models,groups=ET.Element("models"),ET.Element("modelGroups")
    band=list(canonical_band(models,groups,tmp_path,1))
    assert len(band)==6
    channel=1
    for model,points,role in band:
        assert model.start==channel
        channel+=model.channels
        np.testing.assert_allclose(site_xyz(native_xyz(points)),points)
        np.testing.assert_allclose(native_xyz(points),model.points)
        assert np.all((-90<points[:,1]) & (points[:,1]<-61)),role
        assert np.all((0<points[:,2]) & (points[:,2]<17)),role
