"""A refined 3D review rig, separate from preserved native xLights shows.

Member proportions and zones follow the repo's band artwork/specification
contracts. The drummer is a new 3D interpretation of the polished V3 kit and
pose contract, not a claim that another approved source image was recovered.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.interpolate import splprep, splev
import trimesh

from render.keyboard_geometry import generate_keyboard_geometry

SNOW = '#D6EBF3'
WOOD = '#98643C'
METAL = '#7F99AF'
CYAN = '#57D8FF'
PINK = '#EE6EA9'
GOLD = '#E8B759'
TUNINGS = {'bass': (28, 33, 38, 43), 'guitar': (40, 45, 50, 55, 59, 64)}


def string_assignment(note, kind):
    candidates = [(note-open_note, k, note-open_note)
                  for k, open_note in enumerate(TUNINGS[kind])
                  if 0 <= note-open_note <= 24]
    if not candidates:
        return None
    _, string, fret = min(candidates, key=lambda v: (abs(v[0]-4), v[1]))
    return string, fret


def rgb(value):
    return np.array([int(value[i:i+2], 16)/255 for i in (1,3,5)], dtype=np.float32)


def matrix(position, scale=(1,1,1)):
    m = np.eye(4, dtype=np.float32)
    m[:3,:3] = np.diag(scale); m[:3,3] = position
    return m


def line_matrix(a, b, radius):
    a,b = np.asarray(a,float),np.asarray(b,float); delta=b-a
    length = max(np.linalg.norm(delta),1e-5); z=delta/length
    x = np.cross((0,1,0),z)
    if np.linalg.norm(x)<1e-5:
        x=np.array((1.,0,0))
    x/=np.linalg.norm(x); y=np.cross(z,x)
    m=np.eye(4,dtype=np.float32);m[:3,:3]=np.c_[x*radius,y*radius,z*length];m[:3,3]=(a+b)/2
    return m


def smooth(points, closed=False, count=90):
    p=np.asarray(points,float)
    if closed and not np.allclose(p[0],p[-1]):
        p=np.vstack((p,p[0]))
    tck,_=splprep(p.T,s=0,k=min(3,len(p)-1),per=closed)
    return np.array(splev(np.linspace(0,1,count,endpoint=not closed),tck)).T


def tube(points, radius=.025, closed=False):
    p=np.asarray(points,float)
    p=p[np.r_[True,np.linalg.norm(np.diff(p,axis=0),axis=1)>1e-8]]
    if closed:
        if np.allclose(p[0],p[-1]):p=p[:-1]
        p=np.vstack((p,p[0]))
    tangent=np.gradient(p,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-8)
    ref=np.tile((0.,0,1),(len(p),1));near=np.abs(tangent[:,2])>.9;ref[near]=(0,1,0)
    a=np.cross(tangent,ref);a/=np.linalg.norm(a,axis=1,keepdims=True);b=np.cross(tangent,a)
    theta=np.linspace(0,math.tau,8,endpoint=False)
    vertices=(p[:,None,:]+radius*(a[:,None,:]*np.cos(theta)[None,:,None]+b[:,None,:]*np.sin(theta)[None,:,None])).reshape(-1,3)
    faces=[]
    for i in range(len(p)-1):
        for j in range(8):
            k=(j+1)%8;faces.extend(((i*8+j,i*8+k,(i+1)*8+j),(i*8+k,(i+1)*8+k,(i+1)*8+j)))
    return trimesh.Trimesh(vertices=vertices,faces=faces,process=False)


def instrument_body(points, depth=.20):
    outline=smooth([(x,y,0) for x,y in points],closed=True,count=90)[:,:2]
    center=outline.mean(axis=0);n=len(outline)
    vertices=np.vstack((np.c_[outline,np.full(n,-depth/2)],np.c_[outline,np.full(n,depth/2)],
                        [(*center,-depth/2),(*center,depth/2)]))
    faces=[]
    for i in range(n):
        j=(i+1)%n;faces.extend(((2*n,i,j),(2*n+1,n+j,n+i),(i,n+i,j),(j,n+i,n+j)))
    return trimesh.Trimesh(vertices=vertices,faces=faces,process=True)


class BandScene:
    def __init__(self, variant='band'):
        self.variant=variant;self.instances=[];self.custom=[];self.rigs=[]
        self.box('stage',(0,-.17,0),(13,.28,7.6),'#101E35')
        for i in range(3):self.box(f'step_{i}',(0,-.24-i*.15,3.9+i*.30),(10+i,.18,.42),'#162B46')
        self.box('drum_riser',(0,.27,-1.65),(3.45,.5,2.3),'#253148')
        for x in (-6.1,6.1):
            t=np.linspace(0,math.tau*2,140)
            for phase,color in ((0,CYAN),(math.pi,PINK)):
                p=np.c_[x+.32*np.cos(t+phase),.2+t/math.tau*1.9,-2.4+.32*np.sin(t+phase)]
                self.curve('helix_column',p,color,.026,slot=0)
        for j in range(3):
            t=np.linspace(0,math.pi,100)
            p=np.c_[np.cos(t)*(5.9-j*.42),np.sin(t)*(4.8-j*.25)+.2,np.full(len(t),-3.3+j*.25)]
            self.curve('stage_arch',p,[CYAN,GOLD,PINK][j],.020,slot=j)
        self.curve('stage_front',[(x,.01,3.5) for x in np.linspace(-6.4,6.4,120)],CYAN,.025,slot=2)
        self.drummer()
        if variant=='band':
            for role,p,accent in [('bass',(-4,0,-.25),GOLD),('guitar',(4,0,-.25),CYAN),
                                  ('lead',(-1.75,0,1.35),CYAN),('harmony',(1.75,0,1.35),PINK),
                                  ('piano',(0,0,3.0),PINK)]:
                self.performer(role,np.array(p,float),accent)
        else:
            for kind,x,color in [('tree',-4.7,CYAN),('bulb',-1.6,GOLD),('pumpkin',1.6,'#F08945'),('snowman',4.7,PINK)]:
                self.singing_prop(kind,x,color)

    def primitive(self,kind,name,position,scale,color,slot=-1,update=None):
        self.instances.append({'kind':kind,'name':name,'matrix':matrix(position,scale),
                               'color':rgb(color),'slot':slot,'update':update})

    def sphere(self,name,position,scale,color=SNOW,slot=-1,update=None):
        self.primitive('sphere',name,position,scale,color,slot,update)

    def box(self,name,position,scale,color,slot=-1):
        self.primitive('box',name,position,scale,color,slot)

    def rod(self,name,a,b,radius,color=METAL,slot=-1):
        self.instances.append({'kind':'cylinder','name':name,'matrix':line_matrix(a,b,radius),
                               'color':rgb(color),'slot':slot,'update':None})

    def curve(self,name,points,color,radius=.025,closed=False,slot=-1):
        self.custom.append({'name':name,'mesh':tube(points,radius,closed),'color':rgb(color),'slot':slot})

    def mesh(self,name,mesh,color,position=(0,0,0),slot=-1):
        mesh=mesh.copy();mesh.apply_translation(position)
        self.custom.append({'name':name,'mesh':mesh,'color':rgb(color),'slot':slot})

    def snowman(self,role,p,accent,female=False):
        for label,center,scale in [('base',(0,.55,0),(.58,.56,.48)),('torso',(0,1.4,0),(.47,.48,.41)),('head',(0,2.28,0),(.43,.43,.41))]:
            self.sphere(role+'_'+label,p+center,scale)
        self.sphere(role+'_scarf',p+(0,1.90,.01),(.44,.13,.42),accent)
        self.box(role+'_scarf_tail',p+(.23,1.48,.43),(.14,.70,.06),accent)
        for y in (.35,.67,1.1,1.4):self.sphere(role+'_coal_button',p+(0,y,.47),(.045,.045,.027),'#101D2B')
        for x in (-.13,.13):
            self.sphere(role+'_eye',p+(x,2.36,.383),(.059,.067,.04),'#071422')
            self.sphere(role+'_eye_glint',p+(x-.015,2.385,.422),(.017,.019,.012),'#FFFFFF')
            if female:
                for k in range(3):self.rod('eyelash',p+(x,2.405,.397),p+(x+(k-1)*.025,2.46,.404),.009,'#162635')
        self.sphere(role+'_carrot',p+(.038,2.23,.435),(.145,.042,.047),'#F8953F')
        if female:
            for side in (-1,1):self.sphere('bow',p+(side*.105,2.72,.06),(.135,.08,.065),accent)
            self.sphere('bow_center',p+(0,2.72,.10),(.05,.045,.05),GOLD)
        else:
            self.rod(role+'_hat_brim',p+(0,2.665,0),p+(0,2.70,0),.54,'#142234')
            self.rod(role+'_hat_crown',p+(0,2.70,0),p+(0,3.00,0),.35,'#142234')
            self.rod(role+'_hat_ribbon',p+(0,2.72,0),p+(0,2.78,0),.355,accent)
            self.sphere('holly',p+(.29,2.83,.25),(.08,.035,.03),'#339360')
            self.sphere('berry',p+(.30,2.83,.29),(.03,.03,.026),'#EE6A6A')
        return p+(0,2.12,.407)

    def mouth(self,name,center,role,color='#180D1B'):
        # One deforming mouth surface, never seven simultaneously lit outlines.
        index=len(self.instances)
        self.sphere(name,center,(.12,.025,.030),color)
        self.instances[index]['mouth_role']=role;self.instances[index]['mouth_center']=center

    def arm(self,name,shoulder,elbow,hand,role,side):
        ids=[]
        for a,b in ((shoulder,elbow),(elbow,hand)):
            ids.append(len(self.instances));self.rod(name,a,b,.046,WOOD)
        ids.append(len(self.instances));self.sphere(name+'_mitten',hand,(.10,.075,.08))
        self.rigs.append({'name':name,'role':role,'side':side,'shoulder':shoulder,'elbow':elbow,'hand':hand,'ids':ids})

    def performer(self,role,p,accent):
        mouth=self.snowman(role,p,accent,role=='harmony');self.mouth(role+'_mouth',mouth,role)
        if role in ('lead','harmony'):
            mic=p+(.49,2.20,.65)
            self.rod(role+'_mic_stand',p+(.49,.10,.65),mic,.025,METAL)
            self.sphere(role+'_vintage_mic',mic,(.075,.13,.055),METAL,3 if role=='lead' else 4)
            for j in range(5):self.rod('mic_grille',mic+(-.058,-.075+j*.035,.056),mic+(.058,-.075+j*.035,.056),.005,'#202E3F')
            self.rod('mic_base',p+(.22,.05,.65),p+(.75,.05,.65),.04,METAL)
            self.arm(role+'_left',p+(-.36,1.65,.05),p+(-.59,1.30,.15),p+(-.55,1.05,.29),role,'left')
            self.arm(role+'_right',p+(.36,1.65,.05),p+(.62,1.90,.4),mic,role,'right')
        elif role=='bass':
            body=instrument_body([(-.32,-.75),(-.52,-.4),(-.37,-.05),(-.21,.12),(-.39,.37),(-.23,.71),(.23,.71),(.39,.37),(.21,.12),(.37,-.05),(.52,-.4),(.32,-.75)])
            q=p+(.58,1.03,.48);self.mesh('upright_bass_body',body,'#B96C31',q)
            self.curve('bass_binding',smooth([tuple(v+q+(0,0,.108)) for v in np.c_[body.vertices[:90,:2],np.zeros(90)]],True),GOLD,.015,True)
            self.box('bass_fingerboard',p+(.58,2.40,.57),(.14,1.55,.08),'#282323')
            self.sphere('bass_scroll',p+(.58,3.27,.58),(.13,.11,.10),'#B96C31')
            self.rod('bass_endpin',p+(.58,.04,.5),p+(.58,.32,.5),.021,METAL)
            self.box('bass_bridge',p+(.58,.58,.63),(.34,.08,.05),GOLD)
            for j in range(4):self.rod(f'bass_string_{j}',p+(.535+j*.029,.42,.65),p+(.535+j*.029,3.18,.65),.008,'#DCC79A',13+j)
            for side in (-1,1):
                pts=p+np.array([(side*.22+.58,.65,.602),(side*.30+.58,.88,.602),(side*.22+.58,1.04,.602),(side*.29+.58,1.29,.602)])
                self.curve('bass_f_hole',smooth(pts), '#211D21',.018)
            self.arm('bass_pluck',p+(-.36,1.65,.05),p+(-.15,1.26,.50),p+(.59,1.05,.73),role,'pluck')
            self.arm('bass_finger',p+(.36,1.65,.05),p+(.77,2.0,.49),p+(.58,2.3,.68),role,'finger')
        elif role=='guitar':
            body=instrument_body([(-.52,-.18),(-.50,.18),(-.25,.37),(-.10,.20),(.20,.37),(.39,.20),(.32,-.12),(.05,-.40),(-.30,-.39)],.17)
            q=p+(-.16,1.06,.58);self.mesh('electric_guitar_body',body,'#B14940',q)
            begin=p+(.02,1.27,.68);end=p+(1.22,2.32,.68)
            self.rod('guitar_neck',begin,end,.058,'#593B2B')
            self.rod('guitar_headstock',end,end+(.20,.20,0),.086,GOLD)
            for j in range(6):
                off=np.array((-(j-2.5)*.014,(j-2.5)*.014,.020))
                self.rod(f'guitar_string_{j}',p+(-.40,.83,.69)+off,end+off,.005,'#D6D6C4',17+j)
                self.sphere('tuning_pin',end+(.07+(j//2)*.045,.07+(j//2)*.045,(j%2-.5)*.15),(.025,.025,.023),METAL)
            for t in np.linspace(.12,.9,12):
                v=begin+(end-begin)*t
                self.rod('guitar_fret',v+(-.05,.05,.02),v+(.05,-.05,.02),.008,METAL)
            self.box('pickup',p+(-.17,1.11,.70),(.08,.20,.035),'#D3D4C8')
            self.box('bridge',p+(-.33,.89,.70),(.06,.17,.035),METAL)
            self.arm('guitar_strum',p+(-.36,1.65,.05),p+(-.65,1.26,.40),p+(-.17,1.02,.79),role,'strum')
            self.arm('guitar_fret_hand',p+(.36,1.65,.05),p+(.76,1.87,.50),p+(.87,2.02,.73),role,'finger')
        else:
            self.box('keyboard_case',p+(0,1.18,.55),(2.8,.19,.85),'#282A43')
            geometry=generate_keyboard_geometry(48,84)
            for key in geometry.keys:
                x=(key.x+key.width/2-.5)*2.65
                z=.43 if key.is_black else .56
                self.box('piano_key_'+str(key.pitch),p+(x,1.30+(key.is_black*.047),z),
                         (key.width*2.65*.92,.07,.43 if key.is_black else .72),
                         '#152235' if key.is_black else '#E7E7D6',23+key.pitch-48)
            self.rod('keyboard_stand_left',p+(-1.12,.05,.50),p+(1.0,1.12,.5),.045,METAL)
            self.rod('keyboard_stand_right',p+(1.12,.05,.50),p+(-1.0,1.12,.5),.045,METAL)
            self.arm('keyboard_left',p+(-.36,1.65,.05),p+(-.58,1.48,.40),p+(-.62,1.41,.73),role,'left')
            self.arm('keyboard_right',p+(.36,1.65,.05),p+(.58,1.48,.40),p+(.62,1.41,.73),role,'right')

    def drummer(self):
        p=np.array((0,.52,-1.70));mouth=self.snowman('drummer',p,'#CA5753');self.mouth('drummer_mouth',mouth,'drummer')
        self.rod('kick_shell',p+(0,.63,.45),p+(0,.63,1.05),.57,'#324C6E',5)
        t=np.linspace(0,math.tau,90)
        self.curve('kick_rim',p+np.c_[.59*np.cos(t),.63+.59*np.sin(t),np.full(len(t),1.07)],'#E96657',.025,True,5)
        for angle in np.linspace(0,math.tau,6,endpoint=False):
            a=p+(.40*np.cos(angle),.63+.40*np.sin(angle),1.085);b=p+(0,.63,1.085)
            self.rod('kick_snowflake',b,a,.017,CYAN,5)
        kit=[('snare',(-.88,1.13,.52),.36,6,PINK),('tom_high',(-.54,1.62,.08),.29,8,'#429663'),
             ('tom_mid',(.46,1.55,.06),.33,9,'#429663'),('tom_floor',(.97,.83,-.09),.39,10,'#429663')]
        for name,center,radius,slot,color in kit:
            q=p+center;self.rod(name+'_shell',q+(0,-.24,0),q+(0,0,0),radius,color,slot)
            self.rod(name+'_head',q,q+(0,.032,0),radius,'#CCDDCB',slot)
            self.rod(name+'_stand',q+(0,-center[1]+.06,0),q+(0,-.26,0),.021,METAL)
            self.curve(name+'_rim',q+np.c_[radius*np.cos(t),np.full(len(t),.038),radius*np.sin(t)],METAL,.014,True,slot)
        for name,center,slot,radius in [('cymbal_left',(-1.42,1.99,-.04),11,.46),('cymbal_right',(1.40,1.96,-.10),12,.49),('hi_hat',(-1.20,1.40,.54),7,.33)]:
            q=p+center;self.sphere(name+'_dish',q,(radius,.035,radius),GOLD,slot)
            self.sphere(name+'_bell',q+(0,.022,0),(.09,.044,.09),GOLD,slot)
            self.rod(name+'_stand',p+(center[0],.05,center[2]),q,.019,METAL)
        self.arm('drum_left_arm',p+(-.36,1.65,.05),p+(-.66,1.48,.30),p+(-.64,1.50,.55),'drums','left')
        self.arm('drum_right_arm',p+(.36,1.65,.05),p+(.66,1.48,.30),p+(.64,1.50,.55),'drums','right')
        for side in ('left','right'):
            self.rigs[-2 if side=='left' else -1]['stick_id']=len(self.instances)
            self.rod('drum_'+side+'_stick',p+(-.64 if side=='left' else .64,1.50,.55),p+(-.95 if side=='left' else .95,1.15,.6),.015,GOLD)

    def singing_prop(self,kind,x,color):
        p=np.array((x,.1,1.0));cy=1.75
        if kind=='tree':outline=[(0,3.1,0),(-.7,2.0,0),(-.4,2,0),(-.9,1.0,0),(-.6,1,0),(-1.0,.2,0),(1.0,.2,0),(.6,1,0),(.9,1,0),(.4,2,0),(.7,2,0)]
        elif kind=='bulb':outline=[(-.3,.2,0),(.3,.2,0),(.3,.6,0),(.83,1.3,0),(.65,2.4,0),(0,2.85,0),(-.65,2.4,0),(-.83,1.3,0),(-.3,.6,0)]
        elif kind=='pumpkin':outline=[(-.12,2.8,0),(-.12,2.55,0),(-.76,2.35,0),(-1.0,1.45,0),(-.75,.4,0),(0,.25,0),(.75,.4,0),(1.0,1.45,0),(.76,2.35,0),(.12,2.55,0),(.12,2.8,0)]
        else:
            self.snowman('face_snowman',p,color);self.mouth('face_snowman_mouth',p+(0,2.12,.42),'faces');return
        outline=smooth(outline,True,count=130)
        for phase,c in ((0,color),(math.pi,CYAN)):
            t=np.linspace(0,math.tau*6,len(outline));off=np.c_[.028*np.cos(t+phase),.028*np.sin(t+phase),.08*np.sin(t+phase)]
            self.curve(kind+'_helix_rail',p+outline+off,c,.025,True,3)
        for side in (-1,1):self.sphere(kind+'_eye',p+(side*.26,cy+.2,.1),(.09,.12,.05),'#EDF2E0')
        self.mouth(kind+'_mouth',p+(0,cy-.27,.10),'faces','#FFE4A8')

    def export_glb(self,path):
        primitives={'sphere':trimesh.creation.icosphere(subdivisions=2),
                    'box':trimesh.creation.box(),
                    'cylinder':trimesh.creation.cylinder(radius=1,height=1,sections=20)}
        scene=trimesh.Scene()
        for i,item in enumerate(self.instances):
            mesh=primitives[item['kind']].copy();mesh.visual.vertex_colors=np.r_[item['color']*255,255].astype(np.uint8)
            scene.add_geometry(mesh,node_name=f'{item["name"]}_{i}',transform=item['matrix'])
        for i,item in enumerate(self.custom):
            mesh=item['mesh'].copy();mesh.visual.vertex_colors=np.r_[item['color']*255,255].astype(np.uint8)
            scene.add_geometry(mesh,node_name=f'{item["name"]}_curve_{i}')
        path.write_bytes(scene.export(file_type='glb'))
