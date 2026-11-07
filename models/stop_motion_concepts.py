"""Static replacement contours with explicit held-pose metadata (43–62)."""
from __future__ import annotations

import math
import numpy as np
from models.advanced_concepts import whale, manta, waves


def pose(s,index,callback,count=4,track='BODY',order=None):
    start=len(s.g.models);callback()
    for m in s.g.models[start:]:
        m.zone=f'POSE_{track}_{index:02}'
        m.details.update(pose_index=index,pose_count=count,pose_track=track,
                         pose_order=order or list(range(count)))


def person(s,x,y,z,frame=0,height=60,zone='PUPPET'):
    """Jointed silhouette; four readable limb poses, fixed head/body proportions."""
    h=height;head=[x,y+h*.86,z]
    s.ring('HEAD',head,h*.1,h*.12,zone,0,'xy',count=70)
    s.path('TORSO',[(x,y+h*.72,z),(x,y+h*.38,z)],zone,1,45)
    shoulder=np.array([x,y+h*.68,z]);hip=np.array([x,y+h*.38,z])
    for side in (-1,1):
        swing=math.sin(frame*math.pi/2+side*math.pi/2)
        elbow=shoulder+[side*h*.16,-h*.17+swing*h*.10,0]
        hand=elbow+[side*h*.12,-h*.12+swing*h*.23,0]
        knee=hip+[side*h*.12+swing*h*.08,-h*.20,0]
        foot=np.array([x+side*h*.18-swing*h*.12,y,z])
        s.path('ARM',[shoulder,elbow,hand],zone,2,55)
        s.path('LEG',[hip,knee,foot],zone,0,65)
        for p in (elbow,knee):s.ring('JOINT',p,h*.024,h*.024,zone,0,'xy',count=16)
        s.path('SHOE',[foot+[-h*.04,0,0],foot+[h*.08,0,0]],zone,2,18)


def theatre(s):
    s.path('THEATRE_FRAME',[(-110,0,0),(-110,120,0),(110,120,0),(110,0,0)],'THEATRE',2,400)
    for x in (-100,100):
        for k in range(5):s.path('CURTAIN_RIB',[(x+(k-2)*3,5,0),(x+(k-2)*3,110,0)],'CURTAIN',1,100)
    s.rectangle('THEATRE_DECK',0,0,15,220,70,'GROUND',2)


def deer(s,center,frame=0):
    x,y,z=center
    s.path('DEER_BODY',[(x-15,y+30,z),(x+15,y+30,z),(x+27,y+48,z),(x+37,y+44,z),(x+24,y+37,z),(x+18,y+17,z),(x-18,y+17,z)],'DEER',0,140)
    for k,base in enumerate((-12,-5,10,17)):
        delta=9*math.sin(frame*math.pi/2+k*math.pi/2)
        s.path('DEER_LEG',[(x+base,y+18,z),(x+base+delta,y+9,z),(x+base-delta,y,z)],'DEER',2,45)
    for side in (-1,1):s.path('ANTLER',[(x+27,y+47,z),(x+23+side*8,y+59,z),(x+23+side*14,y+63,z)],'DEER',2,30)


def build(s,n):
    if n==43:
        for k in range(6):pose(s,k,lambda k=k:person(s,-125+50*k,0,0,k%4),6)
        s.path('PARADE_PATH',[(-155,0,15),(155,0,15)],'GROUND',2,300)
        for x in (-150,150):s.arch((x,0,-12),35,95,1)
    elif n==44:
        # Height and body compression change, with equal-width grounded bays.
        for k,(y,h) in enumerate(((0,40),(22,80),(0,34),(0,60))):
            pose(s,k,lambda k=k,y=y,h=h:person(s,0,y,k*4,k,height=h))
        s.ring('LANDING_MARKER',[0,0,0],38,18,'GROUND',2)
        for x in (-75,75):s.tree(x,-10,28,10,color=1)
    elif n==45:
        for k in range(4):
            def body(k=k):
                length=(160,110,125,165)[k];offset=(0,0,20,20)[k]
                for j in range(12):
                    x=-length/2+j*length/11+offset;y=13+(18 if k==1 else 3)*math.sin(j*math.pi/11)
                    s.ring('CATERPILLAR_SEGMENT',[x,y,k*3],13,13,'BODY',j%2,'yz',count=70)
                x=length/2+offset
                s.ring('CATERPILLAR_HEAD',[x,17,k*3],15,15,'HEAD',2,'yz')
                for side in (-1,1):s.path('ANTENNA',[(x,25,side*7+k*3),(x+10,42,side*15+k*3)],'HEAD',2,30)
            pose(s,k,body)
    elif n==46:
        for x in (-85,0,85):
            s.path('FLOWER_STEM',[(x,0,0),(x,55,0)],'STEMS',0,70)
            for k in range(4):
                def petals(x=x,k=k):
                    for j in range(8):
                        a=j*math.tau/8;reach=(6,15,27,38)[k]
                        t=np.linspace(0,math.tau,100,endpoint=False)
                        # Radial petal ovals around the flower center.
                        r=reach*(.5+.5*np.cos(t))
                        p=np.c_[x+r*np.cos(a)+reach*.22*np.sin(t)*math.sin(a),
                                55+r*np.sin(a)-reach*.22*np.sin(t)*math.cos(a),np.full(len(t),k*4)]
                        s.add('REPLACEMENT_PETAL',p,'FLOWERS',1+j%2)
                pose(s,k,petals,order=[0,1,2,3,3,2,1,0])
    elif n==47:
        for x in (-110,-45,40,105):s.tree(x,-25,65,14,color=1)
        positions=[(-65,35,10),(-55,42,10),(35,85,10),(40,89,10)]
        for k,p in enumerate(positions):
            def firefly(p=p):
                s.ring('FIREFLY_BODY',p,4,7,'FIREFLY',2,'xy',count=40)
                for side in (-1,1):s.ring('FIREFLY_WING',np.array(p)+[side*8,0,0],8,4,'FIREFLY',2,'xy',count=40)
            pose(s,k,firefly,order=[0,0,1,2,3,3])
    elif n==48:
        s.dna('DRAGON_TORSO',[0,15,0],[0,83,0],9,4,'BODY',0)
        s.path('DRAGON_HEAD',[(0,83,0),(8,108,0),(28,105,0),(17,92,0),(3,91,0)],'HEAD',2,100)
        for k,angle in enumerate((45,0,-38,0)):
            def wings(k=k,angle=angle):
                a=math.radians(angle)
                for side in (-1,1):
                    for j in range(6):
                        length=95-j*11
                        s.path('DRAGON_WING',[(side*8,62,0),(side*length,65+length*math.sin(a),k*4),
                                             (side*(length-15),47+length*.4*math.sin(a),k*4)],'WINGS',j%2,100)
            pose(s,k,wings)
    elif n==49:
        for k,(y,rx,ry) in enumerate(((80,28,28),(60,18,43),(14,43,12),(80,28,28))):
            pose(s,k,lambda k=k,y=y,rx=rx,ry=ry:s.ring('MOON_SHAPE',[0,y,k*4],rx,ry,'MOON',2,'xy'))
        for x in (-90,90):s.arch((x,0,0),60,35,0)
    elif n==50:
        shapes=[ [(-40,0),(40,0),(40,10),(-40,10)], [(-40,0),(0,45),(40,0)],
                 [(-40,0),(0,25),(18,70),(23,20),(55,40),(20,0)],
                 [(-75,62),(-12,25),(10,80),(24,94),(36,83),(23,83),(23,20),(78,60),(40,0),(0,10),(-40,0)] ]
        for k,vertices in enumerate(shapes):
            pose(s,k,lambda k=k,vertices=vertices:s.path('ORIGAMI_REPLACEMENT',[(x,y+12,k*5) for x,y in vertices],'ORIGAMI',k%3,250,True))
        s.rectangle('DISPLAY_PLATFORM',0,0,0,175,60,'GROUND',2)
    elif n==51:
        for k,(y,a) in enumerate(((32,8),(60,32),(90,65),(45,115))):
            pose(s,k,lambda k=k,y=y,a=a:whale(s,(0,y,k*8),.7,a))
        waves(s)
    elif n==52:
        for k in range(4):pose(s,k,lambda k=k:manta(s,(0,65+(8,-2,-8,2)[k],k*5),(0,25,20,-10)[k],(-10,-10,10,15)[k]))
        s.rectangle('WALKWAY',0,0,20,90,160,'GROUND',2)
    elif n==53:
        theatre(s)
        for k in range(4):pose(s,k,lambda k=k:person(s,0,0,k*4,k,height=95),order=[0,1,2,3,3,3,2,1])
    elif n==54:
        from models.approved_concepts import house
        for x in (-110,-65,65,110):house(s,x,25,24,18,2)
        for k in range(4):pose(s,k,lambda k=k:person(s,0,0,k*4,k,height=135))
        s.path('VILLAGE_STREET',[(-150,0,40),(150,0,40)],'GROUND',0,300)
    elif n==55:
        from models.approved_concepts import add_drummer
        theatre(s);add_drummer(s)
        for y in (10,13):s.rectangle('DRUMMER_RISER',0,y,5,75,45,'RISER',2)
        s.dna('OVERHEAD_HELIX',[-100,120,-20],[100,120,-20],6,4,'CANOPY')
        # Canonical source model stays unchanged; extra, independently addressable
        # sticks demonstrate prepare/contact/recovery over its existing kit.
        for k,tip in enumerate(((0,69,7),(16,40,7),(8,58,7),(0,60,7))):
            pose(s,k,lambda tip=tip:s.path('SNARE_STICK_POSE',[(-12,52,7),tip],'STICK',2,40))
    elif n==56:
        theatre(s)
        for k in range(4):
            def fox(k=k):
                z=k*4;ear=(0,8,-3,0)[k]
                s.path('FOX_SILHOUETTE',[(-25,5,z),(-32,38,z),(-22,65,z),(-23,91+ear,z),(-4,74,z),
                                             (12,88-ear,z),(15,66,z),(35,60,z),(10,49,z),(13,15,z),(27,4,z)],'FOX',0,260)
                s.path('FOX_TAIL',[(-25,15,z),(-65,35,z),(-78,12,z),(-49,1,z),(-25,5,z)],'FOX',1,110)
                s.path('FOX_PAW',[(7,20,z),(20+8*k,25+9*k,z)],'FOX',2,40)
            pose(s,k,fox)
    elif n==57:
        from models.approved_concepts import church
        church(s,19)
        for m in s.g.models:
            m.details['assembly_index']={'GROUND':0,'BUTTRESSES':1,'AISLES':1,'TOWERS':3,'ROSE':3}.get(m.zone,2)
    elif n==58:
        for j in range(12):
            a=j*math.pi/11;x=120*math.cos(a);z=-70*math.sin(a)
            for k,tilt in enumerate((0,35)):
                def tile(tilt=tilt,x=x,z=z):
                    dx=45*math.sin(math.radians(tilt))
                    s.path('DOMINO_POSE',[(x-10,0,z),(x-10+dx,50,z),(x+10+dx,50,z),(x+10,0,z)],'DOMINO',j,160,True)
                    for y in (14,35):s.ring('DOMINO_DOT',[x+dx*y/50,y,z],3,3,'DOMINO',2,'xy',count=30)
                start=len(s.g.models);tile()
                for m in s.g.models[start:]:m.details.update(domino_index=j,domino_lean=bool(k))
    elif n==59:
        from models.approved_concepts import boat
        boat(s,21)
        for k in range(4):
            def sails(k=k):
                for z in (-30,20):s.path('SAIL_REPLACEMENT',[(-45,40,z),(15+(k-1)*9,95+k*4,z),(45,40,z)],'SAILS',1,170,True)
                x=np.linspace(-90,90,180)
                s.add('WAVE_REPLACEMENT',np.c_[x,-8+(5+k*3)*np.sin(x/20+k),np.full(len(x),70)],'WAVES',0)
            pose(s,k,sails)
    elif n==60:
        for k in range(12):
            a=k*math.tau/12
            pose(s,k,lambda k=k,a=a:deer(s,(100*math.cos(a),0,65*math.sin(a)),k%4),12)
        for y in (85,100):s.ring('CAROUSEL_HALO',[0,y,0],120,80,'HALO',1)
        for x in (-120,120):s.path('HALO_POST',[(x,0,0),(x,100,0)],'SUPPORTS',2,120)
    elif n==61:
        for z in range(-100,101,40):s.ring('TUNNEL_RING',[0,65,z],85,65,'TUNNEL',1,'xy')
        for k,x in enumerate((-75,-45,5,65)):
            def comet(k=k,x=x):
                s.starburst((x,65,k*5),14,2,'COMET')
                for dy in (-6,0,6):s.path('SMEAR' if k==2 else 'TRAIL',[(x-(80 if k==2 else 22),65+dy,k*5),(x-6,65,k*5)],'COMET',0,80)
            pose(s,k,comet)
    elif n==62:
        theatre(s)
        for k,(x,y) in enumerate(((-65,25),(-20,70),(45,65),(-65,25))):
            pose(s,k,lambda k=k,x=x,y=y:s.ring('MOON_LOOP_POSE',[x,y,k*4],18,18,'MOON',2,'xy'))
        for x in (-85,-40,40,85):s.starburst((x,96,0),5,2)
        for z in (-20,15):s.dna('LOW_HELIX_SCENERY',[-90,15,z],[90,15,z],5,3,'SCENERY',1)
    else:raise ValueError(n)
