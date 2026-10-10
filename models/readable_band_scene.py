"""Performance-visible string surfaces, without changing historical scene assets."""
from __future__ import annotations
import numpy as np
from models.intricate_band_scene import IntricateBandScene
from models.band_performance_scene import line_matrix, rgb


class ReadableBandScene(IntricateBandScene):
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
            elif o['name']=='guitar_fret':
                o['matrix'][:3,2]*=1.9
                o['matrix'][2,3]=.535
        # Head and torso move; the planted upright instrument keeps its bridge,
        # strings and contact positions coherent.
        self.groove=[]
        excluded={n for rig in self.rigs for n in rig['ids']}
        for idx,o in enumerate(self.instances):
            role=o['name'].split('_')[0]
            if role in ('bass','guitar','piano') and idx not in excluded and 'mouth_role' not in o and not any(
                s in o['name'] for s in ('string','fingerboard','scroll','bridge','endpin','key_','fret','neck','headstock')):
                if o['kind']=='sphere' or any(s in o['name'] for s in ('hat','scarf')):
                    self.groove.append((idx,role,o['matrix'].copy()))
        self.key_rest={i:o['matrix'].copy() for i,o in enumerate(self.instances) if o['name'].startswith('piano_key_')}
        self.technical_proof=self.validate()

    def vibrate(self,kind,string,level,source_time):
        s=self.strings[kind][string];u=np.linspace(0,1,17)
        # Slow visible wave depicts the resonance envelope, not acoustic Hz.
        displacement=.040*level*np.sin(np.pi*u)*np.sin(u*4*np.pi-source_time*18-string)
        pts=s['a'][None,:]+u[:,None]*(s['b']-s['a'])[None,:]
        pts[:,2]+=displacement
        for idx,a,b in zip(s['ids'],pts[:-1],pts[1:]):
            self.instances[idx]['matrix']=line_matrix(a,b,s['radius']*(1+.35*level))
