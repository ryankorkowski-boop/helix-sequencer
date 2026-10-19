"""Focused musical-response version of the preserved approved band rig."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from music.note_events import NoteEvent
from models.band_motion_refinement import transition_targets,elbow_3d,signed_gestures,constrained_keyboard_wrist_lane
from models.musical_band_response import ringing_candidates,cast_source_voice
from models.band_instrument_logic import event_curves
from models.band_performance_scene import line_matrix,matrix
from tools.refined_band_performance import RefinedPerformance
from tools.readable_band_performance import key_pitch,ROOT
from tools.render_band_upgrade import SHAPES
from models.band_sampler_logic import SHAPE_NAMES


class MusicalBandPerformance(RefinedPerformance):
    def __init__(self,row,scene,analysis_root,casting=None,*,separate_pitched=False):
        super().__init__(row,scene,analysis_root)
        local_proof=Path(analysis_root)/row['id']/'verification.json'
        proof=json.loads(local_proof.read_text()) if local_proof.is_file() else json.loads((ROOT/'outputs/Intricate_Band_Samplers/analysis'/row['id']/'verification.json').read_text())
        if proof['source_sha256']!=row['sha256']:raise ValueError('mallet source hash mismatch')
        accepted,rejected=ringing_candidates(proof['mallet_attacks'],min(scene.bars),max(scene.bars))
        self.mallet_schedule=[];previous_side='right';self.mallet_evidence=accepted
        for c in accepted:
            time=c['start_ms']/1000;pitch=c['midi'];index=min(self.n-1,round(time*20))
            velocity=float(self.curves['keyboard_mallet_energy'][index])
            if velocity<=.08:continue
            previous_side='left' if pitch<65 else 'right' if pitch>79 else ('left' if previous_side=='right' else 'right')
            display=round(time*20)/20
            self.mallet_schedule.append(dict(time=display,source_time=time,display_error_ms=(display-time)*1000,
                side=previous_side,pitch=pitch,velocity=min(1,velocity)))
        self.mallet_proof=dict(accepted=len(self.mallet_schedule),previous_strict_count=self.mallet_proof['accepted'],
            rejected=len(rejected),register=[min(scene.bars),max(scene.bars)],octave_folding=False,
            provenance='retained source-bound ringing attacks; bells/marimba/xylophone-like candidates',
            instrument_identity_verified=False,piano_events_excluded=True)
        self.directions['bass']=signed_gestures(self.curves['bass_attack'],duration=.13)
        # No changes to guitar events, routes, articulation or contacts.
        self.key_hand_targets={};self.key_assignments={}
        from music.magic_keyboard import magic_keyboard_events
        ev=magic_keyboard_events(self.events['piano'], () if separate_pitched else self.mallet_schedule, duration=self.n/20)
        self._install_keyboard_events(ev)
        casting=casting or dict(lead='male',source='stable lead fallback; no verified voice classification')
        self.casting=casting
        self.curves['mouth_lanes']=cast_source_voice(self.curves['mouth_lanes'].max(axis=1),
            self.curves['vocal_energy'],casting['lead'],casting.get('overrides',()))
        self.voice_lanes=self.curves['mouth_lanes'].copy()
        # Frame energy controls articulation, without a slow release past silence.
        self.voice_energy=np.column_stack([self.curves['vocal_energy']*(self.voice_lanes[:,k]!=0) for k in (0,1)])

    def _install_keyboard_events(self,ev):
        """Install selected evidence-based keyboard notes in BOTH key lights
        and hand targets; source and preview must never use different lanes.
        Hard reach/speed constraints remain in force for any active lane.
        """
        # Unknown confidence is retained as uncertainty, never upgraded to truth.
        self.keyboard_rejected_events=[dict(event=e.to_dict(),reason='low_confidence')
            for e in ev if e.confidence is not None and e.confidence<.55]
        ev=[e for e in ev if e.confidence is None or e.confidence>=.55]
        self.keyboard_events=ev
        held,velocity,attack,phase=event_curves(ev,self.n,6,release=0)
        # Keys and hands share the exact held-note lane, without the inherited
        # visual release tail retaining a depressed key after its hand leaves.
        for key,value in [('notes',held),('note_levels',velocity),('attack',attack),
                          ('phase',phase),('energy',velocity.max(axis=1))]:
            self.curves['piano_'+key]=value
        from models.keyboard_motion_plan import plan_keyboard_hands
        rigs={r['side']:r for r in self.scene.rigs if r['role']=='piano'}
        # Preserve original MIDI identity: out-of-register notes may illuminate
        # the legacy folded display, but cannot be claimed as physical contacts.
        slower = (getattr(self.scene, 'legacy_mallet_player', True) is False)
        motion_limits = dict(max_step=.030, max_acceleration=.010) if slower else {}
        self.key_hand_targets,self.key_assignments,self.keyboard_motion_report=plan_keyboard_hands(
            held,velocity,self.key_centers,rigs, **motion_limits)
        self.keyboard_motion_report['detected_events']=len(ev)+len(self.keyboard_rejected_events)
        self.keyboard_motion_report['accepted_events']=len(ev)
        self.keyboard_motion_report['rejected_events']=self.keyboard_rejected_events

    def pose(self,i):
        levels=super().pose(i)
        # Keyboard and torso must stay attached to the fixed shoulder rig.
        for index,role,rest in self.scene.groove:
            if role=='piano':self.scene.instances[index]['matrix']=rest.copy()
        for rig in self.scene.rigs:
            kind,side=rig['role'],rig['side']
            if kind=='bass' and side=='pluck':
                hand=self.hand_targets[kind,side].copy();stroke=float(self.directions['bass'][i])
                hand[1]=1.03+.10*stroke;hand[2]=.485+.055*abs(stroke)
            elif kind=='piano':hand=self.key_hand_targets[side][i].copy()
            elif kind in ('lead','harmony') and side=='left':
                k=int(kind=='harmony');gain=float(self.voice_energy[i,k])
                hand=rig['hand']+(gain*.10,gain*.35,0)
            else:continue
            shoulder=rig['shoulder']
            lengths=rig.get('link_lengths',(.52,.50) if kind in ('lead','harmony') else (.80,.78))
            elbow=elbow_3d(shoulder,hand,*lengths,(-.8 if side in ('left','pluck') else .8,-.2,.8))
            a,b,c=rig['ids'];self.scene.instances[a]['matrix']=line_matrix(shoulder,elbow,.046)
            self.scene.instances[b]['matrix']=line_matrix(elbow,hand,.046)
            self.scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
            self.hand_targets[kind,side]=hand;self.joint_targets[kind,side]=(shoulder.copy(),elbow.copy(),hand.copy())
        for o in self.scene.instances:
            role=o.get('mouth_role')
            if role not in ('lead','harmony'):continue
            k=int(role=='harmony');shape=SHAPE_NAMES[int(self.voice_lanes[i,k])];w,h=SHAPES[shape]
            # Preserve the correct phoneme silhouette; vocal amplitude varies jaw.
            gain=.55+.45*np.sqrt(self.voice_energy[i,k]) if shape not in ('REST','MBP') else 1
            o['matrix']=matrix(o['mouth_center'],(w,h*gain,.031))
            levels[3+k]=self.voice_energy[i,k]*.6
            if hasattr(self.scene,'update_singer_mouth'):
                self.scene.update_singer_mouth(role,shape,self.voice_energy[i,k])
        return levels

