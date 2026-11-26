#!/usr/bin/env python3
"""Deterministic xLights layout #9: Helix Infinity Universe.

This generator creates actual xLights models and overlapping choreography groups,
not rendered effects. Audio-reactive sequencing is performed by Helix separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

FAMILIES = (
    ("SPIRAL_TREE", 144, 96, "melody"),
    ("DOUBLE_HELIX", 48, 256, "harmony"),
    ("TUNNEL_3D", 12, 480, "transitions"),
    ("VOXEL_GRID_3D", 16, 512, "spatial"),
    ("MEGA_TREE", 64, 192, "harmony"),
    ("ARCH", 256, 48, "rhythm"),
    ("ORNAMENT", 256, 64, "accents"),
    ("SCULPTURE", 128, 96, "counterpoint"),
    ("MATRIX_2D", 64, 192, "melody"),
    ("PIANO_COLUMN", 256, 32, "piano"),
    ("SPHERE", 128, 96, "bass"),
    ("GROUND_WAVE", 512, 32, "bass"),
    ("SINGING_FACE", 32, 288, "vocals"),
    ("SKY_STRUCTURE", 132, 48, "atmosphere"),
)
TOTAL_PROPS = sum(spec[1] for spec in FAMILIES)
assert TOTAL_PROPS == 2048

def coordinates(family, index, count):
    # Deterministic dispersed arrangement with actual Z variation.
    # Give each family a coherent concentric district rather than random overlap.
    district = next(k for k, spec in enumerate(FAMILIES) if spec[0] == family)
    angle = 2*math.pi*(district + 0.12 + 0.76*(index % 17)/16)/len(FAMILIES)
    radius = 90 + 460*((index//17 + .5)/max(1,math.ceil(count/17)))
    return radius * math.cos(angle), radius * math.sin(angle), 5.0 + 35.0 * (index % 7) / 6

def spiral(cx, cy, cz, nodes, turns, height=54, radius=14, handed=1):
    return [(cx + radius * (1 - .76*t)*math.cos(handed*2*math.pi*turns*t),
             cy + radius * (1 - .76*t)*math.sin(handed*2*math.pi*turns*t),
             cz + height*t) for j in range(nodes) for t in [j/(nodes-1)]]

def helix(cx, cy, cz, nodes):
    half = nodes//2
    a = [(cx + 16*math.cos(2*math.pi*7.5*j/(half-1)), cy + 16*math.sin(2*math.pi*7.5*j/(half-1)), cz + 76*j/(half-1)) for j in range(half)]
    b = [(cx + 16*math.cos(2*math.pi*7.5*j/(half-1)+math.pi),
          cy + 16*math.sin(2*math.pi*7.5*j/(half-1)+math.pi),
          cz + 76*j/(half-1)) for j in range(half)]
    return a + list(reversed(b))

def tunnel(cx, cy, cz, nodes):
    return [(cx+24*math.cos(2*math.pi*(j%40)/40), cy+24*math.sin(2*math.pi*(j%40)/40),
             cz+4*(j//40)) for j in range(nodes)]

def voxel(cx, cy, cz):
    out=[]
    # 8 x 8 x 8, physically separated planes, serpentine wiring.
    for z in range(8):
        for y in range(8):
            xs=range(8) if (y+z)%2==0 else range(7,-1,-1)
            for x in xs: out.append((cx+3*(x-3.5),cy+3*(y-3.5),cz+3*z))
    return out

def points(family, i, count, nodes):
    x,y,z = coordinates(family,i,count)
    if family=="DOUBLE_HELIX": return helix(x,y,z,nodes)
    if family=="VOXEL_GRID_3D": return voxel(x,y,z)
    if family=="TUNNEL_3D": return tunnel(x,y,z,nodes)
    if family in ("SPIRAL_TREE","MEGA_TREE"): return spiral(x,y,z,nodes,4+(i%7),43+(i%5)*9,10+(i%3)*5,-1 if i%2 else 1)
    if family=="ARCH":
        return [(x + 14*(2*j/(nodes-1)-1),y,z+22*math.sin(math.pi*j/(nodes-1))) for j in range(nodes)]
    if family=="GROUND_WAVE":
        return [(x+3*j/(nodes-1)*10,y,z+2.5*math.sin(j*math.pi*3/(nodes-1))) for j in range(nodes)]
    if family=="PIANO_COLUMN":
        return [(x,y,z+28*j/(nodes-1)) for j in range(nodes)]
    if family=="SKY_STRUCTURE":
        return [(x+20*math.cos(j*2*math.pi/(nodes-1)),y+20*math.sin(j*2*math.pi/(nodes-1)),z+65) for j in range(nodes)]
    if family in ("SPHERE","SCULPTURE","ORNAMENT"):
        return [(x+(12 if family=="SPHERE" else 8)*math.sin(j*math.pi/9)*math.cos(j*2.399963),
                 y+(12 if family=="SPHERE" else 8)*math.sin(j*math.pi/9)*math.sin(j*2.399963),
                 z+9*math.cos(j*math.pi/9)) for j in range(nodes)]
    return [(x+16*((j%24)/23-.5),y,z+20*((j//24)/max(1,nodes//24-1))) for j in range(nodes)]

def make_layout(output, manifest, size=2048):
    if size not in (128,512,2048,10240): raise ValueError("size must be 128, 512, 2048 or 10240")
    root=ET.Element("xrgb")
    models=ET.SubElement(root,"models")
    groups=ET.SubElement(root,"modelGroups")
    records=[]
    next_channel=1
    for family,maximum,nodes,role in FAMILIES:
        count=maximum*5 if size==10240 else maximum if size==2048 else max(1,round(maximum*size/2048))
        for i in range(count):
            p=points(family,i,count,nodes)
            assert len(p)==nodes, (family,len(p),nodes)
            name=f"HX_INFINITY_{family}_{i+1:04d}"
            x,y,z=coordinates(family,i,count)
            # Geometry helpers use a horizontal XY plane with Z height. xLights
            # displays X/Y from the front and adds WorldPos to model-local points.
            local = [(a-x, c-z, b-y) for a,b,c in p]
            if family == "TUNNEL_3D":
                local = [(a-x, b-y, c-z) for a,b,c in p]
            attrs={"name":name,"DisplayAs":"Poly Line","StringType":"RGB Nodes",
                   "StartChannel":str(next_channel),"parm1":"1","parm2":str(nodes),"parm3":"1",
                   "StartSide":"B","Dir":"L","Antialias":"1","PixelSize":"4",
                   "Transparency":"0","LayoutGroup":"Default",
                   "WorldPosX":f"{x:.4f}","WorldPosY":f"{z:.4f}","WorldPosZ":f"{y:.4f}",
                   "ScaleX":"1.0000","ScaleY":"1.0000","ScaleZ":"1.0000",
                   "NumPoints":str(nodes),
                   "PointData":",".join(f"{a:.3f},{b:.3f},{c:.3f}" for a,b,c in local),
                   "cPointData":"","versionNumber":"7"}
            model = ET.SubElement(models,"model",attrs)
            if family == "SINGING_FACE":
                ET.SubElement(model, "subModel", {"name": "Mouth", "layout": "horizontal", "type": "ranges", "line0": "1-24"})
                ET.SubElement(model, "subModel", {"name": "Eyes", "layout": "horizontal", "type": "ranges", "line0": "25-48"})
            records.append({"name":name,"family":family,"role":role,"nodes":nodes,
                            "start_channel":next_channel,"end_channel":next_channel+3*nodes-1,
                            "center":[round(x,3),round(z,3),round(y,3)]})
            next_channel+=3*nodes
    names=[r["name"] for r in records]
    def group(name,members):
        if members: ET.SubElement(groups,"modelGroup",{"name":name,"models":",".join(members)})
    group("HX_INFINITY_ALL",names)
    family_groups = []
    for family,*_ in FAMILIES:
        family_name = "HX_INFINITY_FAMILY_"+family
        group(family_name,[r["name"] for r in records if r["family"]==family])
        family_groups.append(family_name)
    # Nested group: members are other groups, not models. Helix expands these.
    group("HX_INFINITY_DISTRICTS", family_groups)
    for role in sorted(set(r["role"] for r in records)):
        group("HX_INFINITY_ROLE_"+role.upper(),[r["name"] for r in records if r["role"]==role])
    for axis in (0,1,2):
        for sign in (0,1):
            group(f"HX_INFINITY_AXIS_{axis}_{sign}",
                  [r["name"] for r in records if (r["center"][axis]>=0)==bool(sign)])
    # District, role, axis and ring groups keep their original members. At the
    # full tier use larger local clusters to avoid thousands of overlapping
    # native render buffers around the same physical props.
    levels = (16, 32, 64, 128, 256, 512, 1024) if size == 10240 else (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
    for level in levels:
        for start in range(0,len(records),level):
            group(f"HX_INFINITY_HIER_{level:04d}_{start//level:04d}",names[start:start+level])
    for sector in range(24):
        group(f"HX_INFINITY_SECTOR_{sector:02d}", [r["name"] for r in records if int((math.atan2(r["center"][2],r["center"][0])%(2*math.pi))*24/(2*math.pi))==sector])
    # Musical travel paths overlap family, role and spatial groups.
    for label, families in (("ENCHANTED_FOREST", ("SPIRAL_TREE","MEGA_TREE")), ("STARDUST", ("ORNAMENT","SKY_STRUCTURE")), ("PORTALS", ("DOUBLE_HELIX","TUNNEL_3D")), ("AURORA", ("MATRIX_2D","VOXEL_GRID_3D")), ("BELLS_PROCESSION", ("ARCH","PIANO_COLUMN")), ("RIVER_OF_LIGHT", ("GROUND_WAVE","SPHERE"))):
        group("HX_INFINITY_MAGIC_"+label, [r["name"] for r in records if r["family"] in families])
    for ring in range(8):
        group(f"HX_INFINITY_RING_{ring:02d}", [r["name"] for r in records if min(7,int(math.hypot(r["center"][0],r["center"][2])/70))==ring])
    # Validate full channel allocation and group references before emitting artifacts.
    assert len(names)==len(set(names))
    assert all(a["end_channel"]+1==b["start_channel"] for a,b in zip(records,records[1:]))
    known=set(names)
    declared=set()
    for g in groups:
        members=g.attrib["models"].split(",")
        assert members and all(m in known or m in declared for m in members)
        declared.add(g.attrib["name"])
    output.parent.mkdir(parents=True,exist_ok=True)
    manifest.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(root).write(output,encoding="utf-8",xml_declaration=True)
    h=hashlib.sha256()
    with output.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    digest=h.hexdigest()
    meta={"name":"HELIX INFINITY UNIVERSE","panel":9,"tier":size,
          "model_count":len(records),"group_count":len(groups),
          "pixel_count":sum(r["nodes"] for r in records),"rgb_channel_count":next_channel-1,
          "sha256":digest,"families":dict(Counter(r["family"] for r in records)),
          "channel_map":records,"generated_xml":str(output),
          "status":"layout only; musical XSQ, native FSEQ and MP4 require verified Helix/xLights render"}
    with manifest.open('w', encoding='utf-8') as stream:
        json.dump(meta, stream, indent=2)
        stream.write('\n')
    return meta

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--size",type=int,choices=(128,512,2048,10240),default=10240)
    ap.add_argument("--output",type=Path,default=Path("test_runs/ultimate_showcase/xlights_rgbeffects_infinity.xml"))
    ap.add_argument("--manifest",type=Path,default=Path("test_runs/ultimate_showcase/infinity_manifest.json"))
    args=ap.parse_args()
    m=make_layout(args.output,args.manifest,args.size)
    print(json.dumps({k:v for k,v in m.items() if k!="channel_map"},indent=2))
if __name__=="__main__": main()
