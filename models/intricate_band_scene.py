"""Six volumetric, layered musical stages containing the preserved band rig."""
from __future__ import annotations

import math
import numpy as np
import trimesh

from models.band_performance_scene import BandScene, CYAN, PINK, GOLD, matrix

LAYOUTS = {
    'knot_cathedral': 'Borealis Knot Cathedral',
    'prismatic_orrery': 'Prismatic Orrery',
    'woven_aurora': 'Woven Aurora Vault',
    'cymatic_geode': 'Cymatic Geode Garden',
    'infinity_observatory': 'Infinity Observatory',
    'quasicrystal_theatre': 'Quasicrystal Theatre',
}
PALETTE = (CYAN, '#886DFF', PINK, GOLD, '#5DE2B5', '#719BFF')


class IntricateBandScene(BandScene):
    def __init__(self, layout):
        if layout not in LAYOUTS:
            raise ValueError(layout)
        self.layout = layout
        super().__init__('band')
        self.custom = [x for x in self.custom if x['name'] not in ('stage_arch','helix_column')]
        # Open a central sightline to the original physical drummer display.
        for item in self.instances:
            if item['name'].startswith(('piano_','keyboard_')):
                item['matrix'][0,3] += 6.5
                item['matrix'][2,3] -= .45
                if 'mouth_center' in item:
                    item['mouth_center'] = item['mouth_center'] + (6.5,0,-.45)
        for rig in self.rigs:
            if rig['role']=='piano':
                for k in ('shoulder','elbow','hand'):
                    rig[k] = rig[k]+(6.5,0,-.45)
        # Canonical drummer is rendered by its exact source-art pose compositor,
        # mounted in XYZ on the riser. No replacement kit/arm geometry is made.
        self.dry_drummer_corners = np.array([[-2.25,.80,-1.40],[2.25,.80,-1.40],
                                            [-2.25,3.72,-1.40],[2.25,3.72,-1.40]],dtype='f4')
        self.box('expanded_stage',(0,-.30,-.6),(19,.20,11.8),'#0E2034')
        self.box('back_plinth',(0,.06,-4.9),(18,.20,1.5),'#1E2B45')
        self.floor_rosette()
        getattr(self,layout)()
        rng=np.random.default_rng(1729)
        for j in range(120):
            x,y,z=rng.uniform(-9.8,9.8),rng.uniform(.5,8.6),rng.uniform(-8.5,-7.5)
            self.sphere('constellation_pixel',(x,y,z),(.016,.016,.016),PALETTE[j%6],64+j%48)
        self.technical_proof = self.validate()

    def drummer(self):
        # Overridden before BandScene.__init__ creates any generic drummer.
        pass

    def light_curve(self,name,points,index=0,radius=.024,closed=False):
        self.curve(name,points,PALETTE[index%len(PALETTE)],radius,closed,64+index%48)

    def jewel(self,name,center,scale,index):
        mesh=trimesh.creation.icosphere(subdivisions=0)
        mesh.apply_scale(scale)
        self.mesh(name,mesh,PALETTE[index%6],center,64+index%48)
        v=mesh.vertices+np.array(center)
        for edge in mesh.edges_unique:
            self.light_curve(name+'_edge',v[edge],index+1,.013)

    def floor_rosette(self):
        t=np.linspace(0,math.tau,180,endpoint=False)
        for j in range(8):
            r=3.8+j*.64
            self.light_curve('cymatic_floor_ring',np.c_[r*np.cos(t),np.full(len(t),.018),r*.58*np.sin(t)],j,.014,True)
        for j in range(24):
            theta=j*math.tau/24
            r=np.linspace(4.2,8.6,70);a=theta+.20*np.sin(r*1.6)
            self.light_curve('floor_radial_wave',np.c_[r*np.cos(a),np.full(len(r),.022),r*.58*np.sin(a)],j,.011)
        for x in (-8.1,8.1):
            self.box('architectural_pylon',(x,1.5,-3.8),(.44,3.,.6),'#28324B')
            for k in range(7):
                self.light_curve('pylon_flute',[(x+(k-3)*.055,.18,-3.45),(x+(k-3)*.055,3.,-3.45)],k,.011)

    def knot_cathedral(self):
        t=np.linspace(0,math.tau,420,endpoint=False)
        for j in range(12):
            a=t+j*math.tau/12
            r=2.62+.62*np.cos(3*a)
            p=np.c_[r*np.cos(2*a),4.8+r*np.sin(2*a),-5.0+.70*np.sin(3*a)]
            # Parallel offsets form a real braided surface rather than one loop.
            p[:,0]*=1+j*.010;p[:,1]+=j*.018
            self.light_curve('trefoil_braid',p,j,.022,True)
        # A sculpted central knot gives the light braid a readable solid form.
        r=2.65+.62*np.cos(3*t)
        self.light_curve('sculpted_trefoil',np.c_[r*np.cos(2*t),4.8+r*np.sin(2*t),-5.0+.70*np.sin(3*t)],0,.090,True)
        for side in (-1,1):
            for j in range(18):
                h=np.linspace(.1,6.7,180);a=h*2.1+j*math.tau/18
                r=.48+.16*np.sin(h*1.1)
                self.light_curve('woven_knot_spire',np.c_[side*6.8+r*np.cos(a),h,-4.4+r*np.sin(a)],j,.020)
            self.jewel('cathedral_crown',(side*6.8,7.0,-4.4),(.5,.65,.5),2)
        for j in range(9):
            a=np.linspace(0,math.pi,170)
            self.light_curve('cathedral_vault',np.c_[(8.7-j*.15)*np.cos(a),.3+(8.0-j*.22)*np.sin(a),np.full(len(a),-5.9+j*.16)],j,.018)

    def prismatic_orrery(self):
        t=np.linspace(0,math.tau,220,endpoint=False)
        for j in range(10):
            tilt=j*math.pi/10
            p=np.c_[3.1*np.cos(t),3.1*np.sin(t)*np.cos(tilt),3.1*np.sin(t)*np.sin(tilt)]
            p+=(0,4.9,-5.5)
            self.light_curve('armillary_orbit',p,j,.025,True)
            for theta in np.linspace(0,math.tau,12,endpoint=False):
                q=np.array((3.1*np.cos(theta),3.1*np.sin(theta)*np.cos(tilt),3.1*np.sin(theta)*np.sin(tilt)))+(0,4.9,-5.5)
                self.sphere('orbital_lantern',q,(.045,.045,.045),PALETTE[j%6],64+j)
        self.jewel('orrery_core',(0,4.9,-5.5),(.85,1.1,.85),3)
        for side in (-1,1):
            for j in range(8):
                y=.5+j*.72;x=side*(5.7+.5*np.sin(j*.8))
                self.jewel('suspended_prism',(x,y,-4.0),(.55,.72,.42),j)
                self.light_curve('prism_suspension',[(x,y+.6,-4),(x,7.2,-4)],j,.010)
            for j in range(5):
                a=np.linspace(0,math.pi,110)
                self.light_curve('orrery_side_fan',np.c_[side*6.0+(1.6+j*.12)*np.cos(a),.2+(5.5+j*.32)*np.sin(a),np.full(len(a),-5.1+j*.15)],j,.018)

    def woven_aurora(self):
        u=np.linspace(-8.3,8.3,180)
        for j,v in enumerate(np.linspace(-2.1,2.1,28)):
            y=5.75+.022*u*u-.17*v*v+.40*np.sin(u*.72+v)
            self.light_curve('aurora_warp',np.c_[u,y,-5.4+v+.35*np.sin(u*.43)],j,.019)
        v=np.linspace(-2.1,2.1,90)
        for j,u in enumerate(np.linspace(-8.3,8.3,48)):
            y=5.75+.022*u*u-.17*v*v+.40*np.sin(u*.72+v)
            self.light_curve('aurora_weft',np.c_[np.full(len(v),u),y,-5.4+v+.35*np.sin(u*.43)],j,.016)
        for side in (-1,1):
            for j in range(15):
                h=np.linspace(.1,6.7,160);a=h*1.4+j*math.tau/15
                self.light_curve('aurora_braided_pier',np.c_[side*7.4+.66*np.cos(a),h,-3.8+.66*np.sin(a)],j,.019)
            for j in range(9):
                a=np.linspace(0,math.pi,100)
                self.light_curve('saddle_side_ribbon',np.c_[side*(5.1+j*.29)+.40*np.sin(a*4+j),.3+4.8*np.sin(a),-4.2+.65*np.cos(a)],j,.024)

    def cymatic_geode(self):
        t=np.linspace(0,math.tau,240,endpoint=False)
        for j in range(18):
            r=1.12+j*.14+.22*np.sin(t*8+j*.27)
            self.light_curve('geode_resonance',np.c_[r*np.cos(t),4.6+r*np.sin(t),-5.2+.14*np.cos(t*8+j*.5)],j,.019,True)
        for j in range(16):
            a=j*math.tau/16;q=(4.0*np.cos(a),4.6+3.5*np.sin(a),-5.4)
            self.jewel('geode_prism',q,(.26,.42,.30),j)
        for side in (-1,1):
            for j in range(12):
                x=side*(4.9+(j%4)*.72);y=.4+(j//4)*1.4;z=-3.8-(j%3)*.45
                self.jewel('crystal_garden',(x,y,z),(.35,.9+j*.035,.35),j)
            for j in range(7):
                t=np.linspace(0,math.tau,120,endpoint=False)
                self.light_curve('cymatic_side_shell',np.c_[side*6.5+(1.1+j*.12)*np.cos(t),3.0+(2.1+j*.13)*np.sin(t),np.full(len(t),-5.4+j*.15)],j,.018,True)

    def infinity_observatory(self):
        t=np.linspace(0,math.tau,220,endpoint=False)
        for side in (-1,1):
            for j in range(12):
                r=2.15+j*.025
                p=np.c_[side*2.7+r*np.cos(t),4.8+r*np.sin(t),-5.4+.85*np.sin(t+j*.10)]
                self.light_curve('linked_observatory_rings',p,j,.020,True)
            for j in range(12):
                h=np.linspace(.1,6.9,180);a=h*2+j*math.tau/12
                self.light_curve('dna_observatory_tower',np.c_[side*7.3+.55*np.cos(a),h,-4.3+.55*np.sin(a)],j,.018)
            for h in np.linspace(.3,6.8,24):
                a=h*2
                self.light_curve('dna_rung',[(side*7.3+.55*np.cos(a),h,-4.3+.55*np.sin(a)),(side*7.3-.55*np.cos(a),h,-4.3-.55*np.sin(a))],int(h*4),.016)
        for j in range(8):
            a=np.linspace(0,math.pi,180)
            self.light_curve('infinity_outer_halo',np.c_[(8.3-j*.14)*np.cos(a),.3+(7.8-j*.17)*np.sin(a),-6.1+.24*np.sin(a*3+j*.3)],j,.019)
        self.jewel('infinity_nucleus',(0,5.0,-5),(.50,.75,.50),3)

    def quasicrystal_theatre(self):
        # Fivefold layered rhombi/petals with explicit faceted colored surfaces.
        for ring in range(4):
            for j in range(20):
                theta=j*math.tau/20+(ring%2)*math.pi/20;r=1.3+ring*.66
                c=np.array((r*np.cos(theta),4.9+r*np.sin(theta),-5.1-ring*.14))
                radial=np.array((np.cos(theta),np.sin(theta),0));tangent=np.array((-np.sin(theta),np.cos(theta),0))
                vertices=np.array([c+radial*.55,c+tangent*.21,c-radial*.55,c-tangent*.21,c+(0,0,.18)])
                mesh=trimesh.Trimesh(vertices=vertices,faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],process=False)
                self.mesh('quasicrystal_facet',mesh,PALETTE[(j+ring)%6],slot=64+(j+ring*7)%48)
                self.light_curve('quasicrystal_facet_edge',vertices[[0,1,2,3]],j+ring,.012,True)
        for side in (-1,1):
            for j in range(12):
                h=np.linspace(.15,6.7,150);a=h*1.5+j*math.tau/12
                r=.58+.13*np.cos(h*3)
                self.light_curve('quasicrystal_twisted_column',np.c_[side*6.9+r*np.cos(a),h,-4.4+r*np.sin(a)],j,.022)
            for j in range(7):
                y=.6+j*.82
                self.jewel('origami_side_crown',(side*5.5,y,-4.9),(.42,.42,.42),j)
        for j in range(10):
            a=np.linspace(0,math.pi,160)
            self.light_curve('quasicrystal_proscenium',np.c_[(8.7-j*.20)*np.cos(a),.2+(7.8-j*.17)*np.sin(a),np.full(len(a),-6.3+j*.15)],j,.019)

    def validate(self):
        for item in self.instances:
            assert np.isfinite(item['matrix']).all()
            assert abs(np.linalg.det(item['matrix'][:3,:3]))>1e-10
        triangles=0
        for item in self.custom:
            m=item['mesh'];assert np.isfinite(m.vertices).all() and np.isfinite(m.vertex_normals).all()
            triangles+=len(m.faces)
        return dict(layout=self.layout,title=LAYOUTS[self.layout],curves_and_meshes=len(self.custom),
                    instanced_parts=len(self.instances),custom_triangles=triangles,
                    finite_geometry=True,canonical_dry_drummer=True,
                    band_members=['drummer','bass','guitar','male singer','female singer','keyboard'])
