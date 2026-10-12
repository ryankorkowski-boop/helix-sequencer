"""Connected musical gestures on retained source events, with isolated mallet provenance."""
import json
import numpy as np
from music.note_events import NoteEvent
from models.band_instrument_logic import event_curves
from models.band_motion_refinement import signed_gestures,transition_targets,mallet_events,smoothstep,elbow_3d
from tools.readable_band_performance import ReadablePerformance
from models.band_performance_scene import line_matrix,matrix

class RefinedPerformance(ReadablePerformance):
    def __init__(self,row,scene,analysis_root):
        super().__init__(row,scene,analysis_root)
        from pathlib import Path
        events=json.loads((Path(analysis_root)/row['id']/'note_events.json').read_text())
        self.events={kind:[NoteEvent(**e) for e in values] for kind,values in events.items()}
        mallets,omitted=mallet_events(self.events['piano'])
        # The old merged CQT lane could assign another 'other' instrument's
        # notes to a mallet gate. Use the gate's own measured spectral peak.
        from tools.readable_band_performance import ROOT
        local_proof=Path(analysis_root)/row['id']/'verification.json'
        proof=json.loads(local_proof.read_text())
        if 'mallet_attacks' not in proof:
            proof=json.loads((ROOT/'outputs/Intricate_Band_Samplers/analysis'/row['id']/'verification.json').read_text())
        if row.get('sha256') and proof.get('source_sha256')!=row['sha256']:
            raise ValueError('mallet evidence does not belong to this source song')
        candidates=proof.get('mallet_attacks',[])
        mallets=[];omitted=[];self.mallet_evidence=[]
        for candidate in candidates:
            if candidate['concentration']<.20 or candidate['decay_ratio']<1.35 or candidate['vocal_similarity']>.65:continue
            time=candidate['start_ms']/1000;pitch=candidate['midi']
            index=min(self.n-1,round(time*20))
            velocity=float(self.curves.get('keyboard_mallet_energy',self.curves['piano_energy'])[index])
            if velocity<=.08:continue
            e=NoteEvent(time,time+.10,pitch,min(1,velocity),source='other_stem_screened_mallet_estimate')
            (mallets if 60<=pitch<=84 else omitted).append(e)
            self.mallet_evidence.append(candidate)
        self.mallet_notes,self.mallet_levels,self.mallet_attacks,_=event_curves(mallets,self.n,2,release=.12)
        self.mallet_proof=dict(provenance='screened pitched-percussion estimates; instrument identity unverified',
            accepted=len(mallets),spectral_peak_is_not_verified_fundamental=True,
            rejected_weak_or_vocal_candidates=len(candidates)-len(self.mallet_evidence),out_of_range_omissions=len(omitted),piano_events_excluded=True,octave_folding=False)
        # Remove mallet estimates from the piano performer, retaining piano notes.
        piano=[e for e in self.events['piano'] if e.source=='piano_stem_harmonic_estimate']
        note,vel,attack,phase=event_curves(piano,self.n,6,.16)
        for key,val in [('notes',note),('note_levels',vel),('attack',attack),('phase',phase),('energy',vel.max(axis=1))]:self.curves['piano_'+key]=val
        self.directions={kind:signed_gestures(self.curves[kind+'_attack']) for kind in ('bass','guitar')}
        self.guitar_contacts=[];previous=None
        for i,routes in enumerate(self.curves['guitar_routes']):
            valid=[tuple(map(int,r)) for r in routes if r[0]>=0]
            if not valid:self.guitar_contacts.append(None);continue
            from models.band_instrument_logic import playable_pitch
            def strength(route):
                return max((float(v) for n,v in zip(self.curves['guitar_notes'][i],self.curves['guitar_note_levels'][i])
                    if n>=0 and playable_pitch(int(n),'guitar')==route[2]),default=0)
            selected=previous if previous in valid and not self.curves['guitar_attack'][i] else max(valid,key=strength)
            self.guitar_contacts.append(selected);previous=selected
        self.fret_targets={}
        for kind in ('bass','guitar'):
            rig=next(r for r in scene.rigs if r['role']==kind and r['side']=='finger')
            position=rig['hand'].copy();positions=[]
            for i in range(self.n):
                routes=[tuple(map(int,r)) for r in self.curves[kind+'_routes'][i] if r[0]>=0]
                route=routes[0] if kind=='bass' and routes else self.guitar_contacts[i] if kind=='guitar' else None
                if route is not None:
                    contact=scene.bass_contact if kind=='bass' else scene.guitar_contact
                    position=contact(route[0],route[1])+(0,0,.065)
                positions.append(position.copy())
            self.fret_targets[kind]=transition_targets(positions,.10)
        # Schedule a separate mallet attack per selected pitch, up to two hands.
        # More than two simultaneous notes are explicitly unplayable for this rig.
        self.mallet_schedule=[];last_side='right';self.unplayable_mallet_chords=0
        by_time={}
        for e in mallets:by_time.setdefault(e.start,[]).append(e)
        for time,group in sorted(by_time.items()):
            group=sorted({e.pitch:e for e in sorted(group,key=lambda e:e.velocity)}.values(),key=lambda e:e.pitch)
            if len(group)>2:self.unplayable_mallet_chords+=len(group)-2;group=group[:2]
            if len(group)==2:sides=['left','right']
            else:
                pitch=group[0].pitch
                last_side='left' if pitch<68 else 'right' if pitch>76 else ('left' if last_side=='right' else 'right')
                sides=[last_side]
            for side,e in zip(sides,group):
                # Contacts must exist on a rendered frame. Keep the acoustic
                # timestamp and bounded display error independently auditable.
                self.mallet_schedule.append(dict(time=round(time*20)/20,source_time=time,
                    display_error_ms=(round(time*20)/20-time)*1000,side=side,pitch=e.pitch,velocity=e.velocity))
        self.mallet_targets={};self.contact_audit=[];self.joint_targets={}

    def levels(self,i):
        levels=np.pad(super().levels(i),(0,64))
        # Only actual attack envelopes brighten bars; sustained piano never does.
        time=i/20
        for hit in self.mallet_schedule:
            age=time-hit['time']
            if 0<=age<.30:levels[128+hit['pitch']-60]=max(levels[128+hit['pitch']-60],hit['velocity']*np.exp(-age/.105))
        return levels

    def pose(self,i):
        levels=super().pose(i);time=i/20
        for rig in self.scene.rigs:
            kind,side=rig['role'],rig['side']
            if kind not in ('bass','guitar'):continue
            hand=self.hand_targets[kind,side].copy()
            if side=='finger':
                hand=self.fret_targets[kind][i].copy()
                if kind=='guitar':self.guitar_contact_route=self.guitar_contacts[i]
            elif side in ('pluck','strum'):
                stroke=float(self.directions[kind][i])
                # Connected artistic alternating articulation; no claim of
                # recovering real finger identity or upstroke from mixed audio.
                if kind=='bass':hand[1]=1.03+.20*stroke;hand[2]=.485+.13*abs(stroke)
                else:
                    chord=len(self.active_routes.get(kind,[]))>=2
                    amplitude=.32 if chord else .12
                    hand=np.array((3.87-.18*stroke,1.02+amplitude*stroke,.65))
            old=self.scene.instances[rig['ids'][0]]['matrix']
            shoulder=old[:3,3]-old[:3,2]*.5
            elbow=elbow_3d(shoulder,hand,*rig['link_lengths'],
                (-.8 if side in ('pluck','strum') else .8,-.2,.8))
            a,b,c=rig['ids'];self.scene.instances[a]['matrix']=line_matrix(shoulder,elbow,.046)
            self.scene.instances[b]['matrix']=line_matrix(elbow,hand,.046)
            self.scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08));self.hand_targets[kind,side]=hand
            self.joint_targets[kind,side]=(shoulder.copy(),elbow.copy(),hand.copy())
        for rig in self.scene.rigs:
            if rig['role']!='xylophone':continue
            side=rig['side'];hand=rig['hand'].copy();tip=hand+(0,0,.30)
            lane=[e for e in self.mallet_schedule if e['side']==side]
            previous=next((e for e in reversed(lane) if e['time']<=time),None)
            following=next((e for e in lane if e['time']>time),None)
            def contact(e):return self.scene.bars[e['pitch']]+(0,.0275+.057,0)
            if previous and following and following['time']-previous['time']<=.55:
                phase=(time-previous['time'])/(following['time']-previous['time'])
                weight=smoothstep(phase);tip=contact(previous)*(1-weight)+contact(following)*weight
                tip[1]+=.16*np.sin(np.pi*phase)
                tip[2]+=(.035 if side=='left' else -.035)*np.sin(np.pi*phase)
            elif following and 0<following['time']-time<.15:
                tip=tip*(1-smoothstep(1-(following['time']-time)/.15))+contact(following)*smoothstep(1-(following['time']-time)/.15)
            elif previous and time-previous['time']<.22:
                weight=smoothstep((time-previous['time'])/.22)
                tip=contact(previous)*(1-weight)+tip*weight
                tip[1]+=.12*np.sin(np.pi*weight)
            hand=tip+(0,.2598076211,-.15)
            if previous and abs(time-previous['time'])<1e-7:
                self.contact_audit.append(dict(frame=i,side=side,pitch=previous['pitch'],tip=tip.tolist()))
            shoulder=rig['shoulder'];elbow=elbow_3d(shoulder,hand,*rig['link_lengths'],
                (-.8 if side=='left' else .8,-.2,.8))
            a,b,c=rig['ids'];self.scene.instances[a]['matrix']=line_matrix(shoulder,elbow,.046)
            self.scene.instances[b]['matrix']=line_matrix(elbow,hand,.046);self.scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
            rod,head=rig['mallet_ids'];self.scene.instances[rod]['matrix']=line_matrix(hand,tip,.017)
            self.scene.instances[head]['matrix']=matrix(tip,(.057,.057,.057));self.mallet_targets[side]=(hand,tip)
            self.joint_targets['xylophone',side]=(shoulder.copy(),elbow.copy(),hand.copy())
        return levels
