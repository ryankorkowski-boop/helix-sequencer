"""Additional architectural showcase fixtures; does not replace the recovery bench."""
from pathlib import Path
from tools.layout_bench.generate_layouts import Layout, _rgb, line, rect, tree_outline, star_poly, arc, ellipse, RGB_TINT, write_layout_xml, write_template, parsed_stats, ROOT
import json

def build(style):
    l = Layout(style, style.replace("_", " ").title(), "pixel", "Architectural showcase")
    def path(name, pts, n, tint="roof"):
        return _rgb(l,name,"Poly Line",pts,n,RGB_TINT[tint],{"parm1":"1","parm2":str(n),"parm3":"1","NumPoints":str(len(pts))})
    def trees(xs):
        names=[]
        for i,x in enumerate(xs):
            h=110+30*(i%3)
            names.append(_rgb(l,f"Mini Tree {i+1}","Tree Flat",tree_outline(x,90,80,h),150,RGB_TINT["mini"],{"parm1":"6","parm2":"25","parm3":"1"}))
        l.group("All Mini Trees",names)
    if style=="alpine_chalet":
        path("Roofline A Frame",[(240,220,0),(600,650,0),(960,220,0)],300)
        path("Roofline Base",line(240,220,960,220),120)
        path("Peak Star",star_poly(600,680,28),60,"star")
        path("Window Frame",rect(540,300,120,100),100,"window")
        trees([100,200,330,870,1000,1100])
    elif style=="modern_geometry":
        for i,y in enumerate([320,480,600]):
            path(f"Fascia Roofline {i+1}",line(100,y,1100,y),200)
        pillars=[path(f"Column {i+1}",line(x,160,x,600),100,"line") for i,x in enumerate([100,350,850,1100])]
        l.group("All Columns",pillars)
        l.group("Driveway Stakes",[path(f"Stake {i+1}",line(x,40,x,100),20,"arch") for i,x in enumerate(range(100,1150,75))])
        for i,x in enumerate([180,440,700,960]):
            path(f"Window Frame {i+1}",rect(x,350,120,90),100,"window")
    elif style=="victorian_manor":
        for i,(x,y,w,h) in enumerate([(100,420,350,160),(450,470,350,180),(800,400,250,110)]):
            path(f"Gable Roofline {i+1}",[(x,y,0),(x+w/2,y+h,0),(x+w,y,0)],180)
        path("Turret Spire",[(850,180,0),(850,570,0),(970,690,0),(1090,570,0),(1090,180,0)],300)
        path("Porch Railing",line(100,230,800,230),180)
        for i,(x,y) in enumerate([(180,300),(400,350),(580,500),(690,300),(930,420)]):
            path(f"Window Frame {i+1}",rect(x,y,90,80),100,"window")
        trees([120,320,520,720,1120])
    elif style=="yard_only":
        _rgb(l,"Mega Tree","Tree 360",tree_outline(600,120,300,480),2400,RGB_TINT["mega"],{"parm1":"24","parm2":"100","parm3":"1"})
        l.group("All Arches",[path(f"Arch {i+1}",arc(x,60,160,95,25),100,"arch") for i,x in enumerate([100,300,500,700,900,1100])])
        for i,x in enumerate([160,350,850,1040]):
            path(f"Spinner {i+1}",star_poly(x,360,65,8),160,"spin")
        trees([100,300,900,1100])
    else:
        raise ValueError(style)
    l.group("Whole House",l.names())
    l.group("All Roofline",[n for n in l.names() if "Roofline" in n])
    return l

def main():
    out=ROOT/"fixtures"/"architectural_showcase"
    manifest=[]
    for style in ("alpine_chalet","modern_geometry","victorian_manor","yard_only"):
        l=build(style)
        folder=out/style
        p=folder/"xlights_rgbeffects.xml"
        t=folder/"template.xsq"
        write_layout_xml(l,p)
        write_template(l,t)
        stats=parsed_stats(p)
        if stats["models"]!=len(l.models) or stats["channels"]!=l.channel_count:
            raise ValueError(f"{style}: parser mismatch {stats}")
        manifest.append({"id":style,"layout":str(p.relative_to(ROOT)),"template":str(t.relative_to(ROOT)),**stats})
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
if __name__=="__main__":
    main()
