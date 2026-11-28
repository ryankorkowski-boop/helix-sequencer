"""Export the park's editable geometry, xLights models and RGB node binding."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import numpy as np

from .geometry import MATERIALS
from .site import CAMERAS, COUNTS, DISTRICTS, PALETTES, build_park


def rgb(hex_color):
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]


def native_xyz(points):
    # Site/glTF use a right-handed basis. xLights uses Y-up and positive Z forward.
    return np.asarray(points)[..., [0, 2, 1]] * (1, 1, -1)


def site_xyz(points):
    return np.asarray(points)[..., [0, 2, 1]] * (1, -1, 1)


def packed_geometry(scene):
    for (district, material), pieces in scene.pieces.items():
        vertices, faces = [], []
        offset = 0
        for points, indices in pieces:
            vertices.append(points)
            faces.append(indices + offset)
            offset += len(points)
        yield district, material, np.vstack(vertices), np.vstack(faces)


def export_meshes(scene, folder):
    import trimesh
    from trimesh.visual.material import PBRMaterial
    from trimesh.visual.texture import TextureVisuals

    folder.mkdir(parents=True, exist_ok=True)
    mesh = trimesh.Scene()
    geometry = list(packed_geometry(scene))
    with (folder/"Infinity_Park.mtl").open("w") as mtl:
        for name,(color,metal,roughness) in MATERIALS.items():
            r,g,b = (c/255 for c in rgb(color))
            mtl.write(f"newmtl {name}\nKa {r:.4f} {g:.4f} {b:.4f}\nKd {r:.4f} {g:.4f} {b:.4f}\n"
                      f"Ks {metal:.3f} {metal:.3f} {metal:.3f}\nNs {max(2,100*(1-roughness)):.2f}\nillum 2\n\n")
    mesh_objects = []
    for district in ("Ground", *DISTRICTS):
        name = f"{district}.obj"
        mesh_objects.append(name)
        with (folder/name).open("w") as obj:
            obj.write("mtllib Infinity_Park.mtl\n")
            offset = 1
            for owner, mat, points, faces in geometry:
                if owner != district:
                    continue
                color, metal, roughness = MATERIALS[mat]
                part = trimesh.Trimesh(vertices=native_xyz(points), faces=faces, process=False)
                part.visual = TextureVisuals(material=PBRMaterial(
                    name=mat, baseColorFactor=[*rgb(color),255], metallicFactor=metal,
                    roughnessFactor=roughness, doubleSided=True))
                label = f"{owner}_{mat}"
                mesh.add_geometry(part, geom_name=label, node_name=label)
                obj.write(f"o {label}\nusemtl {mat}\n")
                np.savetxt(obj, part.vertices, fmt="v %.5f %.5f %.5f")
                np.savetxt(obj, faces+offset, fmt="f %d %d %d")
                offset += len(points)
    camera_nodes = []
    for name, camera in CAMERAS.items():
        transform = np.eye(4)
        eye = native_xyz(camera["eye"]).astype(float)
        back = eye-native_xyz(camera["target"])
        back /= np.linalg.norm(back)
        right = np.cross((0.,1.,0.),back)
        right /= np.linalg.norm(right)
        transform[:3,:3] = np.column_stack((right,np.cross(back,right),back))
        transform[:3,3] = eye
        # GLB camera nodes are added below because trimesh exports one scene camera.
        scene_camera = {"name": name, "type": "orthographic",
                        "orthographic": {"xmag": camera["width"]/2, "ymag": camera["width"]*9/32,
                                         "znear": .1, "zfar": 800}}
        camera_nodes.append((scene_camera, transform.T.reshape(-1).tolist()))
    def add_cameras(tree):
        tree["cameras"] = [camera for camera, _ in camera_nodes]
        for i, (camera, transform) in enumerate(camera_nodes):
            tree["scenes"][0]["nodes"].append(len(tree["nodes"]))
            tree["nodes"].append({"name":camera["name"],"matrix":transform,"camera":i})
    # Build cameras before writing the GLB. xLights uses its own Viewpoints below.
    (folder/"Infinity_Park.glb").write_bytes(trimesh.exchange.gltf.export_glb(
        mesh, include_normals=True, tree_postprocessor=add_cameras))
    return mesh_objects, sum(len(faces) for _,_,_,faces in geometry)


def polyline(models, prop, start):
    points = native_xyz(prop.points)
    origin = points[0]
    # One bulb at the leading vertex of each segment. Separately assigned
    # segment counts keep corners, matrix row changes, and curved surfaces exact.
    handles = np.vstack((points, points[-1]+(0,.025,0))) - origin
    attrib = {
        "name": prop.name, "DisplayAs": "Poly Line", "LayoutGroup": "Default",
        "StringType": "RGB Nodes", "StartChannel": str(start), "StartSide": "B", "Dir": "L",
        "parm1": "1", "parm2": str(len(points)), "parm3": "1", "PolyStrings": "1",
        "PixelSize": "3", "Antialias": "1", "NumPoints": str(len(handles)), "cPointData": "",
        "PointData": ",".join(f"{p:.5f}" for p in handles.ravel()),
        **{f"WorldPos{a}":f"{p:.5f}" for a,p in zip("XYZ",origin)},
        **{f"Scale{a}":"1" for a in "XYZ"},
        **{f"Seg{i}":"1" for i in range(1,len(handles))},
        **{f"Corner{i}":"Trailing Segment" for i in range(1,len(handles)+1)},
    }
    model = ET.SubElement(models,"model",attrib)
    if prop.row_width:
        width=prop.row_width
        ET.SubElement(model,"subModel",{
            "name":"Surface","layout":"horizontal","type":"ranges",
            **{f"line{j}":f"{i+1}-{i+width}" if j%2==0 else f"{i+width}-{i+1}"
               for j,i in enumerate(range(0,len(points),width))}})
    else:
        middle=len(points)//2
        for label,node_range in (("First",f"1-{middle}"),("Second",f"{middle+1}-{len(points)}")):
            ET.SubElement(model,"subModel",name=label,layout="horizontal",type="ranges",line0=node_range)


def canonical_band(models, groups, assets, channel):
    from models.canonical_native_band import ROLES, add_band
    from models.ultimate_showcase import Garden
    from tools.build_helpers.ultimate_showcase import model_xml

    _, (x,y), _ = DISTRICTS["Arena"]
    band = add_band(Garden(title="Infinity Live",slug="Infinity_Live"), prefix="HX_INFINITY_SNOW",
                    full_keyboard=True, native_extended_mouths=True)
    if len(band)!=6 or {m.details["final_band_role"] for m in band}!=set(ROLES):
        raise ValueError("The canonical stage must contain exactly six performers")
    reference = Path(__file__).resolve().parents[2]/"fixtures/band_geometry/source"
    for filename in ("drummer_idle.png","drummerbg.png"):
        shutil.copyfile(reference/filename,assets/filename)
    names = defaultdict(list)
    for performer in band:
        role=performer.details["final_band_role"]
        scale=.39 if role=="drummer" else .53
        delta=np.array((x-4.1,4.6,-y-3.8) if role=="drummer" else (x,2.4,-y-1.9))
        performer.points=performer.points*scale+delta
        for i, a in enumerate("XYZ"):
            performer.attrs[f"WorldPos{a}"] = str(float(performer.attrs[f"WorldPos{a}"])*scale+delta[i])
            performer.attrs[f"Scale{a}"] = str(float(performer.attrs[f"Scale{a}"])*scale)
        performer.start = channel
        models.append(model_xml(performer))
        names["HX_SNOWMAN_BAND"].append(performer.name)
        names["HX_SNOWMAN_VOCALS" if role in ("lead","harmony") else "HX_SNOWMAN_INSTRUMENTS"].append(performer.name)
        yield performer, site_xyz(performer.points), role
        channel += performer.channels
    for name,members in names.items():
        ET.SubElement(groups,"modelGroup",name=name,models=",".join(members))


def write_xml(path, root):
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def export(output, *, include_band=True):
    start_time=time.perf_counter()
    output = Path(output)
    assets=output/"assets"
    scene=build_park()
    obj_names, triangles=export_meshes(scene,assets)
    root=ET.Element("xrgb")
    models,groups,objects,views,settings=(ET.SubElement(root,name)
        for name in ("models","modelGroups","view_objects","Viewpoints","settings"))
    members=defaultdict(list)
    inventory=[]
    positions, radii, static_colors=[],[],[]
    channel=1
    for prop in scene.props:
        count=len(prop.points)
        polyline(models,prop,channel)
        record={
            "model":prop.name,"district":prop.district,"family":prop.family,
            "first_channel":channel,"last_channel":channel+3*count-1,"nodes":count,
            "center_m":np.round(prop.points.mean(axis=0),5).tolist(),"row_width":prop.row_width,
        }
        inventory.append(record)
        for key in (f"Infinity_{prop.district}_{prop.family}",f"Infinity_{prop.district}"):
            members[key].append(prop.name)
        positions.append(prop.points)
        radii.append(np.full(count,prop.radius))
        palette=PALETTES[prop.district]
        static_colors.append(np.tile(rgb(palette[(len(members[f"Infinity_{prop.district}_{prop.family}"])-1)%3]),(count,1)))
        channel += 3*count
    for district in DISTRICTS:
        regional=[r for r in inventory if r["district"]==district]
        axis=2 if district=="Gothic" else 1 if district in ("Jungle","Motor") else 0
        members[f"Infinity_{district}_Route"]=[r["model"] for r in sorted(
            regional,key=lambda r:(r["center_m"][axis],r["model"]))]
    for name, elements in members.items():
        ET.SubElement(groups,"modelGroup",name=name,models=",".join(elements),layout="minimalGrid")
    park_end = channel-1
    if include_band:
        for performer, points, role in canonical_band(models,groups,assets,channel):
            count=len(points)
            inventory.append({"model":performer.name,"district":"Arena","family":role,
                              "first_channel":performer.start,"last_channel":performer.start+performer.channels-1,
                              "nodes":count,"center_m":np.round(points.mean(axis=0),5).tolist(),"row_width":0})
            positions.append(points)
            radii.append(np.full(count,.04 if role=="drummer" else .041))
            static_colors.append(np.zeros((count,3),dtype=np.uint8))
            channel=performer.start+performer.channels
    count=Counter(p.family for p in scene.props)
    for family,targets in COUNTS.items():
        target=80 if family=="Matrix" else sum(targets)
        if count[family]<target:
            raise ValueError(f"{family} count {count[family]} below {target}")
    for obj in obj_names:
        ET.SubElement(objects,"view_object",name=Path(obj).stem,DisplayAs="Mesh",ObjFile=f"assets/{obj}",
                      MeshOnly="0",Brightness="100",Active="1",LayoutGroup="Default",
                      WorldPosX="0",WorldPosY="0",WorldPosZ="0",ScaleX="1",ScaleY="1",ScaleZ="1",
                      RotateX="0",RotateY="0",RotateZ="0")
    for name,value in {"backgroundBrightness":"0","storedLayoutGroup":"All Models","LayoutMode3D":"1",
                       "Display2DCenter0":"1","previewWidth":"1920","previewHeight":"1080"}.items():
        ET.SubElement(settings,name,value=value)
    for name,camera in CAMERAS.items():
        eye=native_xyz(camera["eye"])
        target=native_xyz(camera["target"])
        delta=eye-target
        distance=np.linalg.norm(delta)
        ET.SubElement(views,"DefaultCamera3D" if name=="overview" else "Camera",
                      name="DEFAULT3D" if name=="overview" else name,is_3d="1",
                      posX="0",posY="0",posZ="0",panx=str(-target[0]),pany=str(-target[1]),panz=str(-target[2]),
                      angleX=str(np.degrees(np.arcsin(delta[1]/distance))),
                      angleY=str(np.degrees(np.arctan2(delta[0],delta[2]))),angleZ="0",
                      distance=str(-distance),zoom="1",zoom_corrx="0",zoom_corry="0")
    write_xml(output/"xlights_rgbeffects.xml",root)
    network=ET.Element("Networks",computer="Infinity",DisableOutput="1")
    ET.SubElement(network,"network",NetworkType="NULL",Description="Infinity virtual controller",
                  MaxChannels=str(channel-1),BaudRate="115200",ComPort="1")
    write_xml(output/"xlights_networks.xml",network)
    positions=np.vstack(positions).astype(np.float32)
    if len(positions)*3!=channel-1:
        raise ValueError("FSEQ channel bindings are not contiguous")
    np.savez_compressed(output/"rgb_bindings.npz",positions=positions,
                       radii=np.concatenate(radii).astype(np.float32),static_rgb=np.vstack(static_colors).astype(np.uint8))
    with (output/"channel_map.csv").open("w",newline="") as file:
        writer=csv.writer(file)
        writer.writerow(("model","node","red_channel","green_channel","blue_channel","x_m","y_m","z_m"))
        idx=0
        for row in inventory:
            for node in range(row["nodes"]):
                red=row["first_channel"]+3*node
                writer.writerow((row["model"],node+1,red,red+1,red+2,*[f"{v:.5f}" for v in positions[idx]]))
                idx+=1
    manifest={
        "schema":"helix.infinity.park.v1","owner_approved":False,
        "site_basis":"metres; X east, Y north, Z up. xLights/glTF: (X,Z,-Y).",
        "districts":{k:{"name":title,"center_m":[*xy,0],"palette_srgb":PALETTES[k]}
                     for k,(title,xy,_) in DISTRICTS.items()},"cameras":CAMERAS,
        "park_nodes":park_end//3,"total_rgb_channels":channel-1,"prop_counts":dict(count),
        "mesh_triangles":triangles,"model_count":len(inventory),"models":inventory,
    }
    (output/"scene_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return {"districts":len(DISTRICTS),"models":len(inventory),"park_rgb_nodes":park_end//3,
            "channels":channel-1,"triangles":triangles,"seconds":round(time.perf_counter()-start_time,3)}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--without-band",action="store_true")
    args=parser.parse_args()
    print(json.dumps(export(args.output,include_band=not args.without_band),indent=2))
