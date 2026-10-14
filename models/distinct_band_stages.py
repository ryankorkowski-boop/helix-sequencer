"""Six contrasting stages and a combined garden, retaining the approved rig.

Wire contours are artistic prop previews, not measured fabrication drawings.
"""
from __future__ import annotations
import math
import numpy as np
import trimesh
from models.refined_band_scene import RefinedBandScene
from models.band_performance_scene import matrix,line_matrix,tube,rgb
from models.intricate_band_scene import IntricateBandScene,LAYOUTS
from models.ultimate_showcase import Garden
from models.approved_concepts import Structures
from models.expressive_band_face import add_expressive_mouths,update_expressive_mouth

STAGES={
    'ember_amphitheatre':'Ember Amphitheatre',
    'glacier_pier':'Glacier Pier',
    'cathedral_organ':'Cathedral Organ',
    'circuit_garage':'Circuit Garage',
    'orbital_halo':'Orbital Halo',
    'lantern_garden':'Living Lantern Garden',
}
STYLE_PALETTES={'ember_amphitheatre':('#E9AB5D','#CF7756','#FFE0A8'),
    'glacier_pier':('#91D9FF','#C9F0FF','#72E7DE'),
    'cathedral_organ':('#E4C585','#B599C8','#E3D3B0'),
    'circuit_garage':('#E67F67','#8BBF9B','#D9D7C8'),
    'orbital_halo':('#9CB9F8','#D9A1C7','#B1C8F0'),
    'lantern_garden':('#93C694','#E7B97E','#7CC6B0')}


class DistinctBandScene(RefinedBandScene):
    def __init__(self,stage,wire=False,readable_faces=True):
        if stage not in STAGES:raise ValueError(stage)
        super().__init__('prismatic_orrery',(48,96),neutral_performers=True)
        self.stage=stage;self.wire=wire;self.feature_names=[]
        # Keep indices stable: existing poses and key/string maps reference them.
        prefixes=('bass','guitar','electric_guitar','upright_bass','lead','harmony','piano','keyboard','xylophone','drum_riser')
        for o in self.instances:
            keep=bool(o.get('performer_role') or o['name'].startswith(prefixes))
            if not keep:o['kind']='hidden'
            solid_strings=o.get('performer_role') in ('bass','guitar')
            if wire and keep and not solid_strings and o['kind']=='sphere' and not o['name'].startswith('xylophone_mallet') and any(k in o['name'] for k in ('_base','_torso','_head','_scarf','_hat_crown')):
                o['kind']='wire_sphere';o['color']=rgb('#D4E1D6');o['slot']=177
            if wire and keep and not solid_strings and o['name'].endswith(('_eye','_coal_button')):o['color']=rgb('#E1D5AE')
        self.custom=[o for o in self.custom if o['name'].startswith(prefixes)]
        # Retain the actual closed instrument surfaces, including the electric
        # guitar mesh that the old prefix filter accidentally dropped.
        if readable_faces:add_expressive_mouths(self,wire)
        self.palette=STYLE_PALETTES[stage]
        getattr(self,stage)()
        self.technical_proof=dict(stage=stage,title=STAGES[stage],style='wire band with solid strings' if wire else 'sculpted snow band',
            neutral_singers=True,neutral_mallet_player=True,features=self.feature_names,
            preserved_guitar_rig=True,solid_string_players=True,solid_instrument_bodies=True,
            expressive_lips_and_tongues=readable_faces,physical_fabrication_dimensions=False)

    def update_singer_mouth(self,role,shape,energy):
        if hasattr(self,'expressive_mouths'):update_expressive_mouth(self,role,shape,energy)

    def path(self,name,points,color=0,radius=.026,slot=64,closed=False):
        self.curve(name,points,self.palette[color%3],radius,closed,slot)
        if name not in self.feature_names:self.feature_names.append(name)

    def ring(self,name,center,rx,ry,color=0,plane='xy',slot=64):
        t=np.linspace(0,math.tau,100,endpoint=False);p=np.zeros((len(t),3))
        a,b={'xy':(0,1),'xz':(0,2),'yz':(2,1)}[plane];p[:,a]=rx*np.cos(t);p[:,b]=ry*np.sin(t)
        self.path(name,p+center,color,slot=slot,closed=True)

    def ember_amphitheatre(self):
        self.box('ember_deck',(0,-.3,.5),(18.8,.25,9.4),'#39271E')
        for k in range(4):
            t=np.linspace(0,math.pi,150);r=8.9+k*.24
            self.path('amber_apron',np.c_[r*np.cos(t),np.full(len(t),-.05),3.7+2.3*np.sin(t)],k,slot=64+k)
        for x in np.arange(-8.6,9,.70):self.path('deck_planks',[(x,-.15,-3.9),(x,-.15,4.8)],2,.009,64)
        for side in (-1,1):
            for j in range(8):
                x=side*(4.5+j*.48);h=2.6+(7-j)*.34
                self.path('sunburst_fins',[(x,.1,-4.5),(x,h,-4.5),(x+side*.19,h+.25,-4.3)],j,slot=65+j)
        for j in range(5):
            r=2.2+j*.45;t=np.linspace(0,math.pi,120)
            self.path('setting_sun',np.c_[r*np.cos(t),3.5+r*np.sin(t),np.full(len(t),-5)],j,slot=68+j)
        self.feature_names+=['wooden deck','fan amphitheatre','sunburst backdrop']

    def glacier_pier(self):
        self.box('ice_pier_deck',(0,-.3,.4),(18.2,.20,8.5),'#183A4C')
        for side in (-1,1):
            self.box('pontoon',(side*7.3,-.65,.3),(1.4,.65,10.3),'#385A6B')
            for j in range(7):
                x=side*(4.9+j*.54);h=2.8+1.7*np.sin(j*.72)**2
                self.path('ice_crystal',[(x,0,-4.1),(x-.26,h*.75,-4.1),(x,h,-4.1),(x+.26,h*.75,-4.1),(x,0,-4.1)],j,slot=66+j)
        for j in range(7):
            x=np.linspace(-10,10,160)
            self.path('water_waves',np.c_[x,np.full(len(x),-.47),5.1+j*.28+.17*np.sin(x*.9+j)],j,.019,70+j)
        t=np.linspace(0,1,180)
        for k in range(6):
            self.path('aurora_ribbon',np.c_[-9+18*t,5.3+.7*np.sin(t*8+k*.2)+k*.17,np.full(len(t),-5.8)],k,.028,76+k)
        self.feature_names+=['twin pontoons','water surface','ice skyline','aurora ribbons']

    def cathedral_organ(self):
        self.box('cathedral_deck',(0,-.3,.3),(18.8,.25,8.7),'#242334')
        for x in np.linspace(-8.3,8.3,25):
            h=3.8+2.6*(1-abs(x)/9);c=0 if int(abs(x)*4)%2 else 1
            self.rod('organ_pipe',(x,.15,-4.6),(x,h,-4.6),.13,self.palette[c],64+int(abs(x)*3)%20)
            self.ring('pipe_mouth',(x,h-.3,-4.45),.06,.13,c,slot=70)
        for side in (-1,1):
            for k in range(3):
                x=side*(6.1+k*.75)
                self.path('gothic_window',[(x-.5,0,-5),(x-.5,5,-5),(x,6.4,-5),(x+.5,5,-5),(x+.5,0,-5)],k,.029,80+k)
        self.path('nave_chevrons',[(-9,.02,4.5),(-3,.02,0),(0,.02,-3),(3,.02,0),(9,.02,4.5)],0,.035,88)
        self.feature_names+=['pipe organ','pointed windows','nave aisle']

    def circuit_garage(self):
        self.box('circuit_deck',(0,-.3,.3),(19,.25,8.8),'#111B21')
        for x in np.linspace(-9,9,10):
            self.path('pcb_traces',[(x,-.05,4.6),(x,-.05,1),(x+.45,-.05,.3),(x+.45,-.05,-3.9)],int(abs(x)),.020,64+int(abs(x)))
        for side in (-1,1):
            for k in range(4):
                x=side*(4.8+k*1.0)
                self.path('rectangular_circuit_portal',[(x-.4,0,-4.7),(x-.4,5+k*.2,-4.7),(x+.4,5+k*.2,-4.7),(x+.4,0,-4.7)],k,.032,72+k)
                for j in range(7):self.box('circuit_node',(x,1+j*.53,-4.5),(.23,.17,.10),self.palette[j%3],80+j)
        self.path('sawtooth_scope',[(-4,4.9,-5.4),(-2.7,4.9,-5.4),(-2.5,6.4,-5.4),(-1.8,3.5,-5.4),(-1.1,5.5,-5.4),(0,4.9,-5.4),(4,4.9,-5.4)],1,.035,91)
        self.feature_names+=['PCB floor','square portals','circuit nodes','sawtooth oscilloscope']

    def orbital_halo(self):
        disk=line_matrix((0,-.55,0),(0,-.3,0),9.3)
        self.instances.append(dict(kind='cylinder',name='halo_arena',matrix=disk,color=rgb('#16263F'),slot=-1,update=None))
        for j in range(5):self.ring('orbit_apron',(0,-.03+j*.035,0),8.9-j*.5,5.5-j*.25,j,'xz',64+j)
        for j in range(6):
            t=np.linspace(0,math.tau,150);r=2.8+j*.27
            self.path('orbital_bands',np.c_[r*np.cos(t),4.7+r*.65*np.sin(t),-5+.6*np.sin(t+j)],j,.024,70+j,True)
        for side in (-1,1):
            for k in range(5):
                x=side*(4.6+k*.9);self.ring('planetary_moon',(x,3+(k%3),-4.7),.34,.34,k,slot=78+k)
                self.path('comet_tail',[(x,3+k%3,-4.7),(x-side*.4,2.5+k%3,-4.7),(x-side*1.2,2.2+k%3,-4.7)],k,.015,85+k)
        self.feature_names+=['circular arena','planetary rings','moons','comets']

    def lantern_garden(self):
        self.box('garden_ground',(0,-.3,.2),(19,.24,9.7),'#193126')
        for side in (-1,1):
            for k in range(5):
                x=side*(4.8+k*.9);h=3.1+(k%3)*.9
                self.path('branch_trunk',[(x,0,-4.5),(x+.12,h*.55,-4.5),(x,h,-4.5)],k,.035,64+k)
                for branch in (-1,1):
                    self.path('leaf_branch',[(x,h*.60,-4.5),(x+branch*.5,h*.80,-4.4),(x+branch*.8,h*.95,-4.5)],k+1,.025,72+k)
                self.ring('lantern_crown',(x,h,-4.45),.48,.70,k,slot=80+k)
        for k in range(6):
            t=np.linspace(0,1,130)
            self.path('canopy_vines',np.c_[-8+16*t,5.2+1.0*np.sin(np.pi*t)+k*.13,np.full(len(t),-5.7)+.4*np.sin(t*9+k)],k,.021,88+k)
        for j in range(6):
            x=np.linspace(-9,9,150)
            self.path('garden_paths',np.c_[x,np.full(len(x),-.07),4.5-j*.4+.3*np.sin(x*.5+j)],j,.019,96+j)
        self.feature_names+=['branch trees','lantern crowns','vine canopy','curved paths']


class TwinBandGarden:
    """Two live rigs with immutable local coordinates and separate slot banks."""
    def __init__(self,a,b,super_layout=False):
        self.scenes=(a,b);self.instances=[];self.custom=[];self.sources=[];self.transforms=[]
        for k,scene in enumerate(self.scenes):
            world=np.eye(4);world[0,3]=(-10.0,10.0)[k];self.transforms.append(world)
            for o in scene.instances:
                if o['kind']=='hidden':continue
                item=dict(o,matrix=world@o['matrix'],slot=o['slot']+192*k if o['slot']>=0 else -1)
                self.instances.append(item);self.sources.append((item,o,world))
            for o in scene.custom:
                mesh=o['mesh'].copy();mesh.apply_transform(world)
                self.custom.append(dict(o,mesh=mesh,slot=o['slot']+192*k if o['slot']>=0 else -1))
        self.dry_drummer_corners=a.dry_drummer_corners+(-10,0,0)
        self.second_drummer_corners=b.dry_drummer_corners+(10,0,0)
        self.feature_inventory={a.stage:a.feature_names,b.stage:b.feature_names}
        self.inherited_layouts=[];self.technical_models=[]
        if super_layout:self.add_super_features()

    def sync(self):
        for dst,src,world in self.sources:dst['matrix']=world@src['matrix']

    def add_super_features(self):
        # Include geometry from every member of the six-layout stage family.
        # Place each distinctive backdrop in its own region, keeping band views open.
        placements=[(-15,1,-11),(0,3,-15),(15,1,-11),(-18,0,6),(0,0,7),(18,0,6)]
        for k,(name,position) in enumerate(zip(LAYOUTS,placements)):
            scene=IntricateBandScene(name)
            features=[o for o in scene.custom if o['slot']>=64 and not o['name'].startswith(('cymatic_floor','floor_radial'))]
            for o in features:
                mesh=o['mesh'].copy();mesh.apply_scale(.60 if k<3 else .32);mesh.apply_translation(position)
                self.custom.append(dict(o,name='super_'+name+'_'+o['name'],mesh=mesh,slot=64+k*5+o['slot']%5))
            self.inherited_layouts.append(name)
        # Reuse actual approved technical/artistic model node coordinates:
        # double helix, spiral tree, matrices, stars, arches and sculptural fauna.
        g=Garden();s=Structures(g)
        s.dna('SUPER_DOUBLE_HELIX',[-14,0,-13],[-14,8,-13],.8,3,'DNA',0)
        s.tree(23,-8,7,1.7,color=1);s.tree(-23,-8,7,1.7,color=0)
        s.mesh('SUPER_WAVE_MATRIX',[0,7,-15],10,3,'MATRIX',1,wave=.8)
        s.arch((0,0,-13),48,13,2,True,'ARCHES')
        s.starburst([0,11.5,-14],1.5,2,'STAR')
        from models.advanced_concepts import whale,manta,phoenix,cube
        whale(s,center=(0,0,0),scale=1,angle=15,zone='WHALE')
        manta(s,center=(19,8,-12),zone='MANTA')
        # Manta's authored coordinates are in design feet; rescale its node set.
        for m in g.models:
            if m.zone=='MANTA':m.points=(m.points-(19,8,-12))*.04+(19,8,-12)
            elif m.zone=='WHALE':m.points=m.points*.038+(-19,8,-12)
        cube(s,[0,6,-13],2.4,2,'CUBE',yaw=20)
        # Existing finite stock-family gallery gives the union a broad model mix.
        from models.ultimate_showcase import build_ultimate_garden
        original=build_ultimate_garden()
        excluded={'Custom','Image','Label','Channel Block'}
        seen=set()
        for m in original.models:
            if m.display in excluded or m.display in seen:continue
            seen.add(m.display)
            # Retain actual native nodes at a scale suitable for foreground props.
            pts=m.points.copy();span=np.ptp(pts,axis=0);pts-=np.mean(pts,axis=0)
            pts*=2.2/max(float(span.max()),1)
            x=-23+(len(seen)-1)%12*4.2;z=6.2+(len(seen)-1)//12*3
            pts+=(x,1.2,z)
            for j,p in enumerate(pts[::max(1,len(pts)//160)]):
                self.instances.append(dict(kind='light_point',name='native_'+m.display,matrix=matrix(p,(.026,.026,.026)),color=rgb(m.colors[min(j*max(1,len(pts)//160),len(m.colors)-1)]),slot=64+j%48,update=None))
            self.technical_models.append(m.display)
        for k,m in enumerate(g.models):
            for j,p in enumerate(m.points[::max(1,len(m.points)//180)]):
                self.instances.append(dict(kind='light_point',name=m.name,matrix=matrix(p,(.033,.033,.033)),color=rgb(m.colors[min(j*max(1,len(m.points)//180),len(m.colors)-1)]),slot=64+k%48,update=None))
            self.technical_models.append(m.zone)
        self.feature_inventory.update({name:'included distinctive geometry' for name in self.inherited_layouts})
