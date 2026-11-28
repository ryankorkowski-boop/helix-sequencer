"""Dimensioned site plan, lighting furniture and camera compositions."""

from math import cos, pi, sin

import numpy as np

from .architecture import concert, gothic_estate, grand_estate, jungle, modern_estate, motor_district, nexus
from .geometry import Scene, bezier, ring


DISTRICTS = {
    "Grand": ("Grand Estate", (-88, 46), grand_estate),
    "Modern": ("Modern Estate", (0, 72), modern_estate),
    "Gothic": ("Gothic Estate", (88, 46), gothic_estate),
    "Jungle": ("Electric Jungle", (-88, -29), jungle),
    "Motor": ("Infinity Motor District", (88, -30), motor_district),
    "Arena": ("Helix Live Concert Arena", (0, -75), concert),
    "Nexus": ("Infinity Nexus", (0, 1), nexus),
}
COUNTS = {
    "Spiral_Tree": (44, 25, 37, 82, 41, 32, 59),
    "Arch": (53, 44, 54, 65, 71, 52, 61),
    "Tower_Tree": (7, 6, 7, 8, 7, 6, 7),
    "Mega_Tree": (4, 3, 4, 4, 4, 2, 3),
    "Monumental_Mega_Tree": (0, 0, 0, 0, 0, 1, 3),
    "Star": (24, 21, 29, 30, 26, 24, 26),
    "Matrix": (6, 11, 5, 9, 9, 10, 11),
    "Spinner": (19, 18, 23, 25, 23, 25, 27),
}
PALETTES = {
    "Grand": ("f7bb7b", "fff0bd", "6ecab4"),
    "Modern": ("45bff5", "476fed", "55fbe7"),
    "Gothic": ("845dff", "fb4878", "c497ec"),
    "Jungle": ("4af5b2", "fa4fca", "fe8e50"),
    "Motor": ("fa5549", "ffc36a", "6eacff"),
    "Arena": ("6f9dff", "bba1ff", "57f1ed"),
    "Nexus": ("4cdbe6", "fb6dba", "a77ff0"),
}
CAMERAS = {
    "overview": {"eye": (170,-242,190), "target": (0,-2,4), "width": 291},
    "plan": {"eye": (0,-.1,305), "target": (0,0,0), "width": 337},
    "front": {"eye": (0,-310,47), "target": (0,0,14), "width": 290},
    "side": {"eye": (290,-3,61), "target": (0,0,15), "width": 263},
    "Grand": {"eye": (-44,-32,29), "target": (-88,32,7), "width": 77},
    "Modern": {"eye": (58,10,25), "target": (0,68,9), "width": 66},
    "Gothic": {"eye": (51,-25,29), "target": (88,46,16), "width": 73},
    "Jungle": {"eye": (-130,-82,24), "target": (-88,-29,10), "width": 69},
    "Motor": {"eye": (42,-83,26), "target": (88,-30,3), "width": 69},
    "Arena": {"eye": (0,-128,12), "target": (0,-74,8.1), "width": 55},
    "Arena_wing": {"eye": (36,-123,20), "target": (0,-74,8), "width": 58},
    "Nexus": {"eye": (45,-73,35), "target": (0,1,21), "width": 91},
}


def tree(scene, district, family, label, x, y, height, radius):
    arms = {"Spiral_Tree": 1, "Tower_Tree": 5, "Mega_Tree": 10, "Monumental_Mega_Tree": 16}[family]
    scene.profile(district,"graphite",(x,y),[(0,.31+radius*.11),(.31,.4+radius*.11),
                 (.55,.19+radius*.08),(height,.095)],sides=8)
    t = np.linspace(0,1,32 if arms==1 else 15)
    for strand in range(arms):
        phase = 2*pi*(strand/arms + t*(3.3 if arms==1 else .16))
        points = np.c_[x+radius*(1-.96*t)*np.cos(phase),
                       y+radius*(1-.96*t)*np.sin(phase), .43+height*t]
        if arms==1:
            scene.tube(district,"pine",points,.071,sides=4)
            scene.light(district,family,label,points,.098)
        else:
            scene.tube(district,"graphite",points,.058,sides=4)
            if strand==0:
                rows=[]
            rows.append(points if strand%2==0 else points[::-1])
    if arms>1:
        scene.light(district,family,label,np.concatenate(rows),.14 if arms<10 else .18,row_width=len(t))


def arches(s,d,center,count):
    x,y=center
    # Two perimeter promenades and a third gallery, with clear space under each rib.
    for i in range(count):
        path, pair=divmod(i, (count+2)//3)
        n=(count+2)//3
        t=pair/max(1,n-1)
        if path==0:
            xx,yy,cross=x-33,y-22+44*t,(1,0)
        elif path==1:
            xx,yy,cross=x+33,y-22+44*t,(1,0)
        else:
            yy = y+(28 if d in ("Arena","Grand","Motor","Nexus","Jungle") else -32)
            xx,cross=x-28+56*t,(0,1)
        w=2.1+.25*sin(pair*.73)
        h=(2.85+.35*cos(pair*.55)) if path<2 else 3.45+.48*sin(pair*.85)
        a=np.linspace(0,pi,25)
        points=np.c_[xx+cross[0]*w*np.cos(a),yy+cross[1]*w*np.cos(a),.35+h*np.sin(a)]
        s.tube(d,"graphite",points-(0,0,.09),.093,sides=5)
        s.light(d,"Arch",f"Promenade_{i:03d}",points,.109)


def ornaments(s,d,center,counts):
    x,y=center
    for family in ("Spiral_Tree","Tower_Tree","Mega_Tree","Monumental_Mega_Tree"):
        count=counts[family]
        for i in range(count):
            side=(-1,1)[i%2]
            if family=="Spiral_Tree":
                lane,j=divmod(i//2,14)
                px=x+side*(27+lane*2.75)
                py=y-23+j*3.42+.65*cos(j*.9+lane)
                height=2.7+.56*(i%4)+(.9 if d=="Jungle" else 0)
                radius=.71+height*.15
            elif family=="Tower_Tree":
                px=x+side*(22+2.9*(i//2))
                py=y+(23 if d!="Arena" else -18)-(i//2)*5.7
                height=7.3+1.25*(i%3)
                radius=1.4+height*.10
            elif family=="Mega_Tree":
                px=x+side*(23-6*(i//2))
                py=y-(23 if d in ("Modern","Gothic","Nexus") else -24)
                height=10.8+(i%2)*2.3
                radius=2.7
            else:
                px=x+(-23,24,0)[i]
                py=y+(-12,-12,21)[i]
                height=19.5+2.7*i
                radius=4.2+i*.25
            tree(s,d,family,f"{i:03d}",px,py,height,radius)
    arches(s,d,center,counts["Arch"])
    for family in ("Star","Spinner"):
        for i in range(counts[family]):
            side=(-1,1)[i%2]
            lane,j=divmod(i//2,8)
            xx=x+side*(23.5+lane*5.1+.25*cos(j))
            yy=y-22+j*6.0+(2 if family=="Spinner" else 0)
            zz=(5.35 if family=="Star" else 2.9) + .55*(i%4) + lane*.76
            r=(.68+.14*(i%4)) if family=="Star" else (.68+.09*(i%5))
            s.tube(d,"graphite",[(xx,yy,0),(xx,yy,zz)],.08,sides=5)
            if family=="Star":
                vertices=[(xx+(r if k%2==0 else r*.47)*sin(k*pi/5),yy-.08,
                           zz+(r if k%2==0 else r*.47)*cos(k*pi/5)) for k in range(10)]
                outline=np.concatenate([np.linspace(a,b,4,endpoint=False)
                                        for a,b in zip(vertices,vertices[1:]+vertices[:1])])
                s.tube(d,"gold",vertices+[vertices[0]],.081,sides=5)
            else:
                outline=ring(xx,yy-.06,zz,r,n=40,vertical=True)
                s.tube(d,"chrome",np.r_[outline,outline[:1]],.055,sides=5)
                spokes=[]
                for j in range(6):
                    a=j*pi/3
                    edge=(xx+.92*r*cos(a),yy-.12,zz+.92*r*sin(a))
                    hub=(xx+.14*r*cos(a),yy-.13,zz+.14*r*sin(a))
                    spoke=np.linspace(hub,edge,6)
                    spokes.append(spoke[::(-1 if j%2 else 1)])
                    s.tube(d,"graphite",[hub,edge],.075,sides=4)
                outline=np.concatenate([outline,*spokes])
            s.light(d,family,f"{i:03d}",outline,.105)
    for i in range(counts["Matrix"]):
        side=(-1,1)[i%2]
        px=x+side*(28+i//6*4)
        py=y-19+i//2*7.7+.85*side
        height=2.2+(i%3)*.64
        s.box(d,"graphite",(px,py,height),(3.4,.39,2.4))
        for p in (-1.25,1.25):
            s.box(d,"graphite",(px+p,py,height/2),(.15,.18,height))
        s.surface(d,"Matrix",f"Promenade_{i:02d}",(px,py-.27,height),3.15,2.18,13,9)


def build_park():
    scene=Scene()
    scene.box("Ground","lawn",(0,0,-.47),(270,236,.9))
    scene.box("Ground","sand",(0,0,-.75),(276,241,.45))
    for i,(district,(_,center,builder)) in enumerate(DISTRICTS.items()):
        x,y=center
        scene.box(district,"lawn" if district in ("Grand","Gothic","Jungle") else "paving",
                  (x,y,.03),(74,61,.13))
        builder(scene,x,y)
        ornaments(scene,district,center,{family: counts[i] for family,counts in COUNTS.items()})
        for j in range(12):
            xx,yy=x+(j-5.5)*4.9,y-30
            scene.profile(district,"graphite",(xx,yy),[(0,.24),(.25,.19),(1.26,.11),(1.28,.2)],sides=8)
            scene.profile(district,"warm_glass",(xx,yy),[(1.28,.22),(1.56,.22),(1.69,.09)],sides=10)
            scene.light(district,"Lantern",f"Arrival_{j:02d}",ring(xx,yy,1.48,.25,n=10),.073)
        if district=="Nexus":
            continue
        # Approach paths join outside the main structures. They follow the same
        # curve in the mesh and the editable native lighting layout.
        direction = np.array([x,y,0],float)
        direction /= np.linalg.norm(direction)
        side = np.cross((0,0,1),direction)
        end = np.array([x,y,.26]) - direction * (32 if abs(x)<1 else 39)
        start = 16*direction + np.array([0,0,.19])
        path=bezier([start,start+8*direction+3*side,end-6*direction-3*side,end],35)
        for j in range(len(path)-1):
            a,b=path[j:j+2]
            scene.mesh(district,"paving",[a-side*2.2,b-side*2.2,b+side*2.2,a+side*2.2],[(0,1,2,3)])
        for k in (-1,1):
            edge=path+side*k*2.16+np.array([0,0,.075])
            scene.light(district,"Pathway",f"Nexus_Link_{k}",edge,.14)
    return scene
