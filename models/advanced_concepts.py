"""Finite, artwork-guided geometry for the approved perspective round (23–42)."""
from __future__ import annotations

import math
import numpy as np


def cube(s, center, size, color, label='CUBE', yaw=0):
    c=np.asarray(center);r=size/2
    raw=np.array([[x,y,z] for x in (-r,r) for y in (-r,r) for z in (-r,r)])
    vertices=raw.copy();a=math.radians(yaw)
    vertices[:,[0,2]]=raw[:,[0,2]]@np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
    vertices+=c
    for i,p in enumerate(raw):
        for j,q in enumerate(raw[i+1:],i+1):
            if np.count_nonzero(p!=q)==1:s.path(label,[vertices[i],vertices[j]],'CUBES',color,65)
    return vertices


def waves(s):
    for z in (35,55,75):
        x=np.linspace(-145,145,200)
        s.add('WAVE_CONTOUR',np.c_[x,7+7*np.sin(x/22+z/20),np.full(len(x),z)],'WAVES',0)


def whale(s, center=(0,65,0), scale=1, angle=35, zone='WHALE'):
    """Elliptic ribs, pointed head, paired flukes and separate pectoral fins."""
    a=math.radians(angle);c=np.asarray(center)
    def transform(p):
        p=np.asarray(p,float)*scale
        return np.c_[p[:,0]*math.cos(a)-p[:,1]*math.sin(a),
                     p[:,0]*math.sin(a)+p[:,1]*math.cos(a),p[:,2]]+c
    t=np.linspace(0,math.tau,120,endpoint=False)
    for x in np.linspace(-85,75,15):
        r=24*math.sqrt(max(.025,1-(x/90)**2))*(.75+.25*(x+85)/160)
        s.add('WHALE_RIB',transform(np.c_[np.full(len(t),x),r*np.cos(t),r*.65*np.sin(t)]),zone,0)
    for phase in (0,math.pi/2,math.pi,3*math.pi/2):
        x=np.linspace(-88,88,160);r=24*np.sqrt(np.maximum(.005,1-(x/90)**2))
        s.add('WHALE_SPINE',transform(np.c_[x,r*np.cos(phase),r*.65*np.sin(phase)]),zone,2)
    for side in (-1,1):
        s.path('WHALE_FLUKE',transform([(-82,0,0),(-119,side*23,side*12),(-110,side*3,side*19),(-83,-3,0)]),zone,1,90)
        s.path('WHALE_FIN',transform([(0,-12,side*10),(14,-54,side*20),(32,-20,side*12)]),zone,0,80)
    eye=np.c_[68+3*np.cos(t[:60]*2),9+3*np.sin(t[:60]*2),np.full(60,13)]
    s.add('WHALE_EYE',transform(eye),zone,2)


def manta(s, center=(0,70,0), wing=0, tail=0, zone='MANTA'):
    c=np.asarray(center)
    for side in (-1,1):
        for rib in range(6):
            t=np.linspace(0,1,120)
            x=side*(12+115*t);y=(15+wing)*np.sin(t*math.pi/2)-rib*4*(1-t)
            z=-12+rib*7-(45-rib*4)*np.sin(t*math.pi/2)
            s.add('MANTA_WING_RIB',np.c_[x,y,z]+c,zone,rib%2)
        s.path('MANTA_WING_EDGE',np.array([(side*12,12,-12),(side*128,15+wing,-56),
                                          (side*72,-17,24),(side*14,-10,20)])+c,zone,1,170)
    s.ring('MANTA_BODY',c,20,15,zone,0,'xz')
    t=np.linspace(0,1,200)
    s.add('MANTA_TAIL',np.c_[8*np.sin(t*8)+tail*t, -8-15*t, 15+100*t]+c,zone,2)


def phoenix(s):
    s.dna('PHOENIX_BODY',[0,15,0],[0,100,0],7,4,'BODY',2)
    s.path('BIRD_HEAD',[(0,100,0),(-8,116,0),(0,128,0),(18,115,0),(5,111,0)],'HEAD',2,70)
    for side in (-1,1):
        for k in range(12):
            t=np.linspace(0,1,100);reach=48+7*k
            x=side*(9+reach*t);y=83-3*k+(30+5*k)*t**1.5
            upper=np.c_[x,y,np.full(len(t),(k%3)*6)]
            lower=np.c_[x,y-5*np.sin(t*math.pi),np.full(len(t),(k%3)*6)]
            # Exclude coincident root/tip endpoints when closing the feather.
            s.add('FEATHER',np.vstack((upper,lower[-2:0:-1])),'WINGS',k%2)
        for k in range(4):s.path('TAIL',[(0,55,0),(side*(10+k*8),15,5),(side*(15+k*12),0,10)],'TAIL',1,100)


def build(s,n):
    if n==23:
        for strand in range(2):
            for k in range(8):
                t=np.linspace(k/8,(k+1)/8-.018,70);a=t*math.tau*1.25+strand*math.pi
                s.add('DEPTH_HELIX_ARC',np.c_[62*np.sin(a),10+125*t,np.full(len(t),(k%4)*24+strand*6)],'GATE',strand)
        s.ring('VIEWING_MARKER',[0,0,120],9,9,'GROUND',2)
    elif n==24:
        for k in range(8):
            r=.80**k;z=-k*24
            s.path('TAPERED_PORTAL',[(-80*r,0,z),(-80*r,120*r,z),(80*r,120*r,z),(80*r,0,z)],'AVENUE',k%2,250)
        for x in (-70,70):s.path('PATH_RAIL',[(x,0,15),(x*.2,0,-180)],'GROUND',2,160)
    elif n==25:
        for side in range(4):
            for k in range(7):
                a=side*math.pi/2;distance=-65+20*k;y=10+9*k
                p=np.array([[-15,y,distance-8],[15,y,distance-8],[15,y,distance+8],[-15,y,distance+8]])
                p[:,[0,2]]=p[:,[0,2]]@np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])+[65*math.cos(a),65*math.sin(a)]
                s.path('OFFSET_STAIR',p,'TERRACES',side,80,True)
    elif n==26:
        cubes=[cube(s,[0,80,0],r,k,yaw=k*18) for k,r in enumerate((150,88,40))]
        for a,b in zip(cubes,cubes[1:]):
            for p,q in zip(a,b):s.path('DIMENSION_CONNECTOR',[p,q],'CONNECTORS',2,40)
    elif n==27:
        whale(s);waves(s)
    elif n==28:
        manta(s)
        for x in (-90,-30,30,90):s.starburst((x,7,50),5,2)
    elif n==29:
        t=np.linspace(0,math.tau,300,endpoint=False)
        for v in (-14,0,14):
            r=75+v*np.cos(t/2)
            s.add('MOBIUS_EDGE',np.c_[r*np.cos(t),40+v*np.sin(t/2)+15*np.sin(t),r*np.sin(t)],'RIBBON',0)
        for a in np.linspace(0,math.tau,40,endpoint=False):
            p=[]
            for v in (-14,14):p.append([(75+v*math.cos(a/2))*math.cos(a),40+v*math.sin(a/2)+15*math.sin(a),(75+v*math.cos(a/2))*math.sin(a)])
            s.path('RIBBON_RUNG',p,'RUNGS',2,20)
    elif n==30:
        for k,t in enumerate(np.linspace(0,1,30)):
            if t<.55:
                y=10+75*t/.55;r=24+37*math.sin(t/.55*math.pi);x=0;z=0
            else:
                u=(t-.55)/.45;x=38*math.sin(u*math.pi);y=85+60*math.sin(u*math.pi*1.4);r=12;z=20*u
            s.ring('BOTTLE_RIB',[x,y,z],r,r*.8,'LANTERN',k%2,'xz',count=100)
    elif n in (31,32):
        from models.approved_concepts import add_drummer
        s.rectangle('STAGE',0,7,0,180,90,'STAGE',2)
        for y in (0,3,6):s.path('FRONT_STEP',[(-90,y,50),(90,y,50)],'STEPS',2,160)
        add_drummer(s)
        if n==31:
            for x in (-80,-40,0,40,80):
                for z in (-35,0):s.tree(x,z,45,13,100,color=1,invert=True)
            s.rectangle('CEILING_TRUSS',0,150,0,210,110,'TRUSS',0)
            for x in (-105,105):s.path('TRUSS_POST',[(x,0,-50),(x,150,-50)],'TRUSS',0,180)
        else:
            for k in range(5):s.ring('EVENT_RING',[0,88,-30-k*22],85-k*11,85-k*11,'RINGS',k,'xy',tilt=(k-2)*4,count=300)
    elif n==33:
        for k in range(4):s.ring('ECLIPSE_ORBIT',[(k-1.5)*9,83,-k*20],70+8*k,70-5*k,'ORBITS',k,'xy')
        for a in np.linspace(0,math.tau,36,endpoint=False):
            s.path('CORONA_SPOKE',[(27*math.cos(a),83+27*math.sin(a),5),(66*math.cos(a),83+66*math.sin(a),5)],'CORONA',2,35)
    elif n==34:
        for k in range(7):
            x=(k-3)*28;h=105-abs(k-3)*17;z=(k%3)*24
            for d in (0,8):s.path('CRYSTAL_FACET',[(x-24,5,z),(x,h,z-d),(x+24,5,z),(x,30,z+16)],'FACETS',k,150,True)
    elif n==35:
        for k in range(12):
            x=-110+k*20;t=np.linspace(0,1,90)
            # Separate front/back faces; native point previews cannot simulate baffles.
            s.path('FIN_FRAME',[(x-8,0,0),(x-8,95,0),(x+8,95,8),(x+8,0,8)],'FIN_FRAMES',2,130)
            s.path('FIN_TREE_TRUNK',[(x,0,0),(x,88,0)],'TREE_FACES',0,90)
            for y in (22,42,62,78):
                s.path('FIN_TREE_BRANCH',[(x-7,y+9,0),(x,y,0),(x+7,y+9,0)],'TREE_FACES',0,35)
            for phase in (0,math.pi):
                s.add('FIN_HELIX_FACE',np.c_[x+7*np.sin(t*math.tau*2+phase),95*t,np.full(len(t),8)],'HELIX_FACES',1)
        for x in (-130,130):s.path('VIEW_PATH',[(x,0,-15),(x,0,65)],'GROUND',2,80)
    elif n==36:
        r=70
        for z in np.linspace(-60,60,6):
            rr=math.sqrt(r*r-z*z);s.ring('GLOBE_DEPTH_SLICE',[0,80,z],rr,rr,'SLICES',0,'xy')
        for yaw in range(0,180,30):
            t=np.linspace(0,math.tau,180,endpoint=False);a=math.radians(yaw)
            s.add('MERIDIAN',np.c_[r*np.cos(t)*math.cos(a),80+r*np.sin(t),r*np.cos(t)*math.sin(a)],'MERIDIANS',2)
        for lat in (-45,-20,0,20,45):s.ring('LATITUDE',[0,80+lat,0],math.sqrt(r*r-lat*lat),math.sqrt(r*r-lat*lat),'LATITUDE',1)
        # Stylized continental outlines, mapped onto the front hemisphere.
        for poly in ([(-52,29),(-34,47),(-13,35),(-23,14),(-44,8),(-52,29)],
                     [(-29,4),(-10,-2),(-17,-23),(-28,-48),(-37,-17),(-29,4)],
                     [(9,36),(29,47),(52,29),(36,14),(55,1),(28,-4),(12,16),(9,36)],
                     [(15,10),(31,2),(24,-30),(12,-16),(15,10)]):
            p=np.array([[x,80+y,math.sqrt(max(1,r*r-x*x-y*y))] for x,y in poly])
            s.path('CONTINENT_CONTOUR',p[:-1],'CONTINENTS',1,100,True)
    elif n==37:
        t=np.linspace(.17,math.tau-.1,300)
        strands=[]
        for phase in (0,math.pi):
            r=78+6*np.cos(t*8+phase)
            p=np.c_[r*np.cos(t),85+r*np.sin(t),6*np.sin(t*8+phase)]
            strands.append(p);s.add('SERPENT_HELIX',p,'COIL',int(phase>0))
        for k in range(0,len(t),8):s.path('SERPENT_RUNG',[strands[0][k],strands[1][k]],'RUNGS',2,15)
        s.path('SERPENT_HEAD',[(78,101,8),(95,94,8),(81,85,8),(67,92,8)],'HEAD',2,70,True)
    elif n==38:phoenix(s)
    elif n==39:
        for k in range(8):
            scale=.83**k;s.arch(((-1)**k*3,0,-k*24),150*scale,145*scale,k,True,'NAVE')
        for x in (-65,65):s.path('PATHWAY',[(x,0,15),(x*.2,0,-190)],'GROUND',2,170)
    elif n==40:
        for k in range(5):
            t=np.linspace(0,math.pi,19);r=100*.8**k*(1+.11*np.sin(t*13))
            p=np.c_[r*np.cos(t),r*np.sin(t),np.full(len(t),-k*25)]
            s.path('JAGGED_SHELL',p,'SHELLS',k,300)
            for i in range(len(p)-2):s.path('CRYSTAL_TRIANGLE',[p[i],p[i+1]+[0,-12,8],p[i+2]],'CRYSTALS',k,55)
    elif n==41:
        for row in range(4):
            for col in range(4):
                x=(col-1.5)*36;z=(row-1.5)*36;y=8+(row+col)%3*8
                s.rectangle('CHECKER_TILE',x,y,z,32,32,'BOARD',(row+col)%2)
        for x,z,h in ((-54,-54,60),(18,-18,92),(-18,18,48),(54,54,72)):
            s.dna('CHESS_HELIX',[x,20,z],[x,h,z],7,3,'PIECES',2)
            s.ring('PIECE_CROWN',[x,h,z],10,10,'PIECES',2)
    elif n==42:
        from models.approved_concepts import boat
        boat(s,21)
        s.g.models[:]=[m for m in s.g.models if m.zone!='CANOPY']
        for k in range(5):
            z=-60+k*30;r=52-abs(k-2)*10
            s.path('CANOPY_PRISM',[(-r,58,z),(0,115-abs(k-2)*10,z),(r,58,z),(0,36,z)],'PRISM',k,240,True)
    else:raise ValueError(n)
