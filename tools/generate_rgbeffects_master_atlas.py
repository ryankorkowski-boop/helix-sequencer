#!/usr/bin/env python3
"""Build a print-scale, numbered atlas directly from the repository's xLights XML geometries.
No invented layouts. No render/approval claims. Python standard library only.
"""
import base64
import concurrent.futures
import datetime
import html
import json
import math
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

REPO = os.environ.get("GITHUB_REPOSITORY", "ryankorkowski-boop/helix-sequencer")
TOKEN = os.environ.get("GH_TOKEN", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "artwork/rgbeffects-master-poster-20261127")
BASE = "https://api.github.com/repos/" + REPO
OUTPUT = "artwork/helix_rgbeffects_master_atlas.svg"
INDEX = "artwork/helix_rgbeffects_master_atlas_index.json"
PALETTE = ["#39d9f5", "#ff6aa3", "#ffcf59", "#44efb4", "#bd95ff", "#ff9659", "#00d6e8"]
NUM_COLS, TILE_W, TILE_H, GAP, LEFT, TOP = 6, 1100, 725, 26, 72, 555

def api(path, payload=None, method=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Helix-Layout-Atlas-Generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN: headers["Authorization"] = "Bearer " + TOKEN
    if data is not None: headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=100) as resp:
        return json.load(resp)

def scalar(v, fallback=0):
    try:
        n = float(v)
        return n if math.isfinite(n) else fallback
    except (TypeError, ValueError):
        return fallback

def downsample(arr, maximum):
    if len(arr) <= maximum: return arr
    return [arr[round(i*(len(arr)-1)/(maximum-1))] for i in range(maximum)]

def title(path):
    if path == "xlights_rgbeffects.xml": return "Original Base Layout"
    parts = path.split("/")
    folder = parts[-2] if len(parts) > 1 else "Base"
    name = folder.replace("_", " ").replace("-", " ")
    name = re.sub(r"^\d+\s+", "", name)
    if "pre_neighbors" in path: return "AllModels Pre-Neighbors"
    if "source_backup" in path: return name + " Backup"
    return name.title().replace("Helixville", "Helixville")

def section(path):
    if "fixtures/layout_bench/" in path: return "LAYOUT BENCH"
    if "approved_concepts" in path: return "SHOWCASE CONCEPT"
    if "showcase/flavors" in path: return "SHOWCASE FLAVOR"
    if "helixville" in path: return "HELIXVILLE SERIES"
    if "allmodels" in path: return "ALLMODELS"
    return "HELIX / XLIGHTS"

def rank(path):
    if "fixtures/layout_bench/" in path: return 0
    if path == "xlights_rgbeffects.xml": return 1
    if path.startswith("allmodels/"): return 2
    if path.startswith("helixville"): return 3
    if path.startswith("showcase/flavors"): return 4
    if path.startswith("showcase/Experimental"): return 5
    if path.startswith("showcase/Helix_Aurora"): return 6
    if "approved_concepts" in path: return 7
    return 8

def model_lines(model, index):
    a = model.attrib
    x, y, z = (scalar(a.get("WorldPos" + axis)) for axis in "XYZ")
    sx, sy, sz = (scalar(a.get("Scale"+axis), 1) for axis in "XYZ")
    kind = a.get("DisplayAs", "").lower()
    color = a.get("CustomColor", "") or a.get("TagColour", "")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color or "") or color.lower() == "#000000":
        color = PALETTE[index % len(PALETTE)]
    if color.lower() == "#ffffff": color = "#c9eeff"
    pts = []
    raw = a.get("PointData")
    if raw:
        try:
            nums = list(map(float, raw.split(",")))
            pts = [(x+nums[i]*sx, y+nums[i+1]*sy, z+nums[i+2]*sz) for i in range(0,len(nums)-2,3)]
            pts = downsample(pts, 50)
        except ValueError:
            pts = []
    elif "CustomModelCompressed" in a:
        w = scalar(a.get("CustomWidth"), scalar(a.get("parm1"), 1))
        h = scalar(a.get("CustomHeight"), scalar(a.get("parm2"), 1))
        d = scalar(a.get("Depth"), scalar(a.get("parm3"), 1))
        # xLights compressed custom-model coordinates: node_index, y, x, z
        for text in downsample(a["CustomModelCompressed"].split(";"), 64):
            try:
                v = list(map(float, text.split(",")))
                if len(v) >= 4:
                    pts.append((x + (v[2]-w/2)*sx, y + (v[1]-h/2)*sy, z + (v[3]-d/2)*sz))
            except ValueError: pass
    else:
        X2, Y2 = abs(scalar(a.get("X2"))), abs(scalar(a.get("Y2")))
        basis = max(5, min(44, max(abs(sx)*13, abs(sy)*13, min(X2, Y2 or X2)*.3)))
        w = max(6, min(115, X2*.5 if X2 else basis))
        h = max(8, min(110, Y2*.5 if Y2 else basis*1.6))
        def add(px,py): pts.append((x+px,y+py,z))
        if "tree" in kind or "mega" in kind:
            for v in [(-w,-h),(0,h*1.3),(w,-h),(-w,-h),(-w*.72,-h*.4),(w*.72,-h*.4),(-w*.48,h*.25),(w*.48,h*.25)]: add(*v)
        elif "arch" in kind:
            for j in range(17): add(((j/16)-.5)*2*w, math.sin(j/16*math.pi)*h)
        elif "star" in kind:
            for j in range(11):
                theta = j*math.pi/5-math.pi/2
                r = w if j%2 == 0 else w*.45
                add(r*math.cos(theta),r*math.sin(theta))
        elif any(k in kind for k in ("circle","sphere","spinner","wreath")):
            for j in range(25): add(w*math.cos(j*math.pi/12), h*math.sin(j*math.pi/12))
        elif any(k in kind for k in ("matrix","window","frame")):
            for v in [(-w,-h),(w,-h),(w,h),(-w,h),(-w,-h),(-w,0),(w,0)]: add(*v)
        elif "snow" in kind or "face" in kind:
            for k in range(3):
                r = w*(1-k*.24)
                for j in range(17): add(r*math.cos(j*math.pi/8), -h*.55+k*h*.45+r*.8*math.sin(j*math.pi/8))
        elif any(k in kind for k in ("single line","poly line","line")):
            add(-w,-h*.35);add(w,h*.35)
        else:
            add(-w,-h*.5);add(w,h*.5)
    pts = [(u+v*.22, b+v*.17) for u,b,v in pts if math.isfinite(u) and math.isfinite(b) and math.isfinite(v)]
    return kind, color, downsample(pts, 48)

def format_pt(point):
    return f"{point[0]:.1f},{point[1]:.1f}"

def render_card(path, xml_bytes, index):
    root = ET.fromstring(xml_bytes)
    models = root.findall(".//models/model")
    shapes = [model_lines(m,i) for i,m in enumerate(downsample(models,220))]
    coords = [p for _,_,ps in shapes for p in ps]
    if not coords: coords=[(0,0),(1,1)]
    xx=sorted(p[0] for p in coords); yy=sorted(p[1] for p in coords)
    def extents(arr):
        a=arr[max(0,int(len(arr)*.003))]
        b=arr[min(len(arr)-1,int(len(arr)*.997))]
        if b<=a:b=a+1
        return a,b
    ax,bx=extents(xx); ay,by=extents(yy)
    scale=min(945/(bx-ax),465/(by-ay))
    def position(p):return ((p[0]-(ax+bx)/2)*scale+525, 248-(p[1]-(ay+by)/2)*scale)
    col=index%NUM_COLS; row=index//NUM_COLS
    tx=LEFT+col*(TILE_W+GAP);ty=TOP+row*(TILE_H+GAP)
    visuals=[]
    for kind,color,pts0 in shapes:
        pts=[position(p) for p in pts0]
        pts=[p for p in pts if -250<p[0]<1330 and -250<p[1]<850]
        if not pts:continue
        if kind=="custom":
            for px,py in downsample(pts,40):
                visuals.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{color}" opacity=".91"/>')
            if len(pts)>2:
                seq=" ".join(map(format_pt,pts))
                visuals.append(f'<polyline points="{seq}" fill="none" stroke="{color}" stroke-width="1.25" opacity=".38"/>')
        elif len(pts)>1:
            seq=" ".join(map(format_pt,pts))
            visuals.append(f'<polyline points="{seq}" fill="none" stroke="{color}" stroke-width="3" opacity=".9" stroke-linejoin="round" stroke-linecap="round"/>')
        else:
            px,py=pts[0]
            visuals.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.4" fill="{color}"/>')
    label=title(path)
    short=label if len(label)<=33 else label[:32]+"…"
    parent=path.rsplit("/",1)[0] if "/" in path else "repository root"
    svg = f'''<g transform="translate({tx},{ty})">
<rect width="{TILE_W}" height="{TILE_H}" rx="20" fill="#0b1629" stroke="#304963" stroke-width="2"/>
<rect x="18" y="77" width="1064" height="505" rx="11" fill="#020816" stroke="#17334d"/>
<g transform="translate(18,89)">{"".join(visuals)}</g>
<rect x="22" y="18" width="80" height="48" rx="12" fill="#22d3ee"/>
<text x="62" y="51" text-anchor="middle" font-size="32" font-weight="900" fill="#081523">{index+1:02d}</text>
<text x="118" y="49" font-size="21" letter-spacing="2" fill="#b3c5e1">{section(path)}</text>
<text x="28" y="631" font-size="40" font-weight="700" fill="#f6fcff">{html.escape(short)}</text>
<text x="28" y="682" font-size="23" fill="#9eb4cb">{len(models)} models · {html.escape(parent[:63])}</text>
</g>'''
    return svg, {"number":index+1,"title":label,"models":len(models),"path":path,"section":section(path)}

def fetch_blob(entry):
    payload=api("/git/blobs/"+entry["sha"])
    return base64.b64decode(payload["content"])

def put_file(path, content):
    raw=content.encode("utf-8")
    payload={"message":"Generate numbered XML-derived RGBEffects master layout atlas",
        "content":base64.b64encode(raw).decode("ascii"), "branch":BRANCH}
    return api("/contents/"+path,payload,"PUT")

def main():
    tree=api("/git/trees/"+os.environ.get("GITHUB_SHA", BRANCH.replace("/","%2F"))+"?recursive=1")
    unique={}
    for item in tree["tree"]:
        if item["type"] == "blob" and re.search(r"rgbeffects.*\.xml$",item["path"],re.I):
            unique.setdefault(item["sha"],item)
    files=sorted(unique.values(),key=lambda e:(rank(e["path"]), e["path"].lower()))
    print(f"Found {len(files)} unique XML blobs",flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        xmls=list(pool.map(fetch_blob,files))
    cards=[]; index=[]
    for i,(entry,body) in enumerate(zip(files,xmls)):
        try:
            card,record=render_card(entry["path"],body,i)
        except Exception as exc:
            raise RuntimeError(f"Cannot render source layout {entry['path']}: {exc}") from exc
        cards.append(card);index.append(record)
    width=LEFT*2+NUM_COLS*TILE_W+(NUM_COLS-1)*GAP
    height=TOP+math.ceil(len(cards)/NUM_COLS)*(TILE_H+GAP)+145
    head=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<title>Helix Master RGBEffects Layout Atlas — {len(cards)} Unique XML Layouts</title>
<desc>Actual xLights model geometry projected to two-dimensional views from repository XML. These are static layout diagrams, not light choreography or video renders.</desc>
<rect width="{width}" height="{height}" fill="#030b18"/>
<defs><linearGradient id="stripe"><stop stop-color="#22d3ee"/><stop offset=".5" stop-color="#a78bfa"/><stop offset="1" stop-color="#f472b6"/></linearGradient></defs>
<rect width="{width}" height="15" fill="url(#stripe)"/>
<text x="75" y="155" fill="#f8fdff" font-size="112" font-weight="900" letter-spacing="5">HELIX MASTER LAYOUT ATLAS</text>
<text x="78" y="244" fill="#67e8f9" font-size="54" font-weight="750">{len(cards)} UNIQUE RGBEFFECTS XML LAYOUTS · NUMBERED VISUAL INVENTORY</text>
<text x="78" y="320" fill="#bbcbdd" font-size="30">Actual xLights models and spatial coordinates · No invented layouts · Geometry projections, not sequenced lighting renders</text>
<text x="78" y="378" fill="#8da4bf" font-size="27">Repository: {html.escape(REPO)} · Branch: {html.escape(BRANCH)} · {datetime.date.today().isoformat()}</text>
<line x1="75" x2="{width-75}" y1="435" y2="435" stroke="url(#stripe)" stroke-width="5"/>
'''
    end=f'<text x="76" y="{height-63}" fill="#819eb8" font-size="24">Identical XML blob backups consolidated · Source index available alongside poster · Scene geometry is not visual-quality approval</text></svg>'
    svg=head+"\n".join(cards)+end
    put_file(OUTPUT,svg)
    put_file(INDEX,json.dumps(index,indent=2,ensure_ascii=False)+"\n")
    print(f"Saved {OUTPUT}: {len(svg):,} characters; {len(index)} layout records.",flush=True)

if __name__=="__main__":
    main()
