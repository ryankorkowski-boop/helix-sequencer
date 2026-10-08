"""Portable xLights show export; no dependency on the user's existing show."""
from __future__ import annotations

from collections import defaultdict
import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw

from models.ultimate_showcase import Garden, garden_manifest, CYAN, PINK, GOLD


def _write_xml(root: ET.Element, path: Path) -> None:
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def _ranges(nodes: list[int]) -> str:
    runs=[]
    for n in sorted(set(nodes)):
        if runs and n==runs[-1][-1]+1:
            runs[-1].append(n)
        else:
            runs.append([n])
    return ",".join(str(r[0]) if len(r)==1 else f"{r[0]}-{r[-1]}" for r in runs)


def model_xml(m, tag: str = "model") -> ET.Element:
    attrs={"name":m.name,"DisplayAs":m.display,"StringType":"RGB Nodes" if m.kind=="pixel" else "Single Color White",
           "StartChannel":str(m.start),"Controller":"","LayoutGroup":"Default",
           "StartSide":"B","Dir":"L","PixelSize":"2","Antialias":"1","Transparency":"0",
           "versionNumber":"7","parm1":"1","parm2":"1","parm3":"1", **m.attrs}
    root=ET.Element(tag,{k:str(v) for k,v in attrs.items()})
    for name,nodes in m.submodels.items():
        if nodes:
            ET.SubElement(root,"subModel",{"name":name,"layout":"horizontal","type":"ranges","line0":_ranges(nodes)})
    for name,attrs in m.children:
        ET.SubElement(root,name,attrs)
    return root


def _assets(path: Path, palette: tuple[str,str,str] = (CYAN,PINK,GOLD)) -> None:
    path.mkdir(exist_ok=True)
    cyan,pink,gold=palette
    # Original, generated graphics: not external artwork, no machine-local paths.
    for name,rotor in [("helix_crest.png",False),("kinetic_rotor.png",True),("kinetic_base.png",False)]:
        image=Image.new("RGBA",(512,192 if not rotor else 512));d=ImageDraw.Draw(image)
        if rotor:
            for i in range(12):
                a=i*np.pi/6
                d.line((256,256,256+220*np.sin(a),256+220*np.cos(a)),fill=gold,width=12)
            d.ellipse((225,225,287,287),fill=cyan)
        else:
            for phase,color in [(0,cyan),(np.pi,pink)]:
                p=[(32+448*t,96+60*np.sin(t*4*np.pi+phase)) for t in np.linspace(0,1,200)]
                d.line(p,fill=color,width=8)
            for t in np.linspace(0,1,24):
                s=60*np.sin(t*4*np.pi)
                d.line((32+448*t,96+s,32+448*t,96-s),fill=gold,width=3)
        image.save(path/name)
    # Simple, original mesh assets for the native 3D servo; quad-faced rods.
    def mesh(filename,segments):
        lines=["# Original Helix Aurora kinetic sculpture mesh"]
        index=1
        for a,b in segments:
            a,b=np.asarray(a,float),np.asarray(b,float)
            direction=b-a;axis=np.cross(direction,[0,1,0])
            if np.linalg.norm(axis)<.001:axis=np.cross(direction,[1,0,0])
            axis=axis/np.linalg.norm(axis)*.055
            other=np.cross(direction,axis);other=other/np.linalg.norm(other)*.055
            vertices=[p+sa*axis+sb*other for p in (a,b) for sa,sb in [(-1,-1),(1,-1),(1,1),(-1,1)]]
            lines.extend("v "+" ".join(f"{v:.6f}" for v in p) for p in vertices)
            lines.extend("f "+" ".join(str(index+i) for i in face) for face in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)])
            index+=8
        (path/filename).write_text("\n".join(lines)+"\n",encoding="utf-8")
    t=np.linspace(0,1,100)
    a=np.c_[np.cos(t*4*np.pi),t*5,np.sin(t*4*np.pi)]
    b=np.c_[-np.cos(t*4*np.pi),t*5,-np.sin(t*4*np.pi)]
    mesh("kinetic_dna.obj",[(s[i],s[i+1]) for s in (a,b) for i in range(len(s)-1)]+[(a[i],b[i]) for i in range(0,len(a),5)])
    mesh("kinetic_base.obj",[([-1,0,-1],[1,0,-1]),([1,0,-1],[1,0,1]),([1,0,1],[-1,0,1]),([-1,0,1],[-1,0,-1])])


def write_layout(g: Garden, output: Path) -> dict:
    output.mkdir(parents=True,exist_ok=True)
    _assets(output/"assets",g.palette)
    root=ET.Element("xrgb")
    models=ET.SubElement(root,"models")
    groups=ET.SubElement(root,"modelGroups")
    membership=defaultdict(list)
    from models.ultimate_showcase import family
    custom_dir=output/"models";custom_dir.mkdir(exist_ok=True)
    for m in g.models:
        models.append(model_xml(m))
        membership["HX_ZONE_"+m.zone].append(m.name)
        membership["HX_NATIVE_"+family(m.display).upper().replace(" ","_")].append(m.name)
        membership["HX_ALL_PIXELS" if m.kind=="pixel" else "HX_CONTROL_FIXTURES"].append(m.name)
        if m.details.get("double_helix"):
            membership["HX_DNA_ALL"].append(m.name)
            for part in ("STRAND_A","STRAND_B","RUNGS"):
                membership["HX_DNA_"+part].append(m.name+"/"+part)
            _write_xml(model_xml(m,"custommodel"),custom_dir/(m.name+".xmodel"))
        if m.details.get("spiral_tree"):
            membership["HX_SPIRAL_TREES"].append(m.name)
            membership["HX_SPIRALS_WEST" if m.points[:,0].mean()<0 else "HX_SPIRALS_EAST"].append(m.name)
    membership["HX_WHOLE_SHOW"]=[m.name for m in g.models]
    for name,members in sorted(membership.items()):
        ET.SubElement(groups,"modelGroup",{"name":name,"models":",".join(members),"layout":"minimalGrid",
                                            "LayoutGroup":"Default","GridSize":"600"})
    for tag in ("view_objects","effects","views","palettes","layoutGroups","perspectives","colors","Viewpoints"):
        e=ET.SubElement(root,tag)
        if tag=="effects":e.set("version","0007")
    # Native camera serialization, from ViewpointMgr. The generic -2000-unit
    # distance makes a feet-scale garden tiny on first import.
    camera={"name":"DEFAULT3D","is_3d":"1","posX":"0","posY":"0","posZ":"0",
            "angleX":"20","angleY":"7","angleZ":"0","distance":"-430","zoom":"1",
            "panx":"0","pany":"-35","panz":"25","zoom_corrx":"0","zoom_corry":"0"}
    ET.SubElement(root.find("Viewpoints"),"DefaultCamera3D",camera)
    ET.SubElement(root.find("Viewpoints"),"Camera",{**camera,"name":g.title.removeprefix("Helix ")+" overview"})
    settings=ET.SubElement(root,"settings")
    for name,value in {"backgroundBrightness":"0","storedLayoutGroup":"All Models","LayoutMode3D":"1",
                       "Display2DCenter0":"1","previewWidth":"480","previewHeight":"260"}.items():
        ET.SubElement(settings,name,{"value":value})
    _write_xml(root,output/"xlights_rgbeffects.xml")
    # Empty Controller means "Use Start Channel" in xLights. "No Controller"
    # silently reallocates every model alphabetically and breaks this channel map.
    # A standalone design needs no controller/output networks to render offline.
    network=ET.Element("Networks",{"computer":"","GlobalFPPProxy":""})
    _write_xml(network,output/"xlights_networks.xml")
    manifest=garden_manifest(g)
    manifest["groups"]={name:members for name,members in sorted(membership.items())}
    manifest["group_count"]=len(membership)
    (output/"showcase_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    with (output/"model_inventory.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f,lineterminator="\n");writer.writerow(["model","native_type","zone","nodes","start_channel","end_channel","design"])
        for m in manifest["models"]:writer.writerow([m[k] for k in ["name","native_type","zone","nodes","start_channel","end_channel","design"]])
    points=[{"name":m.name,"zone":m.zone,"type":m.display,"kind":m.kind,"start":m.start,
             "points":m.points.round(6).tolist(),"colors":m.colors} for m in g.models]
    (output/"preview_geometry.json").write_text(json.dumps(points,separators=(",",":")),encoding="utf-8")
    write_demo(g,output)
    (output/"README.txt").write_text(
        g.title.upper()+" — ULTIMATE SHOWCASE\n\n"
        f"{manifest['model_count']} models / {len(manifest['native_families'])} stock families / {manifest['spiral_trees']} spiral trees / {manifest['double_helices']} double helices\n\n"
        "1. Extract this entire folder; keep assets/ and models/ alongside the XML.\n"
        "2. In xLights, select this folder as a NEW show directory. Use xLights 2026.18 or newer.\n"
        f"3. Open Layout in 3D. Use Default preview and Restore Default ViewPoint or load {g.title.removeprefix('Helix ')} overview.\n"
        f"4. Open {g.slug}_Showcase.xsq for the 24-second lighting demonstration (no audio required).\n"
        f"5. Open {g.slug}_3D.html in a browser for the portable orbit/zoom design review.\n\n"
        "This is a standalone layout. Existing Helixia/user layouts and drummer assets are unchanged.\n"
        "DNA models expose STRAND_A, STRAND_B, RUNGS, RUNGS_EVEN, RUNGS_ODD and TOP submodels.\n"
        "Spiral tree strands, spinner rays, zones and native families also have sequencing groups.\n"
        "DMX, servo, AC, Image and Label models are isolated control fixtures; the demo sequences only RGB pixels.\n"
        "No physical controllers are configured. Models use absolute Start Channel; add controllers/ports for an actual installation.\n"
        "Dimensions are design feet, not an engineering/fabrication plan.\n"
        "Sparse custom geometry is identical in XML and review. Native stock shapes have illustrative review coordinates; consult native verification evidence.\n"
        "Factory/serialization reference: https://github.com/xLightsSequencer/xLights/tree/"+manifest['xlights_source_ref']+"\n",
        encoding="utf-8")
    return manifest


def demo_envelope(m, index: int) -> list[tuple[int,int,int,int]]:
    """Native On fades, shared by XSQ and optional fallback preview."""
    delay=0 if m.zone=="DNA_CATHEDRAL" else 1200+(index%7)*250
    return [(delay,6000,0,75),(6000,9000,75,35),(9000,12000,35,85),
            (12000,16000,85,50),(16000,21000,50,100),(21000,24000,100,25)]


def write_demo(g: Garden, output: Path) -> None:
    root=ET.Element("xsequence",{"BaseChannel":"1","ChanCtrlBasic":"0","ChanCtrlColor":"0","FixedPointTiming":"1","ModelBlending":"true"})
    head=ET.SubElement(root,"head")
    for name,text in {"version":"2026.18","author":"Helix","song":g.title+" lighting study",
                      "comment":"24-second layout lighting demonstration; no musical/detector claims",
                      "sequenceTiming":"50 ms","sequenceType":"Animation","sequenceDuration":"24.000","mediaFile":""}.items():
        ET.SubElement(head,name).text=text
    ET.SubElement(root,"nextid").text="1"
    palettes=ET.SubElement(root,"ColorPalettes");db=ET.SubElement(root,"EffectDB")
    displays=ET.SubElement(root,"DisplayElements");elements=ET.SubElement(root,"ElementEffects")
    palette_ids={};setting_ids={};identifier=1
    for i,m in enumerate(g.models):
        if m.kind!="pixel":continue
        ET.SubElement(displays,"Element",{"type":"model","name":m.name,"visible":"1","collapsed":"1"})
        element=ET.SubElement(elements,"Element",{"type":"model","name":m.name})
        layers=[]
        base_layer=ET.SubElement(element,"EffectLayer")
        if m.details.get("double_helix"):
            for part in ("STRAND_A","STRAND_B","RUNGS"):
                color=m.colors[m.submodels[part][0]-1]
                layers.append((ET.SubElement(element,"SubModelEffectLayer",{"name":part,"layer":"0"}),color))
        else:
            layers=[(base_layer,m.colors[0])]
        for layer,color in layers:
            if color not in palette_ids:
                palette_ids[color]=len(palette_ids)
                ET.SubElement(palettes,"ColorPalette").text=f"C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1"
            for start,end,b0,b1 in demo_envelope(m,i):
                key=(b0,b1)
                if key not in setting_ids:
                    setting_ids[key]=len(setting_ids)
                    ET.SubElement(db,"Effect").text=f"E_TEXTCTRL_Eff_On_Start={b0},E_TEXTCTRL_Eff_On_End={b1}"
                ET.SubElement(layer,"Effect",{"name":"On","ref":str(setting_ids[key]),"palette":str(palette_ids[color]),
                                             "startTime":str(start),"endTime":str(end),"id":str(identifier)})
                identifier+=1
    root.find("nextid").text=str(identifier)
    ET.SubElement(root,"DataLayers")
    ET.SubElement(root,"lastView").text="0"
    _write_xml(root,output/(g.slug+"_Showcase.xsq"))
