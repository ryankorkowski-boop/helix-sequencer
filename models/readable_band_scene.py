"""Performance-visible string surfaces, without changing historical scene assets."""
from __future__ import annotations
import numpy as np
from models.intricate_band_scene import IntricateBandScene
from models.band_performance_scene import line_matrix, rgb


class ReadableBandScene(IntricateBandScene):
    def snowman(self,role,p,accent,female=False):
        first=len(self.instances)
        center=super().snowman(role,p,accent,female)
        for o in self.instances[first:]:
            o['performer_role']=role
            # Generic decorations also need the piano's stage relocation.
            if not o['name'].startswith(role+'_'):o['name']=role+'_'+o['name']
        return center

    def mouth(self,name,center,role,color='#180D1B'):
        super().mouth(name,center,role,color)
        self.instances[-1]['performer_role']=role

    def __init__(self,layout):
        super().__init__(layout)
        self.strings={'bass':[],'guitar':[]}
        # Quiet original straight lines are replaced by independently deforming
        # segments. Endpoints stay fixed at the bridge and nut.
        for kind,count,first in [('bass',4,13),('guitar',6,17)]:
            for j in range(count):
                original=next(o for o in self.instances if o['name']==f'{kind}_string_{j}')
                original['color']=rgb('#131B24');original['slot']=-1
                if kind=='bass':
                    x=-4+.58+(j-1.5)*.057
                    a=np.array((x,.42,.415));b=np.array((x,3.18,.415));radius=.015
                else:
                    off=np.array((-(j-2.5)*.025,(j-2.5)*.025,0))
                    a=np.array((3.60,.83,.59))+off;b=np.array((5.22,2.32,.59))+off;radius=.010
                segments=[]
                for k in range(16):
                    lo=a+(b-a)*k/16;hi=a+(b-a)*(k+1)/16
                    segments.append(len(self.instances))
                    self.rod(f'{kind}_live_string_{j}_{k}',lo,hi,radius,'#FFF0B0' if kind=='bass' else '#88EEFF',first+j)
                self.strings[kind].append(dict(a=a,b=b,ids=segments,radius=radius))
        board=next(o for o in self.instances if o['name']=='bass_fingerboard')
        board['matrix'][0,0]=.25
        for o in self.instances:
            if o['name']=='guitar_neck':o['matrix'][:3,:2]*=.095/.058
            elif o['name']=='guitar_headstock':o['matrix'][:3,:2]*=.115/.086
        # Nut-to-bridge semitone spacing, shared by visible frets and fingertips.
        existing_frets=[o for o in self.instances if o['name']=='guitar_fret']
        for fret in range(1,25):
            center=self.guitar_contact(2,fret);center[2]=.535
            a=center+(-.10,.10,0);b=center+(.10,-.10,0)
            if fret<=len(existing_frets):existing_frets[fret-1]['matrix']=line_matrix(a,b,.008)
            else:self.rod('guitar_fret',a,b,.008,'#A9BED0')
        # Head and torso move; the planted upright instrument keeps its bridge,
        # strings and contact positions coherent.
        self.groove=[]
        for idx,o in enumerate(self.instances):
            role=o.get('performer_role')
            if role in ('bass','guitar','piano'):
                self.groove.append((idx,role,o['matrix'].copy()))
        self.key_rest={i:o['matrix'].copy() for i,o in enumerate(self.instances) if o['name'].startswith('piano_key_')}
        self.technical_proof=self.validate()

    def guitar_contact(self,string,fret):
        s=self.strings['guitar'][string]
        return s['a']+(s['b']-s['a'])*2**(-fret/12)

    def vibrate(self,kind,string,level,source_time):
        s=self.strings[kind][string];u=np.linspace(0,1,17)
        # Slow visible wave depicts the resonance envelope, not acoustic Hz.
        displacement=.040*level*np.sin(np.pi*u)*np.sin(u*4*np.pi-source_time*18-string)
        pts=s['a'][None,:]+u[:,None]*(s['b']-s['a'])[None,:]
        pts[:,2]+=displacement
        for idx,a,b in zip(s['ids'],pts[:-1],pts[1:]):
            self.instances[idx]['matrix']=line_matrix(a,b,s['radius']*(1+.35*level))
