"""Canonical note/velocity events drive physical routes and attack gestures."""
from __future__ import annotations
import bisect,json,math
from pathlib import Path
import numpy as np
from PIL import ImageDraw
from models.band_performance_scene import matrix,line_matrix
from models.band_sampler_logic import SHAPE_NAMES
from tools.render_intricate_band_samplers import SamplerPerformance,SAMPLER_FRAGMENT
from tools.render_band_upgrade import native_drummer
from tools.build_helpers.ultimate_showcase_preview import _font

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/Band_Instrument_Review'
STRING_FRAGMENT=SAMPLER_FRAGMENT.replace('} else { c+=color*(energy*0.70+rim*0.17); }', '''
 } else if(channel>=13.0 && channel<23.0){
   float shimmer=.5+.5*sin(world.y*15.0-song_time*18.0+channel*1.9);
   c=color*(.055+energy*(.65+1.1*shimmer));
 } else if(channel>=23.0 && channel<60.0){
   c=mix(c,vec3(.30,.95,.85),energy*.72)+vec3(.20,.65,.50)*energy;
 } else { c+=color*(energy*0.70+rim*0.17); }
''')


def key_pitch(note):
    while note<48:note+=12
    while note>84:note-=12
    return int(note)


class ReadablePerformance(SamplerPerformance):
    def __init__(self,row,scene):
        self.row=row;self.variant='band';self.scene=scene
        path=OUT/'analysis'/row['id']
        with np.load(path/'performance_curves.npz') as a:self.curves={k:a[k].copy() for k in a.files}
        self.vocals=json.loads((path/'vocals.json').read_text())
        self.drums,self.strikes,self.hands,self.drum_proof=native_drummer(row)
        self.n=len(self.drums);self.mouths=np.array([SHAPE_NAMES[int(x)] for x in self.curves['mouth_lanes'][:,0]])
        self.lyric_starts=[e['start_ms'] for e in self.vocals['lines']];self.note_routes={}
        self.key_centers={int(o['name'].removeprefix('piano_key_')):o['matrix'][:3,3].copy() for o in scene.instances if o['name'].startswith('piano_key_')}
        self.active_routes={};self.key_levels={};self.hand_targets={}

    def levels(self,i):
        out=np.zeros(128,np.float32);out[5:13]=self.drums[i]
        for k,kind in enumerate(('bass','guitar','piano')):out[k]=self.curves[kind+'_energy'][i]*.5
        for kind,first in [('bass',13),('guitar',17)]:
            routes=[tuple(map(int,r)) for r in self.curves[kind+'_routes'][i] if r[0]>=0]
            self.active_routes[kind]=routes;self.note_routes[kind]=[(r[0],r[1]) for r in routes]
            from models.band_instrument_logic import playable_pitch
            for string,fret,pitch in routes:
                velocity=max((float(v) for n,v in zip(self.curves[kind+'_notes'][i],self.curves[kind+'_note_levels'][i]) if n>=0 and playable_pitch(int(n),kind)==pitch),default=0)
                out[first+string]=velocity
        self.key_levels={}
        for n,v in zip(self.curves['piano_notes'][i],self.curves['piano_note_levels'][i]):
            if n<0 or v<=0:continue
            pitch=key_pitch(int(n));self.key_levels[pitch]=max(self.key_levels.get(pitch,0),float(v))
        for pitch,v in self.key_levels.items():out[23+pitch-48]=v
        return out

    def pose(self,i):
        levels=super().pose(i);t=i/20
        for idx,role,rest in self.scene.groove:
            phase=float(self.curves[role+'_phase'][i]);gain=float(self.curves[role+'_energy'][i])
            m=rest.copy();m[0,3]+=.075*gain*math.sin(t*3.7)
            m[1,3]+=.048*gain*math.exp(-phase*4)
            self.scene.instances[idx]['matrix']=m
        self.hand_targets={}
        for rig in self.scene.rigs:
            kind,side=rig['role'],rig['side']
            if kind not in ('bass','guitar','piano'):continue
            hand=rig['hand'].copy();phase=float(self.curves[kind+'_phase'][i]);energy=float(self.curves[kind+'_energy'][i])
            # Maximum displacement at onset; return to ready within200ms.
            stroke=energy*(1-phase)**2
            routes=self.active_routes.get(kind,[])
            if kind=='bass' and routes:
                s=self.scene.strings[kind][routes[0][0]]
                hand[0]=s['a'][0]
                hand[2]=s['a'][2]+.065
                if side=='finger':hand[1]=float(self.curves['bass_height'][i])
                else:hand[1]=1.03+.16*stroke;hand[2]+=.12*stroke
            elif kind=='guitar' and routes:
                s=self.scene.strings[kind][routes[0][0]]
                if side=='finger':
                    fret=float(np.median([r[1] for r in routes]));u=.96-.50*min(fret,24)/24
                    hand=s['a']+(s['b']-s['a'])*u;hand[2]+=.065
                else:
                    hand=np.array((3.87,1.02,.65));hand[1]+=.27*stroke;hand[0]-=.16*stroke
            elif kind=='piano' and self.key_levels:
                notes=sorted(self.key_levels);spread=notes[-1]-notes[0]>=3
                which='left' if notes[0]<66 else 'right'
                if spread or side==which:
                    pitch=notes[0] if side=='left' else notes[-1]
                    hand=self.key_centers[pitch]+(0,.11-.045*stroke,.08)
            elbow=(rig['shoulder']+hand)/2+(-.12 if side in ('left','pluck','strum') else .12,.04,.12)
            a,b,c=rig['ids'];self.scene.instances[a]['matrix']=line_matrix(rig['shoulder'],elbow,.046)
            self.scene.instances[b]['matrix']=line_matrix(elbow,hand,.046)
            self.scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
            self.hand_targets[kind,side]=hand.copy()
        for kind,first in [('bass',13),('guitar',17)]:
            for j in range(len(self.scene.strings[kind])):self.scene.vibrate(kind,j,float(levels[first+j]),t)
        for idx,rest in self.scene.key_rest.items():
            o=self.scene.instances[idx];m=rest.copy();m[1,3]-=.020*levels[o['slot']];o['matrix']=m
        return levels

    def caption(self,frame,i,focus='stage'):
        # Retain screened lyrics and duet cues without historical-geometry label.
        frame=super().caption(frame,i);d=ImageDraw.Draw(frame);w,h=frame.size
        d.rectangle((20,h-43,w-20,h),fill='#071221')
        d.text((32,h-28),'SOURCE-TIMED STRINGS + KEYS  •  Revised drummer shoulders  •  '+focus.upper(),font=_font(13),fill='#AED8DD')
        return frame
