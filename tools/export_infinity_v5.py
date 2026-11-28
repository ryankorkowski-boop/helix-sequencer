"""Export exact V5 channel inventory without procedural substitutions."""
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from tools.infinity_canonical_band import append_canonical_six_band

def export(source, output, band=True):
    groups = defaultdict(list)
    with open(source, newline="") as f:
        for r in csv.DictReader(f):
            c = int(r["red_channel"])
            if (int(r["green_channel"]), int(r["blue_channel"])) != (c+1,c+2):
                raise ValueError("Invalid RGB triplet")
            p = tuple(float(r[k]) for k in ("x_m","z_m","y_m"))
            if not all(map(math.isfinite,p)):
                raise ValueError("Invalid coordinate")
            groups[r["model"]].append((c,p))
    addresses = sorted(c for g in groups.values() for c,p in g)
    if addresses != list(range(1,90721,3)) or len(groups)!=202:
        raise ValueError("Unexpected V5 inventory")
    root=ET.Element("xrgb")
    models=ET.SubElement(root,"models")
    mg=ET.SubElement(root,"modelGroups")
    families=defaultdict(list)
    for name, points in groups.items():
        points.sort()
        start=points[0][0]
        if [c for c,p in points]!=list(range(start,start+3*len(points),3)):
            raise ValueError("Noncontiguous model: "+name)
        n=len(points)
        ET.SubElement(models,"model",{"name":name,"DisplayAs":"Poly Line","LayoutGroup":"Default","StringType":"RGB Nodes","StartChannel":str(start),"parm1":"1","parm2":str(n),"parm3":"1","NumPoints":str(n),"PointData":",".join(str(v) for c,p in points for v in p),"cPointData":"","WorldPosX":"0","WorldPosY":"0","WorldPosZ":"0","ScaleX":"1","ScaleY":"1","ScaleZ":"1","PolyStrings":"1","PixelSize":"2"})
        families[name.split("_")[0]].append(name)
    for family,names in families.items():
        ET.SubElement(mg,"modelGroup",{"name":"HX_V5_"+family,"models":",".join(names)})
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    path=output/"xlights_rgbeffects.xml"
    ET.ElementTree(root).write(path,encoding="utf-8",xml_declaration=True)
    if band:
        append_canonical_six_band(path)
    return path

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("csv",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--without-band",action="store_true")
    a=p.parse_args()
    print(export(a.csv,a.output,not a.without_band))
