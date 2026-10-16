"""Seven-member performance adapter, preserving existing string/drum motion."""
import json
from pathlib import Path
import numpy as np
from music.note_events import NoteEvent
from music.review_score import spatial_score
from music.unified_mallet import unified_mallet_schedule
from models.band_sampler_logic import SHAPE_NAMES
from tools.musical_band_performance import MusicalBandPerformance
from tools.readable_band_performance import ReadablePerformance


class ReviewBandPerformance(MusicalBandPerformance):
    def __init__(self,row,scene,analysis_root):
        super().__init__(row,scene,analysis_root,separate_pitched=True)
        folder=Path(analysis_root)/row['id'];roles=json.loads((folder/'pitched_roles.json').read_text())
        if roles['source_sha256']!=row['sha256']:raise ValueError('pitch source mismatch')
        self.keyboard_events=[NoteEvent(**e) for e in roles['keyboard']]
        reachable={}
        for rig in scene.rigs:
            if rig['role']=='xylophone':
                reachable[rig['side']]={pitch for pitch,pos in scene.bars.items()
                    if np.linalg.norm(pos+(0,.0275+.057+.2598076211,-.15)-rig['shoulder'])<sum(rig['link_lengths'])-1e-7}
        self.mallet_schedule,self.mallet_motion_omissions=unified_mallet_schedule(
            [NoteEvent(**e) for e in roles['mallets']],duration=self.n/20,
            low=min(scene.bars),high=max(scene.bars),reachable=reachable)
        with np.load(folder/'vocal_clock.npz') as z:self.vocal_clock={k:z[k].copy() for k in z.files}
        self.voice_lanes=np.zeros((self.n,2),'i1');self.voice_energy=np.zeros((self.n,2),'f4')
        for i in range(self.n):
            j=min(len(self.vocal_clock['energy'])-1,i*5)
            self.voice_lanes[i,0]=self.vocal_clock['shapes'][j]
            self.voice_energy[i,0]=self.vocal_clock['energy'][j]
        # Optional evidence-based routing is source-bound and supersedes only
        # this review's lead-only clock. Legacy authored casting stays intact.
        routed=folder/'voice_roles.npz'
        if routed.exists():
            report=json.loads((folder/'voice_roles.json').read_text())
            if report['source_sha256']!=row['sha256']:raise ValueError('voice source mismatch')
            with np.load(routed) as z:
                if z['energy'].shape!=(self.n,2):raise ValueError('voice frame count mismatch')
                self.voice_energy=z['energy'].copy();self.voice_lanes=z['shapes'].copy()
            self.voice_routing_report=report
        self.curves['vocal_energy']=self.voice_energy[:,0];self.curves['mouth_lanes']=self.voice_lanes
        centers=[]
        for slot in range(64,112):
            parts=[o['mesh'].centroid for o in scene.custom if o['slot']==slot]
            centers.append(np.mean(parts,axis=0) if parts else (slot-88,0,0))
        self.stage_levels,self.stage_proof=spatial_score(self,centers,np.arange(48)%6)
        if hasattr(scene,'configure_drummer'):
            from tools.render_refined_helix_band import physical_hits
            scene.configure_drummer(physical_hits(row['drummer_xsq']))

    def levels(self,i):
        out=np.pad(ReadablePerformance.levels(self,i),(0,64))
        for hit in self.mallet_schedule:
            age=i/20-hit['time']
            if 0<=age<.26:
                slot=self.scene.mallet_slot(hit['pitch'])
                out[slot]=max(out[slot],hit['velocity']*np.exp(-age/.09))
        return out

    def pose(self,i):
        levels=super().pose(i);levels[64:112]=self.stage_levels[:,i]
        if hasattr(self.scene,'update_drummer'):self.scene.update_drummer(i/20)
        for k,role in enumerate(('lead','harmony')):
            self.scene.update_singer_mouth(role,SHAPE_NAMES[int(self.voice_lanes[i,k])],float(self.voice_energy[i,k]))
        return levels
