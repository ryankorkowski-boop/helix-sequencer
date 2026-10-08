"""Helix Aurora: deterministic native xLights sculpture garden.

Coordinates are xLights X-right / Y-up / Z-depth, in design feet. These are
planning dimensions, not a fabrication or controller-wiring specification.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import math
from typing import Any

import numpy as np

XLIGHTS_SOURCE = "6ceddc6b25a24d82754d4f9af28e18ee70b51f81"
# Creatable factory families, excluding groups (generated separately). Deprecated
# DMX aliases are not extra physical models. Matrix/tree orientations are variants.
NATIVE_TYPES = (
    "Arches", "Candy Canes", "Channel Block", "Circle", "Cube", "Custom",
    "DmxMovingHead", "DmxMovingHeadAdv", "DmxFloodlight", "DmxFloodArea",
    "DmxGeneral", "DmxSkull", "DmxServo", "DmxServo3d", "Image", "Label",
    "Window Frame", "Wreath", "Sphere", "Single Line", "Poly Line",
    "MultiPoint", "Tree", "Matrix", "Spinner", "Star", "Icicles",
)
CYAN, PINK, GOLD, MINT, VIOLET = "#64F5FF", "#FF70CE", "#FFD98A", "#82FFCD", "#A09AFF"


def family(display: str) -> str:
    if display.startswith("Tree"):
        return "Tree"
    if "Matrix" in display:
        return "Matrix"
    return display


@dataclass
class Sculpture:
    name: str
    display: str
    zone: str
    design: str
    attrs: dict[str, str]
    points: np.ndarray
    colors: list[str]
    submodels: dict[str, list[int]] = field(default_factory=dict)
    kind: str = "pixel"
    children: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    start: int = 0

    @property
    def channels(self) -> int:
        return len(self.points) * (3 if self.kind == "pixel" else 1)


def _points(points: Any) -> np.ndarray:
    return np.asarray(points, dtype=float).reshape(-1, 3)


def _line(a: Any, b: Any, count: int) -> np.ndarray:
    return np.linspace(a, b, count)


def _path(vertices: Any, count: int, *, closed: bool = False) -> np.ndarray:
    vertices = _points(vertices)
    if closed:
        vertices = np.vstack((vertices, vertices[0]))
    lengths = np.linalg.norm(np.diff(vertices, axis=0), axis=1)
    cumulative = np.r_[0, np.cumsum(lengths)]
    return np.column_stack([np.interp(np.linspace(0, cumulative[-1], count, endpoint=not closed), cumulative, vertices[:, k]) for k in range(3)])


class Garden:
    def __init__(self) -> None:
        self.models: list[Sculpture] = []

    def box(self, name: str, display: str, raw: Any, pos: tuple[float, float, float],
            size: tuple[float, float, float], zone: str, design: str, *,
            color: str = CYAN, attrs: dict[str, Any] | None = None, kind: str = "pixel",
            submodels: dict[str, list[int]] | None = None) -> Sculpture:
        """Scale a native coordinate model into a deliberately designed footprint."""
        raw = _points(raw)
        span = np.ptp(raw, axis=0)
        scale = np.asarray(size) / np.where(span > 1e-9, span, 1)
        center = (raw.min(axis=0) + raw.max(axis=0)) / 2
        anchor = np.asarray(pos) - center * scale
        data = {"WorldPos" + k: f"{anchor[i]:.6f}" for i, k in enumerate("XYZ")}
        data.update({"Scale" + k: f"{scale[i]:.6f}" for i, k in enumerate("XYZ")})
        data.update({k: str(v) for k, v in (attrs or {}).items()})
        m = Sculpture(name, display, zone, design, data, raw * scale + anchor,
                      [color] * len(raw), submodels or {}, kind)
        self.models.append(m)
        return m

    def poly(self, name: str, vertices: Any, count: int, zone: str, design: str,
             color: str = GOLD, *, multipoint: bool = False) -> Sculpture:
        vertices = _points(vertices)
        display = "MultiPoint" if multipoint else "Poly Line"
        points = vertices if multipoint else _path(vertices, count)
        attrs = {"WorldPosX": "0", "WorldPosY": "0", "WorldPosZ": "0",
                 "ScaleX": "1", "ScaleY": "1", "ScaleZ": "1",
                 "parm1": "1", "parm2": str(len(points)), "parm3": "1",
                 "NumPoints": str(len(vertices)), "PointData": ",".join(f"{v:.6f}" for v in vertices.flat),
                 "cPointData": "", "PolyStrings": "1", "MultiStrings": "1", "DropPattern": "1"}
        m = Sculpture(name, display, zone, design, attrs, points, [color] * len(points))
        self.models.append(m)
        return m

    def custom(self, name: str, points: Any, zone: str, design: str, colors: list[str],
               submodels: dict[str, list[int]], *, details: dict[str, Any] | None = None) -> Sculpture:
        """Serialize a sparse 3D grid without silently merging occupied cells.

        xLights CustomModel uses row/layer reversed Y/Z and the occupied bounding
        center. Snap once here: exported XML and preview use the identical nodes.
        """
        original = _points(points)
        spacing = .5
        for _ in range(7):
            cells = np.rint(original / spacing).astype(int)
            if len({tuple(c) for c in cells}) == len(cells):
                break
            spacing /= 2
        else:
            raise ValueError(f"Duplicate/coincident custom nodes: {name}")
        lower, upper = cells.min(axis=0), cells.max(axis=0)
        sizes = upper - lower + 1
        attrs = {"parm1": str(sizes[0]), "parm2": str(sizes[1]), "Depth": str(sizes[2]),
                 "CustomWidth": str(sizes[0]), "CustomHeight": str(sizes[1]), "CustomStrings": "1",
                 "String1": "1", "CustomModelCompressed": ";".join(
                     f"{i+1},{upper[1]-c[1]},{c[0]-lower[0]},{upper[2]-c[2]}" for i, c in enumerate(cells))}
        attrs.update({"WorldPos" + k: f"{(upper[i]+lower[i])*spacing/2:.6f}" for i, k in enumerate("XYZ")})
        attrs.update({"Scale" + k: str(spacing) for k in "XYZ"})
        m = Sculpture(name, "Custom", zone, design, attrs, cells * spacing, colors, submodels,
                      details={"grid_spacing_ft": spacing, "max_snap_error_ft": float(np.max(np.linalg.norm(cells*spacing-original, axis=1))), **(details or {})})
        self.models.append(m)
        return m

    def dna(self, name: str, x: float, z: float, height: float, radius: float,
            turns: float, nodes: int, zone: str, *, y: float = 0, ring: bool = False) -> None:
        t = np.linspace(0, 1, nodes, endpoint=not ring)
        theta = math.tau * turns * t
        if ring:
            orbit = math.tau*t
            def strand(phase: float) -> np.ndarray:
                r = radius + 2.5*np.cos(theta+phase)
                return np.c_[x+r*np.cos(orbit), y+2.5*np.sin(theta+phase), z+r*np.sin(orbit)]
        else:
            def strand(phase: float) -> np.ndarray:
                return np.c_[x+radius*np.cos(theta+phase), y+height*t, z+radius*np.sin(theta+phase)]
        a, b = strand(0), strand(math.pi)
        points = [*a, *b]
        colors = [CYAN]*nodes + [PINK]*nodes
        subs = {"STRAND_A": list(range(1, nodes+1)), "STRAND_B": list(range(nodes+1, 2*nodes+1)), "RUNGS": []}
        rung_indices = np.linspace(0, nodes-1, max(9, round(turns*10)), dtype=int)
        for number, idx in enumerate(rung_indices):
            # Full bars with their own pixels; strand endpoints already exist.
            count = max(5, round(np.linalg.norm(a[idx]-b[idx]) / .9))
            rung = _line(a[idx], b[idx], count+2)[1:-1]
            ids = list(range(len(points)+1, len(points)+len(rung)+1))
            subs["RUNGS"].extend(ids)
            subs.setdefault("RUNGS_ODD" if number % 2 else "RUNGS_EVEN", []).extend(ids)
            points.extend(rung)
            colors.extend([GOLD]*len(rung))
        subs["TOP"] = [i+1 for i, p in enumerate(points) if p[1] > y+height*.8] if not ring else subs["STRAND_A"][-nodes//8:]
        self.custom(name, points, zone, "Twisted orbital DNA halo" if ring else f"Two-strand DNA sculpture: {turns:g} turns, full illuminated ladder rungs",
                    colors, subs, details={"double_helix": True, "ring": ring, "strand_nodes": nodes,
                                          "rung_count": len(rung_indices), "height_ft": height, "turns": turns})

    def tree(self, name: str, x: float, z: float, height: float, radius: float,
             turns: float, strings: int, nodes: int, zone: str, *, display: str = "Tree 360", color: str = MINT) -> None:
        # Native TreeModel distributes spiral pixels by wire length, using ten
        # cone sections (not a uniform-height vertical-line approximation).
        render_h, render_w = nodes*3, nodes*3/1.8
        raw_radius, top = render_w/2, render_w/12
        if turns:
            gap = (raw_radius-top)/10
            lengths = np.array([math.hypot((math.tau*(raw_radius-gap*s)-gap/2)*turns/10, nodes/10) for s in range(10)])
            lengths /= lengths.sum()
            y_steps, angles = np.zeros(nodes), np.zeros(nodes)
            section = used = 0
            lights = max(1, math.floor(lengths[0]*nodes+.5))
            for idx in range(1, nodes):
                if used >= lights:
                    section += 1
                    used = 0
                    lights = nodes-idx if section == 9 else max(1, math.floor(lengths[section]*nodes+.5))
                y_steps[idx] = y_steps[idx-1] + nodes/10/lights
                angles[idx] = angles[idx-1] + turns*math.tau/10/lights
                used += 1
            fractions = y_steps/(nodes-1)
        else:
            fractions, angles = np.linspace(0, 1, nodes), np.zeros(nodes)
        rows = []
        for s in range(strings):
            degrees = int(display.split()[-1]) if display.split()[-1].isdigit() else 360
            if display in ("Tree Flat", "Tree Ribbon"):
                base = (s+.5-strings/2)*(5 if display.endswith("Ribbon") else 4)
                tip = (s+.5-strings/2)*.9
                raw = np.c_[base*(1-fractions)+tip*fractions, nodes*2*(fractions-.5), np.zeros(nodes)]
            else:
                arc = math.radians(degrees)
                angle = -arc/2+s*arc/(strings if degrees >= 350 else max(1, strings-1))+math.radians(3)+angles
                r = raw_radius+(top-raw_radius)*fractions
                raw = np.c_[r*np.sin(angle), render_h*(fractions-.5), r*np.cos(angle)]
            rows.extend(raw)
        m = self.box(name, display, rows, (x, height/2, z), (radius*2, height, radius*2), zone,
                     f"{'Spiral' if turns else display} tree; {strings} strands, {turns:g} twists; graduated canopy",
                     color=color, attrs={"parm1": strings, "parm2": nodes, "parm3": 1, "TreeSpiralRotations": turns,
                                         "TreeBottomTopRatio": 6, "TreeRotation": 3, "StrandDir": "Vertical"},
                     submodels={f"STRAND_{s+1:02d}": list(range(s*nodes+1, (s+1)*nodes+1)) for s in range(strings)})
        m.details.update({"spiral_tree": bool(turns), "turns": turns, "height_ft": height})

    def circle(self, name: str, x: float, y: float, z: float, diameter: float, zone: str,
               *, display: str = "Circle", color: str = GOLD, layers: int = 1) -> None:
        n = 96
        t = np.linspace(0, math.tau, n, endpoint=False)
        raw = np.concatenate([np.c_[n/2*(1-l*.2)*np.sin(t), n/2*(1-l*.2)*np.cos(t), np.zeros(n)] for l in range(layers)])
        self.box(name, display, raw, (x,y,z), (diameter,diameter,1), zone,
                 "Nested astronomical orbit rings" if layers > 1 else "Halo wreath with an open, readable center",
                 color=color, attrs={"parm1":1,"parm2":n*layers,"parm3":60,"LayerSizes": ",".join([str(n)]*layers)})

    def star(self, name: str, x: float, y: float, z: float, diameter: float, zone: str,
             tips: int = 5, color: str = GOLD) -> None:
        t = np.arange(tips*2)*math.pi/tips
        r = np.where(np.arange(tips*2)%2 == 0, 1, 1/2.618034)
        # Odd sampling avoids an exact lower-tip pixel falling outside the native
        # integer Star effect buffer (observed for 144-node six-point crowns).
        count=tips*24+int(tips%2==0)
        raw = _path(np.c_[r*np.sin(t), r*np.cos(t), np.zeros(len(t))], count, closed=True)*count/2
        self.box(name, "Star", raw, (x,y,z), (diameter,diameter,1), zone,
                 f"{tips}-point jewel crown; warm gold contrasts the cool spiral forest", color=color,
                 attrs={"parm1":1,"parm2":len(raw),"parm3":tips,"StarStartLocation":"Top-CW","starRatio":2.618034})


def build_ultimate_garden() -> Garden:
    g = Garden()
    # A cathedral skyline with space between each hero and the forest canopies.
    g.dna("HX_DNA_CATHEDRAL", 0, 28, 94, 12, 4.5, 420, "DNA_CATHEDRAL")
    for side in (-1,1):
        g.dna(f"HX_DNA_TOWER_{'WEST' if side < 0 else 'EAST'}", side*39, 20, 65, 8, 3.5, 288, "DNA_CATHEDRAL")
        for row in range(3):
            for index in range(4):
                x = side*(67+index*25+row*5)
                height = 59-index*9-row*8
                g.tree(f"HX_SPIRAL_{'W' if side < 0 else 'E'}_{row+1}_{index+1}", x, 29-row*25,
                       height, height*.17, 2.5+row*.5+index*.25, 2+row%2, 180-row*32,
                       "SPIRAL_FOREST", color=(MINT,VIOLET,CYAN)[row])
                if row == 0:
                    g.star(f"HX_CANOPY_CROWN_{side}_{index}",x,height+3,29,7,"SKY_JEWELS",tips=5+index%3)
        # A front ribbon of small trees gives the show a scale progression.
        for i in range(6):
            x = side*(62+i*16)
            h = 11+(i%3)*3
            g.tree(f"HX_SPIRAL_MINI_{side}_{i+1}", x, -100+5*math.sin(i), h, h*.24, 2+i*.2, 2, 96, "MINI_SPIRAL_GARDEN", color=MINT)
        for i in range(3):
            g.dna(f"HX_DNA_PATH_{side}_{i+1}", side*(22+i*15), -81, 13+i*3, 2.6, 2.5, 104, "DNA_WALK")
        g.dna(f"HX_DNA_GATE_{side}", side*22, -43, 32, 4, 3, 176, "DNA_WALK")
    g.dna("HX_DNA_ORBIT", 0,-26,0,27,12,512,"DNA_CATHEDRAL",y=12,ring=True)
    g.star("HX_NORTH_STAR",0,103,28,12,"SKY_JEWELS",tips=7)

    # Four intentionally different stock-tree personalities, beyond spiral trees.
    for display, x, z, color in [("Tree 360",-169,29,MINT),("Tree 180",169,29,VIOLET),
                                 ("Tree Flat",-169,-30,CYAN),("Tree Ribbon",169,-30,PINK)]:
        g.tree("HX_NATIVE_"+display.replace(" ","_"),x,z,28,9,0,12,48,"NATIVE_TREE_GALLERY",display=display,color=color)

    # Native spheres float over the twin matrix pavilions, like kinetic moons.
    for side in (-1,1):
        x,z = side*86,-53
        n,m = 20,24
        longitude = np.repeat(math.pi/2+.003-np.arange(n)*math.tau/n,m)
        latitude = np.tile(np.linspace(0,math.pi,m),n)
        radius=max(n,m)/3.6
        sphere = radius*np.c_[np.sin(latitude)*np.cos(longitude),np.cos(latitude),np.sin(latitude)*np.sin(longitude)]
        g.box(f"HX_ORRERY_MOON_{side}","Sphere",sphere,(x,36,z),(14,14,14),"ORRERY_PAVILIONS",
              "Pixel moon above a lyric pavilion; full-depth meridians",color=CYAN,attrs={"parm1":n,"parm2":m,"parm3":1})
        cols,rows = (40,20) if side<0 else (20,32)
        matrix = np.array([[c-cols/2,r-rows/2,0] for c in range(cols) for r in range(rows)])
        display = "Horiz Matrix" if side<0 else "Vert Matrix"
        g.box(f"HX_AURORA_{'HORIZONTAL' if side < 0 else 'VERTICAL'}",display,matrix,(x,17,z),(27,19,1),"ORRERY_PAVILIONS",
              "A wide lyric cinema" if side<0 else "Portrait generative-art canvas",color=VIOLET,
              attrs={"parm1": rows if side<0 else cols,"parm2":cols if side<0 else rows,"parm3":1})
        vertices=[[-1,-1,0],[-1,1,0],[1,1,0],[1,-1,0]]
        # Window Frame count = top + bottom + two sides.
        window=np.concatenate([_line(vertices[i],vertices[(i+1)%4],48) for i in range(4)])*np.array([25,24,1])
        g.box(f"HX_JEWEL_WINDOW_{side}","Window Frame",window,(x,17,z-.5),(30,22,1),"ORRERY_PAVILIONS",
              "Oversized jewel-box frame around the art canvas",color=GOLD,attrs={"parm1":48,"parm2":48,"parm3":48,"Rotation":"CW"})
        g.circle(f"HX_ORBIT_TRIPTYCH_{side}",side*124,21,-52,19,"ORRERY_PAVILIONS",layers=3,color=PINK)
        g.circle(f"HX_MOON_WREATH_{side}",side*124,39,-52,11,"ORRERY_PAVILIONS",display="Wreath",color=GOLD)
        # Native spinners form sunflowers on the opposite side of each moon.
        arms,per_arm=12,18
        a=np.repeat(np.linspace(0,math.tau,arms,endpoint=False),per_arm)
        r=np.tile(np.arange(per_arm)+.5+.4*per_arm,arms)
        spinner=np.c_[r*np.sin(a),r*np.cos(a),np.zeros(len(a))]
        g.box(f"HX_SOLAR_SPINNER_{side}","Spinner",spinner,(side*152,20,-54),(20,20,1),"ORRERY_PAVILIONS",
              "Twelve-arm hollow solar rosette; independent radial chase lanes",color=GOLD,
              attrs={"parm1":1,"parm2":per_arm,"parm3":arms,"Hollow":20,"Arc":360},
              submodels={f"RAY_{i+1:02d}":list(range(i*per_arm+1,(i+1)*per_arm+1)) for i in range(arms)})

    # A row of native arches and canes frames the entrance, in open pockets.
    for i,x in enumerate((-148,-120,-92,-64,64,92,120,148)):
        n=80; t=np.linspace(0,math.pi,n)
        pts=np.c_[x-11*np.cos(t),10*np.sin(t),np.full(n,-79)]
        m = Sculpture(f"HX_RIBBON_ARCH_{i+1:02d}","Arches","RIBBON_PROMENADE","A scalloped aurora entrance arch",{
            "WorldPosX":str(x-11),"WorldPosY":"0","WorldPosZ":"-79","X2":"22","Y2":"0","Z2":"0",
            "Height":".91","Angle":"0","parm1":"1","parm2":str(n),"parm3":"1","arc":"180"},pts,[PINK]*n)
        g.models.append(m)
    for side in (-1,1):
        # Five canes, with native hook geometry and a staggered-looking wave.
        points=[];cane_height=1.1;reverse=side<0
        for i in range(5):
            # Native 48-node canes: 32 upright + 16 hook pixels; internal
            # width16 and gap2. The three-point handle scales their height.
            x=i*18+(16 if reverse else 0)
            raw=[(x,y*cane_height) for y in range(32)]
            center=x+(-8 if reverse else 8)*cane_height
            for k in range(1,17):
                a=math.pi-math.pi*k/16
                raw.append((center+(-1 if reverse else 1)*math.cos(a)*8*cane_height,
                            (31+math.sin(a)*8)*cane_height))
            points.extend((side*170+px*15/88,py*15/88,-85) for px,py in raw)
        g.models.append(Sculpture(f"HX_CANDY_GARDEN_{side}","Candy Canes","RIBBON_PROMENADE","Five slim hooked candy reeds; mirrored portal accents",{
            "parm1":"5","parm2":"48","parm3":"1","WorldPosX":str(side*170),"WorldPosY":"0","WorldPosZ":"-85",
            "X2":"15","Y2":"0","Z2":"0","Height":"1.1","CandyCaneHeight":"1","CandyCaneReverse":"true" if side<0 else "false"},_points(points),[GOLD]*240))

    # Distinct native cube treatments: a crystal and a voxel lantern.
    for side in (-1,1):
        cube=np.array([[x-4,y-4,z-4] for z in range(8) for y in range(8) for x in range(8)])
        m=g.box(f"HX_VOXEL_LANTERN_{side}","Cube",cube,(side*53,10,-53),(13,17,13),"CRYSTAL_GARDEN",
                "Deep crystal voxel lantern; three-dimensional chase volume",color=VIOLET if side<0 else CYAN,
                attrs={"parm1":8,"parm2":8,"parm3":8,"Strings":1,"Style":"Horizontal Left/Right","Start":"Front Bottom Left"})
        m.attrs["RotateY"]="25" if side<0 else "-25"
        # Apply the same authored rotation in the preview.
        angle=math.radians(float(m.attrs["RotateY"]));center=np.array([side*53,10,-53]);p=m.points-center
        m.points=np.c_[p[:,0]*math.cos(angle)+p[:,2]*math.sin(angle),p[:,1],-p[:,0]*math.sin(angle)+p[:,2]*math.cos(angle)]+center

    # Icicles have a designed Fibonacci cadence, rather than identical defaults.
    drops=(3,5,8,5,3,2,3,5,8,13,8,5)
    for side in (-1,1):
        pts=[]
        for i in range(24):
            count=drops[i%len(drops)]
            pts.extend((i,-j,0) for j in range(count))
        g.box(f"HX_FIBONACCI_ICICLES_{side}","Icicles",pts,(side*86,4,-67),(28,7,1),"ORRERY_PAVILIONS",
              "Fibonacci-length ice fringe under the lyric pavilion",color=CYAN,
              attrs={"parm1":1,"parm2":len(pts),"parm3":1,"DropPattern":",".join(map(str,drops)),
                     "X2":28,"Y2":0,"Z2":0,"Height":-7/(12*28/23)})

    # The native polyline draws a real flowing infinity contour across the lawn.
    t=np.linspace(0,math.tau,181)
    g.poly("HX_INFINITY_RIBBON",np.c_[52*np.sin(t),.6+1.5*np.sin(t)**2,-112+8*np.sin(2*t)],420,
           "DNA_WALK","An illuminated figure-eight/infinity ribbon woven into the entrance",PINK)
    rng=np.random.default_rng(620)
    stars=np.c_[rng.uniform(-174,174,96),rng.uniform(63,85,96),rng.uniform(36,45,96)]
    stars=stars[np.abs(stars[:,0])>58]
    g.poly("HX_FIREFLY_CONSTELLATION",stars,len(stars),"SKY_JEWELS","Seeded, independently positioned native MultiPoint fireflies",GOLD,multipoint=True)
    for side in (-1,1):
        raw=_line((0,0,0),(1,0,0),180)
        m=g.box(f"HX_HORIZON_RAIL_{side}","Single Line",raw,(side*100,.3,-115),(145,.1,1),"RIBBON_PROMENADE",
                "Continuous low horizon rail for clean opposing chases",color=CYAN,attrs={"parm1":1,"parm2":180,"parm3":1})
        m.attrs.update({"WorldPosX":str(side*100-72.5),"WorldPosY":".3","X2":"145","Y2":"0","Z2":"0"})

    # Custom sixfold snowflakes belong to the show, without a fake native type.
    for side in (-1,1):
        for i in range(3):
            x=side*(72+i*34);y=70-i*8;z=38;pts=[]
            for a in np.arange(6)*math.pi/3:
                direction=np.array([math.sin(a),math.cos(a),0]);normal=np.array([math.cos(a),-math.sin(a),0])
                pts.extend(np.array([x,y,z])+direction*r for r in np.linspace(.5,5.5,15))
                for r in (2.8,4.2):
                    for sign in (-1,1):
                        start=np.array([x,y,z])+direction*r
                        pts.extend(_line(start+direction*.1+normal*.1*sign,start+direction*1+normal*1.1*sign,5))
            g.custom(f"HX_FRACTAL_SNOWFLAKE_{side}_{i}",pts,"SKY_JEWELS","Sixfold crystalline snowflake with branching tips",[CYAN]*len(pts),{})

    # Native image/label plus AC/DMX types live in their own technology alcove.
    # They are real control fixtures, never auto-assigned RGB music effects.
    g.box("HX_HELIX_CREST_IMAGE","Image",[(0,0,0)],(0,5,-108),(16,6,1),"WELCOME_CREST",
          "Original Helix Aurora luminous crest; portable image asset",color=GOLD,kind="control",
          attrs={"parm1":1,"Image":"assets/helix_crest.png","OffBrightness":80,"WhiteAsAlpha":"false","ScaleX":16,"ScaleY":6})
    g.box("HX_WELCOME_LABEL","Label",[(0,0,0)],(0,1,-120),(1,1,1),"WELCOME_CREST",
          "Native scene label: HELIX AURORA",color=GOLD,kind="control",
          attrs={"LabelText":"HELIX AURORA","LabelFontSize":20,"LabelTextColor":GOLD,"parm1":1})
    controls=[("Channel Block",16,"An amber legacy AC marquee"),
              ("DmxGeneral",8,"Eight-channel fountain/utility controller"),
              ("DmxMovingHead",16,"Classic cyan spotlight turret"),
              ("DmxMovingHeadAdv",16,"Full 3D magenta spotlight turret"),
              ("DmxFloodlight",3,"RGB garden uplighter"),
              ("DmxFloodArea",3,"Broad aurora lawn wash"),
              ("DmxSkull",26,"Articulated Halloween guest in the technology alcove"),
              ("DmxServo",2,"2D kinetic pinwheel ornament"),
              ("DmxServo3d",6,"Three-axis kinetic DNA wind sculpture")]
    for i,(display,n,design) in enumerate(controls):
        x=-184 if i<5 else 184;z=-10-(i%5)*16
        raw=np.c_[np.linspace(-1,1,n),np.zeros(n),np.zeros(n)]
        m=g.box("HX_TECH_"+display.replace(" ","_"),display,raw,(x,3,z),(8,1,1),"TECHNOLOGY_ALCOVES",design,
                color=GOLD,kind="control",attrs={"parm1":n,"parm2":1,"parm3":1,"NumChannels":n,
                      "DmxChannelCount":n,"X2":8,"Y2":0,"Z2":0,"DmxRedChannel":1,"DmxGreenChannel":2,
                      "DmxBlueChannel":3,"DmxStyle":"Moving Head Top","DmxBeamLength":8,"DmxBeamWidth":5})
        if display in ("DmxMovingHead","DmxMovingHeadAdv"):
            # Native head meshes scale beam length by their own body dimensions;
            # the stock eight-body-length cone overwhelms this feet-scale scene.
            m.attrs["DmxBeamLength"]="0.06"
        if display=="DmxMovingHeadAdv":
            # Its bundled meshes span ~32 raw units; the simple head uses a
            # unit-sized icon. Keep the real 3D fixture within its 8-foot alcove.
            m.attrs.update({"ScaleX":"0.25","ScaleY":"0.25","ScaleZ":"0.25"})
        if display=="Channel Block":
            m.attrs.update({f"ChannelColor{j+1}":GOLD for j in range(n)})
        if display in ("DmxServo","DmxServo3d"):
            m.attrs.update({"NumServos":3 if display.endswith("3d") else 1,"NumStatic":1,"NumMotion":3,"Bits16":1})
            for j in range(3 if display.endswith("3d") else 1):
                m.children.append((f"Servo{j+1}",{"Channel":str(j*2+1),"MinLimit":"1","MaxLimit":"65535","RangeOfMotion":"180","Axis":str(j)}))
            if display=="DmxServo":
                m.children.extend([("StaticImage1",{"Image":"assets/kinetic_base.png"}),
                                   ("MotionImage1",{"Image":"assets/kinetic_rotor.png"})])
            else:
                m.children.append(("StaticMesh1",{"ObjFile":"assets/kinetic_base.obj","Width":"2","Height":"2","Depth":"2"}))
                for j in range(3):
                    m.children.append((f"MotionMesh{j+1}",{"ObjFile":"assets/kinetic_dna.obj","Width":"3","Height":"5","Depth":"3",
                                                             "RotateY":str(j*120),"OffsetX":str((j-1)*2)}))
    names = [m.name for m in g.models]
    if len(names)!=len(set(names)):
        raise ValueError("Duplicate model name")
    start=1
    for m in g.models:
        m.start=start;start+=m.channels
    missing=set(NATIVE_TYPES)-{family(m.display) for m in g.models}
    if missing:
        raise ValueError(f"Missing native families: {missing}")
    return g


def garden_manifest(g: Garden) -> dict[str, Any]:
    return {"schema":"helix.ultimate_showcase.v1","name":"Helix Aurora — Ultimate Showcase",
            "coordinate_system":"x-right, y-up, z-depth; design feet", "xlights_source_ref":XLIGHTS_SOURCE,
            "coverage":dict(sorted(Counter(family(m.display) for m in g.models).items())),
            "native_families":list(NATIVE_TYPES), "native_coverage_complete":True,
            "model_count":len(g.models), "rgb_pixels":sum(len(m.points) for m in g.models if m.kind=="pixel"),
            "channel_count":sum(m.channels for m in g.models), "spiral_trees":sum(bool(m.details.get("spiral_tree")) for m in g.models),
            "double_helices":sum(bool(m.details.get("double_helix")) for m in g.models),
            "preview_contract":"Custom sparse-grid coordinates exactly match exported XML; native-family preview coordinates illustrate the authored geometry. Native xLights render/load evidence is recorded separately.",
            "models":[{"name":m.name,"native_type":m.display,"family":family(m.display),"zone":m.zone,"design":m.design,
                       "kind":m.kind,"nodes":len(m.points),"start_channel":m.start,"end_channel":m.start+m.channels-1,
                       "bounds_ft":[m.points.min(axis=0).round(6).tolist(),m.points.max(axis=0).round(6).tolist()],
                       "submodels":list(m.submodels),**m.details} for m in g.models]}
