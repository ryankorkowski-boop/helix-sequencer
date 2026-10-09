"""Six-member, finite 3D pixel ensemble with stationary replacement-pose nodes.

The accepted drummer is imported without changing its grid or source ranges.
Other members are original geometry, not vendor downloads or moving hardware.
"""
from __future__ import annotations

import math
import numpy as np
from models.ultimate_showcase import Garden, _path
from models.approved_concepts import ROOT,Structures, add_drummer
from models.helixville4_vocal_phonemes import PHONEME_NAMES

WHITE = '#C8E5F2'
WOOD = '#B87937'
COLORS = ('#73E7FF', '#FF87CE', '#FFD783')


class Parts:
    def __init__(self, garden, name, position, role):
        self.g, self.name, self.position, self.role = garden, name, np.array(position), role
        self.cells, self.colors, self.parts, self.lookup = [], [], {}, {}

    def add(self, name, points, color=WHITE):
        ids = []
        for point in np.asarray(points):
            cell = tuple(np.rint((point+self.position)*2).astype(int))
            if cell not in self.lookup:
                self.lookup[cell] = len(self.cells)+1
                self.cells.append(cell)
                self.colors.append(color)
            ids.append(self.lookup[cell])
        self.parts[name] = sorted(set(ids))

    def path(self, name, vertices, color=WHITE, count=60, closed=False):
        self.add(name, _path(vertices, count, closed=closed), color)

    def ellipse(self, name, center, radii, color=WHITE, count=80, depth=0):
        t=np.linspace(0, math.tau, count, endpoint=False)
        self.add(name, np.c_[radii[0]*np.cos(t),radii[1]*np.sin(t),depth*np.sin(t*2)]+center,color)

    def sphere(self,name,center,radius):
        points=[]
        for a in (-.75,-.35,0,.35,.75):
            t=np.linspace(0,math.tau,90,endpoint=False)
            r=radius*math.sqrt(1-a*a)
            points.extend(np.c_[r*np.cos(t),np.full(len(t),radius*a),r*np.sin(t)]+center)
        # An equatorial upright silhouette keeps the face readable front-on.
        t=np.linspace(0,math.tau,100,endpoint=False)
        points.extend(np.c_[radius*np.cos(t),radius*np.sin(t),np.zeros(len(t))]+center)
        self.add(name,points)

    def finish(self):
        mouth_nodes=set().union(*(set(ids) for name,ids in self.parts.items() if name.startswith('MOUTH_')))
        for name,ids in self.parts.items():
            if not name.startswith('MOUTH_'):
                self.parts[name]=[node for node in ids if node not in mouth_nodes]
        model=self.g.custom(self.name,np.asarray(self.cells)/2,'BAND',self.role,self.colors,self.parts,
                            details={'performer':self.role,'pose_method':'stationary replacement light nodes'})
        from models.snowman_face_contract import face_definition
        model.children.append(('faceInfo',face_definition(model)))
        return model


def mouths(p, center=(0,39,9)):
    shapes={'REST':(2,.35),'MBP':(2,.55),'AH':(2.8,2.3),'EE':(3.1,.9),
            'OH':(1.5,2),'FV':(2,1),'L':(2.1,1.7)}
    for shape in PHONEME_NAMES:
        p.ellipse('MOUTH_'+shape,center,shapes[shape], '#FF9EA9',count=44)


def snowman(p, accent, female=False):
    p.sphere('BASE',(0,11,0),11)
    p.sphere('TORSO',(0,25,0),8.7)
    p.sphere('HEAD',(0,40,0),7)
    p.path('HAT',[(-8,46,1),(8,46,1),(5,46,1),(5,54,1),(-5,54,1),(-5,46,1)],'#93A7BC')
    p.path('SCARF',[(-8,33,5),(8,33,5),(5,33,5),(7,22,7)],accent)
    for i,y in enumerate((17,24,29)):
        p.ellipse('BUTTON_'+str(i),(0,y,9),(.6,.6),'#87A3B8',24)
    for side in (-1,1):p.ellipse('EYE_'+str(side),(side*2.5,42,7),(.65,.8),'#EEFAFF',24)
    p.path('NOSE',[(0,40,7),(3,39.5,9),(0,39,7)],'#FF9B39',30)
    if female:
        p.path('BOW',[(-4,48,7),(0,46.5,8),(4,48,7),(4,45,7),(0,46.5,8),(-4,45,7)],accent,60,True)
    mouths(p)


def performer(g,role,pos,accent):
    name='HX_SNOWMAN_SINGER_FEMALE' if role=='female_singer' else 'HX_SNOWMAN_'+role.upper()
    p=Parts(g,name,pos,role)
    snowman(p,accent,role=='female_singer')
    if role in ('singer','female_singer'):
        p.path('MIC_STAND',[(7,0,10),(7,34,10)],'#8296AA',65)
        p.ellipse('MIC',(7,35,10),(1,1.5),'#D5CBE5',30)
        p.path('ARM_REST',[(-7,29,0),(-12,24,3),(-13,20,4)],WOOD)
        p.path('ARM_ACTIVE',[(-7,29,0),(-12,34,3),(-15,38,4)],WOOD)
        p.path('RIGHT_ARM',[(7,29,0),(11,31,4),(7,35,10)],WOOD)
    elif role=='bassist':
        p.path('BASS_BODY',[(10,7,11),(4,10,11),(5,17,11),(9,20,11),(7,24,11),(10,28,11),(14,28,11),(17,24,11),(15,20,11),(19,17,11),(20,10,11),(14,7,11)],'#CD923F',140,True)
        p.path('BASS_NECK',[(12,24,11),(12,50,11),(15,53,11),(13,55,11),(11,53,11)],'#E6B56D',70)
        p.path('ENDPIN',[(12,7,11),(12,0,11)],'#BDC9DD',20)
        for i in range(4):p.path('STRING_'+str(i),[(10.5+i,10,12),(10.5+i,50,12)],'#F5DE9D',80)
        for i in range(8):p.path('FRET_'+str(i),[(10.5,28+i*2.5,12),(14,28+i*2.5,12)],accent,15)
        p.path('ARM_REST',[(-7,29,2),(1,21,12),(10,18,13)],WOOD)
        p.path('ARM_ACTIVE',[(-7,29,2),(1,23,12),(13,21,13)],WOOD)
        p.path('RIGHT_ARM',[(7,29,2),(15,39,12)],WOOD)
    elif role=='guitarist':
        p.path('GUITAR_BODY',[(-7,16,12),(-10,19,12),(-8,24,12),(-3,24,12),(0,27,12),(4,25,12),(3,21,12),(0,17,12)],'#D67B48',100,True)
        p.path('GUITAR_NECK',[(0,23,12),(18,40,12),(20,40,12),(19,37,12),(2,21,12)],'#D0AF75',80,True)
        for i in range(6):p.path('STRING_'+str(i),[(-6+i*.6,19+i*.4,13),(18+i*.4,38+i*.4,13)],'#F2DDA0',65)
        for i in range(8):p.path('FRET_'+str(i),[(4+i*1.5,25+i*1.5,13),(6+i*1.5,24+i*1.5,13)],accent,15)
        p.path('ARM_REST',[(-7,29,2),(-11,25,8),(-3,23,14)],WOOD)
        p.path('ARM_ACTIVE',[(-7,29,2),(-11,22,8),(-4,17,14)],WOOD)
        p.path('RIGHT_ARM',[(7,29,2),(14,34,14)],WOOD)
    else:
        p.path('KEYBOARD',[(-17,17,12),(17,17,12),(17,22,12),(-17,22,12)],'#8492C8',110,True)
        p.path('STAND',[(-13,0,10),(13,17,12),(-13,17,12),(13,0,10)],'#8BA4B8',75)
        for i in range(24):
            x=-16+i*1.35
            p.path('KEY_'+str(i),[(x,18,13),(x,21.5,13)],WHITE if i%12 not in (1,3,6,8,10) else '#8765BB',16)
        p.path('ARM_REST',[(-7,29,1),(-10,24,5),(-7,22,13),(7,22,13),(10,24,5),(7,29,1)],WOOD)
        p.path('ARM_ACTIVE',[(-7,29,1),(-10,24,5),(-7,19,13),(7,19,13),(10,24,5),(7,29,1)],WOOD)
    return p.finish()


def face(g,kind,x,accent):
    p=Parts(g,'HX_HELIX_FACE_'+kind.upper(),(x,5,0),kind)
    if kind=='tree':outline=[(0,51,0),(-18,35,0),(-10,35,0),(-22,17,0),(-12,17,0),(-24,0,0),(24,0,0),(12,17,0),(22,17,0),(10,35,0),(18,35,0)]
    elif kind=='bulb':outline=[(-8,0,0),(8,0,0),(8,8,0),(19,20,0),(17,35,0),(8,45,0),(-8,45,0),(-17,35,0),(-19,20,0),(-8,8,0)]
    elif kind=='pumpkin':outline=[(-4,46,0),(-4,42,0),(-19,39,0),(-24,24,0),(-21,8,0),(-12,2,0),(12,2,0),(21,8,0),(24,24,0),(19,39,0),(4,42,0),(4,46,0)]
    else:
        p.ellipse('BASE',(0,13,0),(18,13),accent,100)
        p.ellipse('BODY',(0,31,0),(14,10),accent,90)
        outline=[(-10,46,0),(-10,55,0),(10,55,0),(10,46,0),(16,46,0),(-16,46,0)]
    p.path('OUTLINE',outline,accent,230,True)
    # Two interwoven rails sample the outline at different depths. This is an
    # original Helix implementation around familiar singing-prop silhouettes.
    points=_path(outline,230,closed=True)
    t=np.linspace(0,math.tau*6,230,endpoint=False)
    for rail,phase in [('HELIX_A',0),('HELIX_B',math.pi)]:
        offset=np.c_[1.1*np.cos(t+phase),1.1*np.sin(t+phase),3+2*np.sin(t+phase)]
        p.add(rail,points+offset,COLORS[0 if phase==0 else 1])
    cy=31 if kind!='snowman' else 40
    for side in (-1,1):p.ellipse('EYE_'+str(side),(side*6,cy+4,7),(2,2.7),WHITE,44)
    mouths(p,(0,cy-5,8))
    return p.finish()


def build_ensemble(variant='band'):
    if variant not in ('band','faces'):raise ValueError('Unknown ensemble variant')
    g=Garden(title='Helix Snowman Band' if variant=='band' else 'Helix Singing Faces & Snowman Drummer',
             slug='Snowman_Band' if variant=='band' else 'Helix_Singing_Faces',palette=COLORS)
    add_drummer(Structures(g))
    drummer=g.models[0]
    # Keep source backdrop/axis labels out of the helper light. This helper is
    # new scene lighting; all 40 canonical strike/actuator ranges stay untouched.
    from tools.render_drummer_v3_preview import load_component_masks,_content_crop
    from PIL import Image,ImageDraw,ImageChops
    source,masks=load_component_masks()
    crop=Image.new('L',source.size,0);ImageDraw.Draw(crop).rectangle(_content_crop(source),fill=255)
    body=ImageChops.multiply(masks['__preview_body__'],crop).resize((96,72),Image.Resampling.BOX)
    body_nodes=set((np.flatnonzero(np.asarray(body)>=8)+1).tolist())
    dynamic=set().union(*(set(ids) for name,ids in drummer.submodels.items() if name!='BODY_KEEPALIVE'))
    drummer.submodels['BODY_KEEPALIVE']=sorted(body_nodes-dynamic)
    idle=Image.open(ROOT/'fixtures/band_geometry/source/drummer_idle.png').convert('RGB')
    hsv=np.asarray(idle.convert('HSV'))
    visible=Image.fromarray(np.where((hsv[:,:,1]>=55)&(hsv[:,:,2]>=40),255,0).astype(np.uint8))
    visible=ImageChops.multiply(visible,crop).resize((96,72),Image.Resampling.BOX)
    idle_nodes=set((np.flatnonzero(np.asarray(visible)>=8)+1).tolist())|set(drummer.submodels['BODY_KEEPALIVE'])
    rgb=np.asarray(idle.resize((96,72),Image.Resampling.BOX)).reshape(-1,3).astype(float)
    groups={name:[] for name in ('BLUE','RED','GREEN','GOLD','NEUTRAL')}
    for node in sorted(idle_nodes):
        r,green,b=rgb[node-1]
        color='BLUE' if b>r*1.2 else 'GREEN' if green>r*1.2 and green>b*1.1 else 'RED' if r>green*1.4 else 'GOLD' if r>b*1.5 and green>b*1.2 else 'NEUTRAL'
        groups[color].append(node)
    for color,nodes in groups.items():
        if nodes:drummer.submodels['IDLE_'+color]=nodes
    # Lift the preserved planar source model onto the rear center riser.
    drummer.points=np.array([[x-47.5,71-y-35.5+54,-14] for y in range(72) for x in range(96)])
    drummer.attrs.update(WorldPosY='54',WorldPosZ='-14',ScaleX='1',ScaleY='1',ScaleZ='1')
    if variant=='band':
        for role,pos,accent in [('bassist',(-66,0,-8),COLORS[2]),('guitarist',(60,0,-8),COLORS[0]),
                               ('singer',(-26,0,24),COLORS[0]),('female_singer',(26,0,24),COLORS[1]),
                               ('keyboardist',(0,0,53),COLORS[1])]:performer(g,role,pos,accent)
    else:
        for kind,x,accent in [('tree',-82,COLORS[0]),('bulb',-30,COLORS[2]),('pumpkin',30,'#FFA553'),('snowman',82,COLORS[1])]:face(g,kind,x,accent)
    s=Structures(g)
    s.path('STAGE_EDGE',[(-101,0,66),(-101,0,-37),(101,0,-37),(101,0,66)],'STAGE',0,300,True)
    s.path('RISER',[(-32,18,-37),(32,18,-37),(32,18,5),(-32,18,5)],'STAGE',2,160,True)
    for x in (-102,102):s.dna('STAGE_DNA',(x,0,-30),(x,75,-30),4,4,'STAGE',0)
    start=1
    for model in g.models:model.start=start;start+=model.channels
    return g
