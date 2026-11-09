"""Six independently composed shows using the verified native sculpture catalog."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math

import numpy as np

from models.ultimate_showcase import Garden, Sculpture, build_ultimate_garden, family, NATIVE_TYPES, CYAN, PINK, GOLD, MINT, VIOLET


@dataclass(frozen=True)
class Flavor:
    key: str
    title: str
    code: str
    description: str
    colors: tuple[str, str, str, str, str]
    pavilions: tuple[tuple[float, float, float], tuple[float, float, float]]  # x,z,scale

    @property
    def slug(self) -> str:
        return "Helix_"+self.title.replace(" & ","_and_").replace(" ","_")


FLAVORS = (
    Flavor("neon_circuit","Neon Circuit","NC","An asymmetric cyberpunk skyline: stepped DNA skyscrapers, luminous circuit avenues and spiral antenna farms.",
           ("#00F0FF","#FF3BC8","#FFF275","#65FF47","#926BFF"),((-139,-18,.65),(122,12,.65))),
    Flavor("enchanted_grove","Enchanted Grove","EG","A winding woodland crescent: emerald spiral canopies, rose-gold DNA trunks, fireflies and a low braided garden bridge.",
           ("#7DFFC2","#FFC29A","#FFF0BC","#9FE65B","#BBA1FF"),((-126,-48,.68),(131,-30,.6))),
    Flavor("celestial_orrery","Celestial Orrery","CO","A golden astronomical plaza: concentric orbital groves, suspended DNA halos and a tall paired observatory at the centre.",
           ("#9FD5FF","#C5A7FF","#FFD979","#E7F6FF","#6CA5FF"),((-137,-61,.62),(137,-61,.62))),
    Flavor("fire_and_ice","Fire & Ice","FI","Two opposing elemental kingdoms: hot volcanic spires and icy blue spirals meet across a luminous DNA bridge.",
           ("#FF6242","#76E5FF","#FFE0A6","#FFAD41","#A8C9FF"),((-140,-32,.7),(140,-32,.7))),
    Flavor("crystal_lagoon","Crystal Lagoon","CL","Terraced turquoise islands: low DNA reef arches, pearl spiral reeds and layered wave paths around a luminous lagoon.",
           ("#54F8DB","#8DC8FF","#FFF4D5","#B0FFF2","#BDAEFF"),((-138,8,.6),(132,-73,.6))),
    Flavor("midnight_masquerade","Midnight Masquerade","MM","A velvet theatrical fan: amethyst spiral plumes, garnet DNA balconies, gold proscenium arcs and a royal central throne.",
           ("#D4A2FF","#FF6F9B","#FFD27B","#9365FF","#D148AF"),((-140,-29,.64),(140,-29,.64))),
)
FLAVOR_BY_KEY = {f.key:f for f in FLAVORS}


def _move(m: Sculpture, origin, target, scale: float = 1) -> None:
    """Uniform affine move in both native screen coordinates and review nodes."""
    origin,target=np.asarray(origin,float),np.asarray(target,float)
    transform=lambda points:(np.asarray(points)-origin)*scale+target
    m.points=transform(m.points)
    if m.display in ("Poly Line","MultiPoint"):
        vertices=np.array([float(v) for v in m.attrs["PointData"].split(",")]).reshape(-1,3)
        m.attrs["PointData"]=",".join(f"{v:.6f}" for v in transform(vertices).flat)
        return  # These use absolute vertices and an identity screen location.
    anchor=np.array([float(m.attrs.get("WorldPos"+k,0)) for k in "XYZ"])
    anchor=transform(anchor)
    for i,k in enumerate("XYZ"):
        m.attrs["WorldPos"+k]=f"{anchor[i]:.6f}"
        if "Scale"+k in m.attrs:m.attrs["Scale"+k]=f"{float(m.attrs['Scale'+k])*scale:.9f}"
        if k+"2" in m.attrs:m.attrs[k+"2"]=f"{float(m.attrs[k+'2'])*scale:.9f}"
    for key in ("grid_spacing_ft","max_snap_error_ft","height_ft"):
        if key in m.details:m.details[key]*=scale


def _palette(m: Sculpture, flavor: Flavor) -> None:
    colors=flavor.colors
    if flavor.key=="fire_and_ice":
        colors=("#FF6242","#FFAD41","#FFE0A6","#FF8547","#FFD058") if m.points[:,0].mean()<0 else (
                "#76E5FF","#A8C9FF","#EEFAFF","#61BAFF","#B8FFFF")
    mapping=dict(zip((CYAN,PINK,GOLD,MINT,VIOLET),colors,strict=True))
    m.colors=[mapping.get(c,c) for c in m.colors]
    for key in list(m.attrs):
        if key.startswith("ChannelColor"):m.attrs[key]=colors[2]
    if m.display=="Label":
        m.attrs["LabelTextColor"]=colors[2]


def _catalog(g: Garden, f: Flavor) -> None:
    """Re-stage native gallery props; rebuild all DNA and spiral compositions."""
    original=build_ultimate_garden()
    for source in original.models:
        if source.details.get("spiral_tree") or source.details.get("double_helix") or source.name.startswith(("HX_CANOPY_CROWN","HX_NORTH_STAR")):
            continue
        m=deepcopy(source);m.name="HX_"+f.code+"_"+m.name.removeprefix("HX_")
        side=-1 if source.points[:,0].mean()<0 else 1
        if source.zone=="ORRERY_PAVILIONS":
            x,z,s=f.pavilions[0 if side<0 else 1]
            _move(m,(side*118,0,-53),(x,0,z),s)
            m.zone="NATIVE_PAVILIONS"
        elif source.zone=="NATIVE_TREE_GALLERY":
            index=int("Flat" in source.name or "Ribbon" in source.name)
            _move(m,(side*169,0,29 if not index else -30),(side*(173-8*index),0,45-index*87),.8)
        elif source.zone=="CRYSTAL_GARDEN":
            offsets={"neon_circuit":(78,-66),"enchanted_grove":(84,-88),"celestial_orrery":(102,-92),
                     "fire_and_ice":(73,-78),"crystal_lagoon":(40,-64),"midnight_masquerade":(77,-80)}
            x,z=offsets[f.key];_move(m,(side*53,0,-53),(side*x,0,z),.8)
        elif source.zone=="RIBBON_PROMENADE":
            _move(m,(0,0,-100),(0,0,-112),.92)
        elif source.zone=="SKY_JEWELS":
            # Six crystalline motifs remain as sky accents; forest layouts lower
            # them into lantern clearings, while the theatre makes a high frieze.
            y={"neon_circuit":6,"enchanted_grove":-21,"celestial_orrery":8,
               "fire_and_ice":0,"crystal_lagoon":-18,"midnight_masquerade":10}[f.key]
            _move(m,(0,0,0),(0,y,35),.9);m.zone="SKY_MOTIFS"
        elif source.name=="HX_INFINITY_RIBBON":
            # The native path is authored anew, rather than copying Aurora's lawn.
            t=np.linspace(0,math.tau,181)
            path=np.c_[65*np.sin(t),1+2*np.sin(t)**2,-123+9*np.sin(2*t)]
            if f.key=="neon_circuit":path=np.array([[-70,1,-124],[-70,1,-110],[0,1,-110],[0,1,-122],[70,1,-122],[70,1,-108]])
            elif f.key=="crystal_lagoon":path=np.c_[85*np.cos(t),1.2+1.5*np.sin(t)**2,-35+43*np.sin(t)]
            elif f.key=="celestial_orrery":path=np.c_[67*np.cos(t),1.2+np.sin(t)**2,-20+42*np.sin(t)]
            elif f.key=="midnight_masquerade":path=np.c_[95*np.cos(t),2+2*np.sin(t)**2,-67+30*np.sin(t)]
            elif f.key=="enchanted_grove":path=np.c_[70*np.sin(t),1+np.sin(t)**2,-89+19*np.cos(t)]
            g.poly(m.name,path,420,"SIGNATURE_PATH",f.title+" signature illuminated contour",f.colors[1]);continue
        elif source.zone=="WELCOME_CREST":
            _move(m,(0,0,-110),(0,0,-135),1)
            if m.display=="Label":m.attrs["LabelText"]=("HELIX "+f.title).upper()
        elif source.zone=="TECHNOLOGY_ALCOVES":
            _move(m,(side*184,0,-42),(side*186,0,-48),.75)
        _palette(m,f)
        m.design=f.title+" — "+m.design.replace("Helix Aurora",f.title)
        g.models.append(m)


def _dna(g: Garden, f: Flavor, name: str, x: float, z: float, height: float, radius: float,
         turns: float = 3, *, y: float = 0, ring: bool = False, bridge: bool = False) -> None:
    g.dna("HX_"+f.code+"_"+name,0 if bridge else x,0 if bridge else z,height,radius,turns,
          360 if height>65 else 180 if not ring else 320,"DNA_CATHEDRAL",y=0 if bridge else y,ring=ring)
    m=g.models[-1]
    if bridge:
        p=m.points.copy();points=np.c_[p[:,1]-height/2+x,-p[:,0]+y,p[:,2]+z]
        g.models.pop()
        m=g.custom(m.name,points,"DNA_BRIDGES","Horizontal double-helix bridge with full illuminated ladder rungs",
                   m.colors,m.submodels,details={**m.details,"axis":"horizontal"})
    _palette(m,f)


def _tree(g: Garden, f: Flavor, i: int, x: float, z: float, h: float, turns: float = 3,
          *, color_index: int = 3, radius_ratio: float = .17) -> None:
    g.tree(f"HX_{f.code}_SPIRAL_{i:02d}",x,z,h,h*radius_ratio,turns,2+i%2,112+(i%3)*16,"SPIRAL_GROVES")
    m=g.models[-1];m.colors=[(MINT,CYAN,VIOLET,PINK,GOLD)[color_index%5]]*len(m.points);_palette(m,f)


def _compose(g: Garden, f: Flavor) -> None:
    if f.key=="neon_circuit":
        for i,(x,z,h) in enumerate([(-65,42,70),(-27,23,96),(17,57,59),(58,38,81)]):
            _dna(g,f,f"SKYSCRAPER_{i}",x,z,h,7+i%2,3+i*.4)
        _dna(g,f,"TRANSIT_BRIDGE",0,-63,99,4,5,y=19,bridge=True)
        for i in range(8):_dna(g,f,f"STREET_BEACON_{i}",-94+i*27,-91,15+i%3*5,2.4,2.5)
        for i in range(36):
            side=-1 if i<18 else 1;j=i%18;row,col=divmod(j,6)
            _tree(g,f,i,side*(80+col*15),48-row*36,43-col*3-row*5,2.5+j*.07,color_index=row)
        for i in range(4):g.star(f"HX_NC_ROOFTOP_{i}",(-65,-27,17,58)[i],(76,102,65,87)[i],(42,23,57,38)[i],7,"SKY_CROWNS",color=f.colors[2])
    elif f.key=="enchanted_grove":
        for i in range(36):
            angle=math.pi*.08+(math.pi*.84)*(i%18)/17;radius=106+(i//18)*38
            _tree(g,f,i,radius*math.cos(angle),-13+radius*.52*math.sin(angle),
                  24+19*math.sin(angle)+(i//18)*7,2.5+i%5*.2,color_index=i%3)
        for i,(x,z,h) in enumerate([(-43,16,52),(3,42,73),(49,22,46)]):_dna(g,f,f"ANCIENT_TRUNK_{i}",x,z,h,6,3.4)
        _dna(g,f,"ROOT_BRIDGE",-14,-38,77,4,4.5,y=15,bridge=True)
        for i in range(8):
            a=math.pi+i*math.pi/7;_dna(g,f,f"LANTERN_PATH_{i}",72*math.cos(a),-39+38*math.sin(a),12+i%3*3,2.4,2.4)
        g.star("HX_EG_MOON_CROWN",3,80,42,10,"SKY_CROWNS",tips=7,color=f.colors[2])
    elif f.key=="celestial_orrery":
        _dna(g,f,"OBSERVATORY_WEST",-21,20,78,8,4)
        _dna(g,f,"OBSERVATORY_EAST",21,20,78,8,4)
        for i,(r,y,z) in enumerate([(22,15,-24),(33,34,12),(44,55,26)]):_dna(g,f,f"ORBITAL_HALO_{i}",0,z,0,r,9+i,y=y,ring=True)
        for i in range(8):
            a=math.tau*i/8;_dna(g,f,f"PLANET_MARKER_{i}",74*math.cos(a),-18+47*math.sin(a),15+i%3*4,2.8,2.5)
        for i in range(40):
            a=math.tau*(i%20)/20;r=108+(i//20)*36
            _tree(g,f,i,r*math.cos(a),-16+r*.5*math.sin(a),15+(i//20)*15+8*max(0,math.sin(a)),2.5+i%6*.2,color_index=i%3)
        g.star("HX_CO_POLARIS",0,98,25,15,"SKY_CROWNS",tips=7,color=f.colors[2])
    elif f.key=="fire_and_ice":
        for side in (-1,1):
            for i in range(3):_dna(g,f,f"ELEMENT_{side}_{i}",side*(27+i*30),32-i*13,82-i*18,7-i,3.2+i*.4)
            for i in range(20):
                row,col=divmod(i,5);_tree(g,f,i+(0 if side<0 else 20),side*(50+col*27),57-row*35,
                        43-col*4-row*5,2.5+i*.1,color_index=i%3)
            for i in range(4):_dna(g,f,f"SENTINEL_{side}_{i}",side*(26+i*24),-94,14+i%2*5,2.7,2.8)
        _dna(g,f,"ELEMENTAL_BRIDGE",0,-53,104,5,5,y=25,bridge=True)
        _dna(g,f,"CONFLUENCE_RING",0,3,0,17,10,y=17,ring=True)
        for side in (-1,1):g.star(f"HX_FI_CROWN_{side}",side*27,89,32,10,"SKY_CROWNS",tips=7,color=f.colors[2])
    elif f.key=="crystal_lagoon":
        islands=[(-94,28,12),(0,49,31),(90,14,18),(-57,-55,13),(53,-73,22)]
        for cluster,(x,z,base) in enumerate(islands):
            for i in range(8):
                a=math.tau*i/8;r=18+(i%2)*7
                _tree(g,f,cluster*8+i,x+r*math.cos(a),z+r*.7*math.sin(a),base+i%3*6,2.8+i*.2,color_index=cluster%3,radius_ratio=.2)
        _dna(g,f,"REEF_BRIDGE_WEST",-55,-15,64,4,4,y=18,bridge=True)
        _dna(g,f,"REEF_BRIDGE_EAST",51,-32,62,4,4,y=23,bridge=True)
        _dna(g,f,"TIDAL_HALO",0,-29,0,35,12,y=9,ring=True)
        _dna(g,f,"LIGHTHOUSE",0,53,76,6,4)
        for i in range(8):
            a=math.tau*i/8;_dna(g,f,f"PEARL_REED_{i}",90*math.cos(a),-29+53*math.sin(a),12+i%3*6,2.6,2.5)
        g.star("HX_CL_LIGHTHOUSE_CROWN",0,83,53,9,"SKY_CROWNS",tips=7,color=f.colors[2])
    else:  # midnight_masquerade
        _dna(g,f,"ROYAL_THRONE",0,22,89,10,4.2)
        _dna(g,f,"GILDED_BALCONY",0,-35,94,4,5,y=35,bridge=True)
        for side in (-1,1):
            for i in range(5):_dna(g,f,f"BALUSTRADE_{side}_{i}",side*(31+i*25),14-i*8,57-i*8,4.5,3)
        for i in range(36):
            side=-1 if i<18 else 1;j=i%18;row,col=divmod(j,6)
            x=side*(34+col*23+row*5);z=65-row*37
            _tree(g,f,i,x,z,64-col*7-row*12,2.5+row*.7+col*.18,color_index=row)
        for i in range(7):g.star(f"HX_MM_CROWN_{i}",-126+i*42,72+17*(1-abs(i-3)/3),52,7+(i==3)*5,"SKY_CROWNS",tips=5+i%3,color=f.colors[2])


def build_flavor(key: str) -> Garden:
    f=FLAVOR_BY_KEY[key]
    g=Garden(title="Helix "+f.title,slug=f.slug,description=f.description,palette=f.colors[:3])
    _catalog(g,f);_compose(g,f)
    start=1
    for m in g.models:m.start=start;start+=m.channels
    if len({m.name for m in g.models})!=len(g.models):raise ValueError("Duplicate flavor model names")
    if {family(m.display) for m in g.models}!=set(NATIVE_TYPES):raise ValueError("Incomplete native catalog")
    return g
