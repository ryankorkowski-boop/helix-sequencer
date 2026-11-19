"""Build six distinct native shows, a comparison gallery and review packages."""
from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import zipfile

from PIL import Image, ImageDraw

from models.showcase_flavors import FLAVORS, FLAVOR_BY_KEY, build_flavor
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_helpers.ultimate_showcase_preview import write_previews, _font
from tools.build_ultimate_showcase_layout import package_showcase
from tools.audit_ultimate_showcase_native import audit_native


def build_one(key: str, root: Path, *, xlights: Path | None = None, video: bool = True) -> dict:
    g=build_flavor(key);out=root/g.slug;manifest=write_layout(g,out)
    native=None;proof=None
    if xlights:
        env={**os.environ,"XL_NO_GPU_COMPUTE":"1"}
        command=[str(xlights.resolve()),"--headless","-q","-s",str(out.resolve()),"-od",str(out.resolve()),str((out/(g.slug+"_Showcase.xsq")).resolve())]
        with (out/"native_render.log").open("w") as log:
            subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        native=out/(g.slug+"_Showcase.fseq")
        proof=audit_native(out,garden=g)
    preview=write_previews(g,out,video=video,fseq=native)
    summary={"key":key,"title":g.title,"slug":g.slug,"description":g.description,"palette":list(g.palette),
             "models":manifest["model_count"],"groups":manifest["group_count"],"native_families":27,
             "spiral_trees":manifest["spiral_trees"],"double_helices":manifest["double_helices"],
             "rgb_pixels":manifest["rgb_pixels"],"channels":manifest["channel_count"],
             "native_verified":bool(proof),**preview}
    (out/"BUILD_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    package_showcase(out)
    return summary


def collection_gallery(root: Path, summaries: list[dict], *, tour: bool = True) -> None:
    contact=Image.new("RGB",(1920,1080),(7,12,23));draw=ImageDraw.Draw(contact)
    draw.text((36,24),"SIX FLAVORS  /  HELIX SHOWCASE",font=_font(35),fill="#DDF6FF")
    draw.text((38,76),"Six new compositions • Native xLights models • Spiral forests and volumetric DNA",font=_font(18),fill="#8DA9BC")
    cards=[]
    for i,s in enumerate(summaries):
        slug=s["slug"];x=36+(i%3)*632;y=121+(i//3)*454
        image=Image.open(root/slug/(slug+"_Night.png")).convert("RGB").resize((610,343),Image.Resampling.LANCZOS)
        contact.paste(image,(x,y));draw.text((x+6,y+350),s["title"],font=_font(25),fill=s["palette"][0])
        draw.text((x+6,y+386),f"{s['models']} models  /  {s['spiral_trees']} spirals  /  {s['double_helices']} DNA",font=_font(17),fill="#A8C0CF")
        swatches=''.join(f'<i style="background:{c}"></i>' for c in s['palette'])
        video=f'<a href="{slug}/{slug}_Showcase.mp4">Watch lighting preview ↗</a>' if s["mp4_seconds"] else ''
        cards.append(f'''<article><a href="{slug}/{slug}_3D.html"><img src="{slug}/{slug}_Night.png" alt="{html.escape(s['title'])} night layout"></a>
<div class="body"><div class="swatches">{swatches}</div><h2>{html.escape(s['title'])}</h2><p>{html.escape(s['description'])}</p>
<div class="counts">{s['models']} models · {s['spiral_trees']} spirals · {s['double_helices']} DNA</div>
<nav><a href="{slug}/{slug}_3D.html">Explore in 3D ↗</a>{video}<a href="{slug}_Ultimate_Showcase.zip">Download show ↓</a></nav></div></article>''')
    contact.save(root/"Helix_Six_Flavors_Comparison.png")
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Six Flavors | Helix Showcase</title><style>*{box-sizing:border-box}body{margin:0;background:#070c17;color:#dcecf5;font:16px system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:64px 30px}header{max-width:850px;margin-bottom:48px}small{color:#70e4ec;letter-spacing:.25em}h1{font-size:clamp(38px,6vw,72px);font-weight:500;letter-spacing:-.035em;margin:16px 0}header p{font-size:19px;line-height:1.6;color:#9eb5c6}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:26px}article{background:#0c1625;border:1px solid #203448;border-radius:18px;overflow:hidden}img{width:100%;display:block}.body{padding:28px}h2{font-size:28px;font-weight:500;margin:16px 0 12px}.body p{line-height:1.65;color:#abc0cf;min-height:80px}.counts{font-size:13px;color:#c1d4df;margin:20px 0}nav{display:flex;flex-wrap:wrap;gap:16px}a{color:#8aebf4;text-decoration:none}a:hover{text-decoration:underline}.swatches{display:flex;gap:8px}.swatches i{width:36px;height:5px;border-radius:3px}footer{margin-top:50px;color:#849ead;font-size:14px;line-height:1.8}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:32px 18px}.body{padding:22px}}</style>
<main><header><small>HELIX / THE SHOWCASE COLLECTION</small><h1>Six different worlds.<br>One love of light.</h1><p>Explore cyberpunk, woodland, celestial, elemental, aquatic and theatrical compositions. Every show includes all27 native model families, real spiral trees and three-dimensional double helices.</p><a href="Helix_Six_Flavors_Comparison.png">Open the comparison image ↗</a> · <a href="Helix_Six_Flavors_Layouts.zip">Download all six native layouts ↓</a>__TOUR__</header><section class="grid">__CARDS__</section><footer>Open any extracted show folder as a new xLights2026.18+ show. Keep its assets alongside the XML. Control/servo fixtures are reviewed in xLights; the RGB lighting studies have no audio. Custom grids are exact; stock review paths illustrate the design. Each show is an independent, scalable composition.<br>The original Helix Aurora remains preserved as the seventh option.</footer></main></html>'''
    if tour and all(s["mp4_seconds"] for s in summaries) and len(summaries)==6:
        _tour(root,summaries)
        tour_link=' · <a href="Helix_Six_Flavors_Tour.mp4">Watch the 36-second collection tour ↗</a>'
    else:tour_link=''
    page=page.replace('__CARDS__',''.join(cards)).replace('__TOUR__',tour_link)
    page=page.replace('all27','all 27').replace('xLights2026.18','xLights 2026.18')
    (root/"index.html").write_text(page,encoding="utf-8")
    (root/"collection_manifest.json").write_text(json.dumps({"layouts":summaries,"original_aurora_preserved":True},indent=2)+"\n")
    (root/"README.txt").write_text("HELIX — SIX ADDITIONAL SHOWCASE FLAVORS\n\nOpen index.html for the visual comparison and links.\nEach show lives in its own folder; choose one as a NEW xLights2026.18+ show directory.\nEach individual show ZIP includes its original assets, reusable DNA models, XSQ, images and interactive viewer.\nNative-verified builds also include the rendered FSEQ,24s MP4 and palette verification.\nHelix_Six_Flavors_Layouts.zip includes all six native layouts and review images/viewers; videos are separate to keep this download small.\nThe36s tour extracts six seconds from each native-lighting MP4. No audio or musical correctness claim.\nOriginal Aurora, existing layouts and drummer remain unchanged.\n")
    # All native layouts and reviewers in one modest download; full movies stay
    # in individual packages. Avoid including archives inside this archive.
    # The compact archive has its own gallery: movie/ZIP links only belong to
    # the full output directory. Every link in an extracted archive must work.
    archive_page=page.replace(' · <a href="Helix_Six_Flavors_Layouts.zip">Download all six native layouts ↓</a>','')
    if tour_link:archive_page=archive_page.replace(tour_link,'')
    for s in summaries:
        slug=s['slug']
        archive_page=archive_page.replace(f'<a href="{slug}/{slug}_Showcase.mp4">Watch lighting preview ↗</a>','')
        archive_page=archive_page.replace(f'<a href="{slug}_Ultimate_Showcase.zip">Download show ↓</a>',f'<a href="{slug}/README.txt">Import instructions ↗</a>')
    with zipfile.ZipFile(root/"Helix_Six_Flavors_Layouts.zip","w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("Helix_Six_Flavors/index.html",archive_page)
        for name in ("README.txt","Helix_Six_Flavors_Comparison.png","collection_manifest.json"):
            z.write(root/name,Path("Helix_Six_Flavors")/name)
        for s in summaries:
            folder=root/s["slug"]
            checksums=json.loads((folder/'bundle_checksums.json').read_text())
            portable={name:digest for name,digest in checksums.items() if Path(name).suffix!='.mp4'}
            for name in sorted(portable):
                p=folder/name
                z.write(p,Path("Helix_Six_Flavors")/p.relative_to(root))
            z.writestr(f"Helix_Six_Flavors/{s['slug']}/bundle_checksums.json",json.dumps(portable,indent=2)+'\n')


def _tour(root: Path, summaries: list[dict]) -> None:
    command=["ffmpeg","-v","error","-y"]
    for s in summaries:command += ["-ss","16","-t","6","-i",str(root/s['slug']/(s['slug']+"_Showcase.mp4"))]
    graph=';'.join(f'[{i}:v]scale=1280:720,setsar=1,setpts=PTS-STARTPTS[v{i}]' for i in range(6))
    graph+=';'+''.join(f'[v{i}]' for i in range(6))+'concat=n=6:v=1:a=0[v]'
    command += ["-filter_complex",graph,"-map","[v]","-an","-r","20","-c:v","libx264","-crf","23","-preset","fast","-pix_fmt","yuv420p","-movflags","+faststart",str(root/"Helix_Six_Flavors_Tour.mp4")]
    subprocess.run(command,check=True,timeout=180)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("outputs/showcase_flavors"))
    parser.add_argument("--flavor",choices=list(FLAVOR_BY_KEY))
    parser.add_argument("--xlights",type=Path,help="Native AppRun path; supply a working DISPLAY or wrap this command with xvfb-run")
    parser.add_argument("--no-video",action="store_true")
    parser.add_argument("--gallery-only",action="store_true",help="Rebuild comparison/collection ZIP from existing completed shows")
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    if args.gallery_only:
        summaries=[json.loads((args.output/f.slug/"BUILD_SUMMARY.json").read_text()) for f in FLAVORS]
    else:
        keys=[args.flavor] if args.flavor else list(FLAVOR_BY_KEY)
        summaries=[]
        for key in keys:
            summary=build_one(key,args.output,xlights=args.xlights,video=not args.no_video)
            summaries.append(summary);print(json.dumps(summary),flush=True)
    if len(summaries)==6:collection_gallery(args.output,summaries,tour=not args.no_video)


if __name__=="__main__":main()
