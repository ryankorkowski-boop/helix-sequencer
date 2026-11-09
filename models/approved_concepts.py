"""Artwork-guided finite pixel structures for the 62 approved concept briefs.

All emitted geometry is native Custom with exact grid coordinates. These are
editable planning layouts, not surveyed structures or fabrication drawings.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from models.ultimate_showcase import Garden, Sculpture, _path

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS = ROOT / 'showcase/concepts/2026_10_08/concepts.json'
CATALOGS = (CONCEPTS, ROOT/'showcase/concepts/2026_10_09_advanced/concepts.json',
            ROOT/'showcase/concepts/2026_10_09_stop_motion/concepts.json')
PALETTES = {
    1: ('#FF9C32', '#79CEFF', '#FFF0CD'), 2: ('#83FFA3', '#CEACFF', '#FFF3CC'),
    3: ('#B69BFF', '#75FFD5', '#FF91D7'), 4: ('#A8B5FF', '#FFD37A', '#66BFFF'),
    5: ('#59FFD9', '#FF839B', '#95EFFF'), 6: ('#FFD17B', '#FFF2DD', '#CBB1FF'),
    7: ('#60DFFF', '#ED78FF', '#FFE292'), 8: ('#80FFC0', '#FFB080', '#FFEAB5'),
    9: ('#B68AFF', '#63FFC9', '#FF9EE8'), 10: ('#6EE5FF', '#FF7CCC', '#FFE293'),
    11: ('#FFD496', '#94F8BF', '#E7BBFF'), 12: ('#64DDFF', '#FF9C85', '#9BFCEC'),
    13: ('#FF535B', '#63FF93', '#FFF0D3'), 14: ('#FF5C7D', '#FFF2E7', '#64FFB0'),
    15: ('#61EFFF', '#F775FF', '#B79CFF'), 16: ('#FFE1A0', '#D8EFFF', '#FFB34E'),
    17: ('#FF61E7', '#69EEFF', '#DAB9FF'), 18: ('#FFD277', '#FFF0C9', '#FF9871'),
    19: ('#FFC573', '#FF6470', '#FFE3AA'), 20: ('#89DCFF', '#BC9AFF', '#EEF5FF'),
    21: ('#6BEDFF', '#BB92FF', '#FF8ED7'), 22: ('#FFD075', '#FF927D', '#FFF1C9'),
}


class Structures:
    def __init__(self, g):
        self.g = g
        self.serial = 0

    def add(self, label, points, zone, color=0, subs=None, details=None):
        self.serial += 1
        points = np.asarray(points, float)
        subs = dict(subs or {})
        for i, ids in enumerate(np.array_split(np.arange(1, len(points) + 1), 8)):
            if len(ids):
                subs[f'SECTOR_{i:02}'] = ids.tolist()
        return self.g.custom(f'HX_{self.serial:03}_{label}', points, zone, label.replace('_', ' '),
                             [self.g.palette[color % 3]] * len(points), subs, details=details)

    def path(self, label, vertices, zone, color=0, count=100, closed=False):
        return self.add(label, _path(vertices, count, closed=closed), zone, color)

    def ring(self, label, center, rx, ry, zone, color=0, plane='xz', tilt=0, count=150):
        t = np.linspace(0, math.tau, count, endpoint=False)
        p = np.zeros((count, 3))
        axes = {'xz': (0, 2), 'xy': (0, 1), 'yz': (2, 1)}[plane]
        p[:, axes[0]] = rx * np.cos(t)
        p[:, axes[1]] = ry * np.sin(t)
        if tilt:
            a = math.radians(tilt)
            p[:, 1], p[:, 2] = p[:, 1]*math.cos(a)-p[:, 2]*math.sin(a), p[:, 1]*math.sin(a)+p[:, 2]*math.cos(a)
        return self.add(label, p + center, zone, color)

    def dna(self, label, a, b, radius=4, turns=3, zone='HELIX', color=0):
        a, b = np.asarray(a, float), np.asarray(b, float)
        axis = b-a
        u = np.cross(axis, [0, 1, 0])
        if np.linalg.norm(u) < .01:
            u = np.cross(axis, [1, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(axis, u); v /= np.linalg.norm(v)
        t = np.linspace(0, 1, 150)
        theta = math.tau*turns*t
        spine = a + t[:, None]*axis
        offset = radius*(np.cos(theta)[:, None]*u+np.sin(theta)[:, None]*v)
        p = np.vstack((spine+offset, spine-offset))
        subs = {'STRAND_A': list(range(1, 151)), 'STRAND_B': list(range(151, 301)), 'RUNGS': []}
        for k in range(0, 150, 8):
            rung = np.linspace(p[k], p[150+k], 7)[1:-1]
            subs['RUNGS'].extend(range(len(p)+1, len(p)+6))
            p = np.vstack((p, rung))
        m = self.add(label, p, zone, color, subs, {'double_helix': True})
        for key, c in [('STRAND_A', color), ('STRAND_B', color+1), ('RUNGS', color+2)]:
            for n in subs[key]:
                m.colors[n-1] = self.g.palette[c % 3]
        return m

    def tree(self, x, z, h=40, r=12, y=0, color=0, tilt=0, invert=False):
        t = np.linspace(0, 1, 80)
        p = []
        for strand in range(4):
            angle = t*math.tau*2.3 + strand*math.tau/4
            p.extend(np.c_[(r*(1-t)+.7)*np.cos(angle), h*t, (r*(1-t)+.7)*np.sin(angle)])
        p = np.asarray(p)
        if invert:
            p[:, 1] = h-p[:, 1]
        a = math.radians(tilt)
        p[:, 0], p[:, 1] = p[:, 0]*math.cos(a)+p[:, 1]*math.sin(a), -p[:, 0]*math.sin(a)+p[:, 1]*math.cos(a)
        m = self.add('SPIRAL_TREE', p+[x, y, z], 'GROVE', color,
                     {f'STRAND_{i+1}': list(range(80*i+1,80*(i+1)+1)) for i in range(4)},
                     {'spiral_tree': True, 'custom_exact': True})
        return m

    def mesh(self, label, center, width, height, zone, color=0, wave=0, yaw=0, curved=0):
        rows, cols = 16, 32
        x, y = np.meshgrid(np.linspace(-width/2, width/2, cols), np.linspace(0, height, rows))
        z = wave*np.sin(x/width*math.tau*1.5+y/height*math.tau) + curved*(x/width)**2
        a=math.radians(yaw)
        p=np.c_[x.ravel()*math.cos(a)+z.ravel()*math.sin(a),y.ravel(),-x.ravel()*math.sin(a)+z.ravel()*math.cos(a)]+center
        return self.add(label,p,zone,color,{f'ROW_{i:02}':list(range(i*cols+1,(i+1)*cols+1)) for i in range(rows)})

    def arch(self, center, width=40, height=50, color=0, pointed=False, zone='ARCHES'):
        x,y,z=center
        if pointed:
            vertices=[(x-width/2,y,z),(x-width/2,y+height*.5,z),(x-width*.3,y+height*.8,z),(x,y+height,z),
                      (x+width*.3,y+height*.8,z),(x+width/2,y+height*.5,z),(x+width/2,y,z)]
            return self.path('POINTED_ARCH',vertices,zone,color,160)
        t=np.linspace(0,math.pi,150)
        return self.add('ARCH',np.c_[x+width/2*np.cos(t),y+height*np.sin(t),np.full(len(t),z)],zone,color)

    def rectangle(self, label, x, y, z, w, d, zone, color=0):
        return self.path(label,[(x-w/2,y,z-d/2),(x+w/2,y,z-d/2),(x+w/2,y,z+d/2),(x-w/2,y,z+d/2)],zone,color,200,True)

    def starburst(self, center, radius=9, color=2, zone='ACCENTS'):
        for angle in np.linspace(0, math.tau, 8, endpoint=False):
            a=np.asarray(center)+[1.0*math.cos(angle),1.0*math.sin(angle),0]
            b=np.asarray(center)+[radius*math.cos(angle),radius*math.sin(angle),0]
            self.path('STAR_RAY',[a,b],zone,color,12)


def add_drummer(s):
    """Keep source node order and all 40 canonical target/helper ranges intact."""
    from tools.render_drummer_v3_preview import _expand_ranges, load_component_masks
    source=ET.parse(ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel').getroot()
    subs={e.get('name'):sorted(_expand_ranges(e.get('line0',''))) for e in source.findall('subModels/subModel')}
    art,masks=load_component_masks()
    mask=masks['__preview_body__'].resize((96,72),Image.Resampling.NEAREST)
    # The canonical model uses the whole source grid, including its margins.
    subs['BODY_KEEPALIVE']=(np.flatnonzero(np.asarray(mask)>80)+1).tolist()
    points=np.array([[(x-47.5)*.62,(71-y-35.5)*.62+36,8] for y in range(72) for x in range(96)])
    attrs={**source.attrib,'ModelBrightness':'100','CustomBkgImage':'assets/drummer_idle.png',
           'HelixVisualSource':'assets/drummerbg.png','WorldPosX':'0','WorldPosY':'36','WorldPosZ':'8',
           'ScaleX':'.62','ScaleY':'.62','ScaleZ':'.62'}
    m=Sculpture(source.get('name'),'Custom','BAND','Unchanged canonical drummer placed on center riser',
                attrs,points,['#B8C5C9']*len(points),subs,details={'canonical_drummer':True,'source_grid_preserved':True})
    s.g.models.append(m)


def spatial(s, n):
    if n==1:
        for side in (-1,1):
            for tier in range(3):
                x=side*(65+32*tier);y=12*tier
                s.rectangle('TERRACE',x,y,-30+20*tier,60,95,'TERRACES',int(side>0))
                for z in (-65,-10,35):s.tree(x,z,35+tier*12,10,y,int(side>0))
        s.dna('VALLEY_BRIDGE',[-150,62,-70],[140,18,40],5,5,'BRIDGE')
        s.ring('VALLEY', [0,0,20],30,20,'GROUND',2)
    elif n==2:
        for z in (-80,-40,0,40):
            for x in (-75,75):s.dna('NAVE_COLUMN',[x,0,z],[x,80,z],4,3,'COLUMNS')
            s.arch((0,0,z),145,103,1,True,'NAVE')
            s.dna('CANOPY_RIB',[-75,75,z],[75,85,z],4,4,'CANOPY',1)
        for x in (-140,140):
            for z in (-60,10,55):s.tree(x,z,45,13,color=0)
        s.rectangle('WALKWAY',0,0,-20,50,155,'GROUND',2)
    elif n==3:
        for tier in range(4):
            z=50-45*tier;y=18*tier
            s.path('SWITCHBACK',[(-150,y,z),(150,y,z),(150 if tier%2==0 else -150,y+18,z-45)],'PATH',tier,250)
            for x in (-120,-50,40,115):s.tree(x,z-8,30+tier*7,10,y,tier)
        s.dna('CLIMBING_BRIDGE',[-140,6,45],[120,77,-85],4,6,'BRIDGE',1)
    elif n==4:
        for i in range(5):s.ring('BASIN_RING',[0,i*3,0],45+i*24,25+i*14,'TERRACES',i)
        s.dna('BEACON',[0,0,0],[0,85,0],8,4,'CENTER',1)
        for i in range(10):
            t=i*math.tau/10;x,z=125*math.cos(t),65*math.sin(t)
            s.tree(x,z,35+(i%3)*10,10,6,i)
        for x,tilt in [(-100,-28),(0,22),(100,38)]:s.ring('ORBIT',[x,85,-30],35,23,'ORBITS',1,'xz',tilt)
    elif n==5:
        for i in range(7):
            x=-135+i*45;z=-50 if i%2 else 20;h=45+(i%3)*20
            s.dna('MANGROVE_TRUNK',[x,5,z],[x,h,z],4,3,'TRUNKS')
            s.ring('CROWN',[x,h,z],22,17,'CANOPY',1)
            for a in np.linspace(0,math.tau,6,endpoint=False):s.path('ROOT',[(x,22,z),(x+10*math.cos(a),5,z+10*math.sin(a)),(x+24*math.cos(a),0,z+24*math.sin(a))],'ROOTS',0,65)
        s.path('RAISED_PATH',[(-160,8,55),(-90,8,35),(-30,12,50),(40,12,0),(110,8,30),(160,8,5)],'PATH',2,400)
    elif n==6:
        for k in range(3):
            r=55+40*k;s.ring('RADIAL_GARDEN',[0,3*k,0],r,r*.55,'GROUND',0)
            for i in range(8):
                t=i*math.tau/8;s.tree(r*math.cos(t),r*.55*math.sin(t),25+12*k,9,3*k,(i+k)%3)
        s.dna('SLOPING_CANOPY',[-120,65,-45],[120,110,-45],10,4,'CANOPY')
        s.dna('CENTRAL_SPIRE',[0,0,-10],[0,100,-10],8,4,'CENTER')


def abstract(s,n):
    if n==7:
        for i in range(4):s.mesh('MOIRE_LATTICE',[-50+i*35,5,-25+i*16],100,85,'LATTICES',i,yaw=(i-1.5)*13)
        for i in range(5):s.ring('PHASE_RING',[0,48,45],12+i*15,12+i*15,'RINGS',i,'xy')
        for x in (-145,145):s.tree(x,-50,72,18,color=2)
    elif n==8:
        for i in range(9):
            x=-140+(i%5)*65;z=-65+(i//5)*95;h=30+(i%3)*16
            s.tree(x,z,h,12,color=0)
            s.ring('MUSHROOM_CROWN',[x,h+5,z],23,16,'CROWNS',1,'xz',i*3)
            for r in (8,16):s.ring('CROWN_RIB',[x,h+9-r*.25,z],r,r*.7,'CROWNS',2)
        for z in (-30,40):s.dna('BRAIDED_TUNNEL',[-160,20,z],[150,35,z],5,5,'TUNNELS')
    elif n==9:
        for i in range(9):s.tree(-140+i*35,-50+(i%3)*40,42,13,20+(i%3)*17,i,(-1)**i*25,i%2==1)
        s.dna('GRAVITY_SPINE',[-150,100,-40],[140,24,40],6,5,'SPINE')
        s.ring('GROUNDED_RING',[0,0,0],165,70,'GROUND',2)
    elif n==10:
        for i in range(8):
            z=55-i*20;r=70-i*5
            s.ring('VORTEX_HOOP',[0,65,z],r,r,'TUNNEL',i,'xy',(-1)**i*12)
            for a in np.linspace(0,math.tau,8,endpoint=False):
                s.path('CROSSED_SPOKE',[(r*.25*math.cos(a+.35*i),65+r*.25*math.sin(a+.35*i),z),
                                     (r*math.cos(a+.35*i),65+r*math.sin(a+.35*i),z)],'SPOKES',i+1,45)
        for x in (-130,130):s.tree(x,0,80,18,color=0)
        s.dna('COUNTERWOUND_RAIL',[-90,5,65],[-30,50,-100],5,4,'RAILS',1)
        s.dna('COUNTERWOUND_RAIL',[90,5,65],[30,50,-100],5,-4,'RAILS',2)
    elif n==11:
        for x in (-105,0,105):
            s.tree(x,-45,75,20,color=0)
            for offset in (-30,30):
                s.tree(x+offset,12,38,10,color=1)
                for dx in (-12,12):s.tree(x+offset+dx,48,18,5,color=2)
            s.dna('FERN_CURL',[x-28,5,-35],[x+26,70,-40],7,3,'FERNS',0)
        s.ring('MEADOW',[0,0,0],165,85,'GROUND',1)
    elif n==12:
        for i in range(3):s.mesh('WAVE_MESH',[0,8,-55+i*48],280,75,'WAVES',i,wave=15,yaw=(i-1)*8)
        for i in range(10):s.tree(-150+i*32,65,22+(i%3)*10,7,color=i)
        s.dna('REEF_RIDGE',[-150,60,-90],[145,85,-80],7,5,'RIDGE',1)
        for x in (-110,-35,40,115):s.ring('CORAL_RING',[x,18,75],16,16,'CORAL',0,'xy')


def house(s,x,z,w=80,h=50,color=0):
    s.path('HOUSE_FACADE',[(x-w/2,0,z),(x-w/2,h,z),(x,h+25,z),(x+w/2,h,z),(x+w/2,0,z)],'FACADES',color,250)
    for off in (-w*.25,w*.25):
        s.path('WINDOW',[(x+off-7,18,z),(x+off-7,35,z),(x+off+7,35,z),(x+off+7,18,z)],'WINDOWS',2,60,True)


def traditional(s,n):
    if n==13:
        for x in (-105,0,105):house(s,x,-90,95,48)
        for x in (-155,155):s.tree(x,-70,115,22,color=1)
        for z in (-20,20,60):
            for x in np.linspace(-145,145,9):
                s.tree(x,z,17,5,color=int((x+z)%3))
                s.arch((x+13,0,z+12),18,15,2)
        for x in (-125,-65,0,65,125):s.starburst((x,62,-82),9,2,'SNOWFLAKES')
    else:
        for i in range(9):
            z=65-i*24;s.arch((0,0,z),80,80-i*3,i%2)
            for side in (-1,1):
                x=side*(70+(i%2)*30);s.tree(x,z,30+i*3,10,color=2)
                s.path('CANE',[(side*52,0,z),(side*52,28,z),(side*48,34,z),(side*43,32,z),(side*43,26,z)],'CANES',i%2,65)
        for x in (-140,140):
            for z in (-95,-10,65):house(s,x,z,40,28,0)
        s.rectangle('BOULEVARD',0,0,-30,70,230,'GROUND',1)


def stage(s,n):
    for i in range(3):s.ring('STAGE_APRON',[0,5*i,22],72-5*i,32-3*i,'STAGE',i)
    s.rectangle('DRUM_RISER',0,18,8,60,24,'BAND',2)
    if n==15:
        for i in range(4):s.ring('SPECTATOR_RING',[0,5+i*7,-5],108+22*i,55+12*i,'ARENA',i)
        for x in (-105,105):
            s.dna('TOWER',[x,0,-30],[x,112,-30],7,4,'TOWERS')
            s.path('TRUSS',[(x-10,0,-30),(x-10,112,-30),(x+10,112,-30),(x+10,0,-30)],'TOWERS',2,240)
        for tilt in (-30,32):s.ring('INTERLOCKED_TRUSS',[0,110,-15],74,44,'CEILING',0 if tilt<0 else 1,'xz',tilt,220)
        s.mesh('CURVED_BACKDROP',[0,20,-46],145,65,'BACKDROP',1,curved=70)
    else:
        for side in (-1,1):
            for i in range(3):
                x=side*(95+i*20);y=30+i*22;z=-30-i*10
                s.path('FACETED_WING',[(x-side*18,y-24,z),(x,y+30,z-6),(x+side*18,y,z),(x,y-30,z+6)],'WINGS',i,180,True)
                for k in range(3):s.path('WING_INSET',[(x-side*12+k*3,y-12,z),(x,y+20-k*5,z),(x+side*10-k*2,y,z)],'WINGS',i+1,85)
        for i in range(7):s.mesh('REAR_LED_PANEL',[-70+i*23,15,-65-(i%2)*10],15,80,'BACKDROP',i%2)
        for z in (-60,-20,20):
            s.dna('OVERHEAD_RIB',[-105,105,z],[105,126,z-12],5,3,'CEILING',0)
            s.dna('CROSSED_RIB',[-105,126,z-12],[105,105,z],5,3,'CEILING',1)
    # Dedicated canonical front-facing drummer, not a substituted sculpture.
    add_drummer(s)


def car(s,n):
    # Stylized parked 1964 coupe proportions, explicitly not a surveyed mesh.
    for side in (-1,1):
        z=side*32
        s.path('BODY_CONTOUR',[(-140,15,z),(-138,35,z),(-80,42,z),(-50,65,z),
                             (35,65,z),(65,42,z),(125,38,z),(145,30,z),(140,15,z)],'BODY',0,380)
        s.path('BELT_TRIM',[(-138,33,z),(-75,40,z),(65,40,z),(140,30,z)],'TRIM',1,260)
        s.path('WINDOW_TRIM',[(-65,42,z),(-45,61,z),(28,61,z),(50,42,z)],'CABIN',1,150,True)
        for x in (-85,90):
            s.ring('WHEEL',[x,17,z],17,17,'WHEELS',1,'xy',count=90)
            for a in np.linspace(0,math.tau,12,endpoint=False):s.path('WHEEL_SPOKE',[(x,17,z),(x+14*math.cos(a),17+14*math.sin(a),z)],'WHEELS',2,12)
    for x in (-140,140):
        s.path('BUMPER',[(x,18,-32),(x,18,32)],'BODY',2,100)
        for z in (-22,-11,11,22):s.ring('LAMPS',[x,30,z],4,4,'LAMPS',2,'yz',count=36)
    s.rectangle('UNDERGLOW',0,6,0,280,64,'UNDERBODY',0)
    s.path('OPEN_TRUNK',[(80,42,-32),(120,84,-32),(120,84,32),(80,42,32)],'AUDIO',0,170,True)
    for z in (-20,0,20):s.ring('TRUNK_SPEAKER',[119,65,z],8,8,'AUDIO',1,'yz',count=60)
    if n==17:
        for x in (-160,160):s.dna('AUDIO_TOWER',[x,0,-65],[x,90,-65],5,4,'AUDIO')
        for x in (-100,-35,35,100):s.ring('SPEAKER_WALL',[x,65,-70],18,18,'AUDIO',0,'xy')
    else:
        for i in range(4):s.arch((30,0,-60-i*10),230-i*25,125-i*14,i,zone='AUDIO_FAN')
        s.dna('REAR_HELIX_FAN',[-130,65,-80],[135,118,-80],7,5,'AUDIO',0)


def church(s,n):
    house(s,0,-50,145,92,0)
    s.arch((0,0,-49),45,65,1,True,'DOOR')
    for i in range(3):s.ring('ROSE_WINDOW',[0,100,-48+i],13+i*5,13+i*5,'ROSE',i,'xy')
    s.starburst((0,100,-45),24,2,'ROSE')
    for side in (-1,1):
        x=side*92
        s.path('TOWER',[(x-20,0,-55),(x-20,135,-55),(x,180,-55),(x+20,135,-55),(x+20,0,-55)],'TOWERS',0,400)
        s.arch((x,62,-53),24,50,1,True,'WINDOWS')
        for z in (-100,-55,-10,35):
            s.path('BUTTRESS',[(side*125,0,z),(side*108,54,z),(side*80,94,z)],'BUTTRESSES',1,130)
            s.arch((side*73,0,z),28,54,0,True,'AISLES')
    for x in (-145,145):
        for z in (15,65):s.tree(x,z,35,10,color=1)
    if n==20:
        for z in (25,65):
            s.arch((0,0,z),145,145,2,True,'CLOISTER')
            s.dna('CLOISTER_COLUMN',[-80,0,z],[-80,105,z],3,4,'CLOISTER',0)
            s.dna('CLOISTER_COLUMN',[80,0,z],[80,105,z],3,4,'CLOISTER',1)
        for x in (-35,35):s.dna('DEEP_GROVE',[x,0,-115],[x,70,-115],4,3,'GROVE')
    for i in range(3):s.rectangle('COURT',0,i*2,25,260-i*25,150-i*20,'GROUND',i)


def boat(s,n):
    for x in (-45,45):
        for side in (-1,1):
            s.path('PONTOON_HULL',[(x+side*12,0,-90),(x+side*14,0,66),(x+side*8,3,84),(x,6,92)],'HULL',2,240)
        for z in (-85,70):s.ring('HULL_SECTION',[x,1,z],13,7,'HULL',2,'xy',count=70)
    for y in (12,20,33):s.rectangle('RAIL_CONTOUR',0,y,0,116,175,'RAILS',0 if n==21 else 1)
    for x in (-58,58):
        for z in (-85,-45,0,45,85):s.path('RAIL_POST',[(x,12,z),(x,34,z)],'RAILS',2,30)
        s.mesh('SIDE_PIXEL_MESH',[x,16,-25],140,14,'SIDES',0,yaw=90,wave=2)
    for i,z in enumerate((-55,-20,15,50)):
        s.arch((0,43,z),110,28,i%2,zone='CANOPY')
        for side in (-1,1):s.path('BIMINI_SUPPORT',[(side*56,16,z-8),(side*45,44,z)],'CANOPY',2,60)
    for x in (-27,0,27):
        for r in (8,11):s.ring('SPEAKER_RING',[x,38,-67],r,r,'AUDIO',0 if n==21 else 2,'xy',count=80)
    for x in (-55,55):
        for z in (-75,65):
            if n==21:s.dna('SHORT_SPIRAL',[x,32,z],[x,60,z],3,3,'ACCENTS',0)
            else:s.starburst((x,48,z),10,2)
    for i in range(4):s.path('BOARDING_STEP',[(-20,12-3*i,89+8*i),(20,12-3*i,89+8*i)],'STEPS',2,70)
    if n==22:
        s.ring('AFT_FAN_RING',[45,54,-65],27,27,'AFT_FAN',0,'xy')
        for phase in range(6):
            t=np.linspace(.1,1,90);a=t*math.tau*1.3+phase*math.tau/6
            s.add('AFT_HELIX_FAN',np.c_[45+26*t*np.cos(a),54+26*t*np.sin(a),np.full(len(t),-64)],'AFT_FAN',phase)


def build_concept(concept):
    n=int(concept['id'])
    slug=concept['name'].replace(' ','_')
    palette=PALETTES.get(n, ('#69EFFF','#B599FF','#FFD98A'))
    if n in (25,30,33,38,40,46,57):palette=('#FFD277','#C9A1FF','#FFF0CF')
    if n in (27,28,36,48,51,52):palette=('#69EFFF','#FFAB99','#E5F6FF')
    g=Garden(title=concept['name'],slug=slug,description=concept['description'],palette=palette)
    s=Structures(g)
    if n<=6:spatial(s,n)
    elif n<=12:abstract(s,n)
    elif n<=14:traditional(s,n)
    elif n<=16:stage(s,n)
    elif n<=18:car(s,n)
    elif n<=20:church(s,n)
    elif n<=22:boat(s,n)
    elif n<=42:
        from models.advanced_concepts import build
        build(s,n)
    else:
        from models.stop_motion_concepts import build
        build(s,n)
    start=1
    for m in g.models:m.start=start;start+=m.channels
    return g


def catalog():
    result=[]
    for path in CATALOGS:
        for original in json.loads(path.read_text())['concepts']:
            c=dict(original);n=int(c['id'])
            c['source_catalog']=str(path.relative_to(ROOT))
            c.setdefault('description',c.get('standout',''))
            c.setdefault('constraint','Finite artwork-guided planning geometry; no physical actuation or surveyed construction dimensions.')
            c.setdefault('round','advanced' if n<=42 else 'stop_motion')
            result.append(c)
    return result
