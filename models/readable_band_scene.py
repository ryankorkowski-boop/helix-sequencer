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
                # Recover authored endpoint XY instead of widening the guitar
                # strings. Inherited stage transforms and the widened neck
                # require a new front plane; raw old Z would bury the strings.
                # The still-visible original rods also made a duplicate set.
                transform=original['matrix']
                a=transform[:3,3]-.5*transform[:3,2]
                b=transform[:3,3]+.5*transform[:3,2]
                if kind=='bass':
                    # Use the central half of the actual .34-wide bridge.
                    # Four thin strings remain independently readable and fit
                    # inside the .25-wide fingerboard at both attachments.
                    bridge=next(o for o in self.instances if o['name']=='bass_bridge')['matrix']
                    spacing=abs(float(bridge[0,0]))*.5/3
                    a[0]=b[0]=bridge[0,3]+(j-1.5)*spacing
                    a[2]=b[2]=max(a[2],b[2],bridge[2,3]+abs(bridge[2,2])*.5)+.006
                else:
                    neck=next(o for o in self.instances if o['name']=='guitar_neck')['matrix']
                    # .095 is the authored readable-neck radius installed
                    # below. Keep the maximum historical .040 safety margin.
                    plane=max(a[2],b[2],neck[2,3]+.095+.050)
                    a[2]=b[2]=plane
                    for item in self.instances:
                        if item['name'] in ('bridge','pickup'):
                            item['matrix'][2,3]=plane-abs(item['matrix'][2,2])*.5
                original['kind']='hidden'
                radius=.0045 if kind=='bass' else .0032
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
            center=self.guitar_contact(2,fret);center[2]-=.008
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
        displacement=.006*level*np.sin(np.pi*u)*np.sin(u*4*np.pi-source_time*18-string)
        pts=s['a'][None,:]+u[:,None]*(s['b']-s['a'])[None,:]
        pts[:,2]+=displacement
        for idx,a,b in zip(s['ids'],pts[:-1],pts[1:]):
            self.instances[idx]['matrix']=line_matrix(a,b,s['radius'])
