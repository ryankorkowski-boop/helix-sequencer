"""Opt-in volumetric snow drummer; original accepted pose art remains intact."""
import numpy as np
from models.review_snowman_scene import ReviewSnowmanScene
from models.band_performance_scene import matrix,line_matrix
from models.band_motion_refinement import elbow_3d

TARGETS=('KICK','SNARE','HI_HAT','TOM_HIGH','TOM_MID','TOM_FLOOR','CYMBAL_LEFT','CYMBAL_RIGHT')


class Review3DScene(ReviewSnowmanScene):
    def __init__(self,layout='prismatic_orrery'):
        super().__init__(layout)
        self.snowman('drummer',np.array((0,.35,-3.6)),'#86C6E7')
        # Audience-view staging: screen left -> right must be
        # LEFT CYMBAL, FLOOR TOM, MID TOM, KICK, SNARE, HIGH TOM,
        # HI-HAT, RIGHT CYMBAL. Front cameras look along -Z, so
        # increasingly positive world X is increasingly screen-right.
        # The legacy arrangement had the hi-hat and floor tom reversed.
        self.drum_centers={
            'CYMBAL_LEFT':np.array((-2.34,2.53,-3.08)),
            'TOM_FLOOR':np.array((-1.64,1.36,-2.36)),
            'TOM_MID':np.array((-.91,1.96,-2.80)),
            'KICK':np.array((0,.82,-2.25)),
            'SNARE':np.array((.72,1.53,-2.31)),
            'TOM_HIGH':np.array((1.24,2.07,-2.80)),
            'HI_HAT':np.array((1.76,2.03,-2.65)),
            'CYMBAL_RIGHT':np.array((2.38,2.55,-3.08))}
        # The original 3.45-wide riser clipped both ends of the kit.
        # Resize only this review-stage riser; preserve all note routing.
        riser=next(o for o in self.instances if o['name']=='drum_riser')
        riser['matrix'][0,0]=5.8
        riser['matrix'][2,2]=2.9
        riser['matrix'][2,3]=-2.42
        self.drummer_parts={};self.drummer_rigs={}
        for j,(name,center) in enumerate(self.drum_centers.items()):
            first=len(self.instances);metal='CYMBAL' in name or name=='HI_HAT';radius=.40 if metal else .30
            if name=='KICK':
                self.rod('drummer_KICK',center+(0,0,-.48),center,.57,'#357DA9',5+j)
                self.rod('drummer_KICK_RIM',center,center+(0,0,.035),.585,'#A4D9E9',5+j)
            else:
                self.rod('drummer_'+name,center-(0,.025 if metal else .22,0),center,radius,'#BDA665' if metal else '#4C8EAD',5+j)
                self.rod('drummer_'+name+'_RIM',center,center+(0,.018,0),radius+.018,'#D4E5E7',5+j)
                self.rod('drummer_'+name+'_STAND',center-(0,.25,0),(center[0],.05,center[2]),.024,'#6A7A86')
            self.drummer_parts[name]=list(range(first,len(self.instances)))
        for side in ('left','right'):
            sign=-1 if side=='left' else 1;shoulder=np.array((sign*.38,2.0,-3.55));hand=shoulder+(sign*.22,-.1,.43)
            start=len(self.instances)
            self.rod('drummer_'+side+'_UPPER',shoulder,hand,.047,'#996B45')
            self.rod('drummer_'+side+'_FOREARM',shoulder,hand,.041,'#996B45')
            self.sphere('drummer_'+side+'_MITTEN',hand,(.10,.075,.08),'#D5E5EF')
            self.rod('drummer_'+side+'_STICK',hand,hand+(0,-.36,.30),.018,'#DDBB83')
            self.drummer_rigs[side]=dict(shoulder=shoulder,ids=tuple(range(start,start+4)),idle=hand)
        self.hihat_pedal=len(self.instances)
        self.rod('drummer_HIHAT_FOOT_PEDAL',(1.75,.09,-3.03),(1.75,.16,-2.68),.075,'#8095A3')
        self.hihat_foot=len(self.instances)
        self.sphere('drummer_HIHAT_FOOT',(1.75,.22,-2.82),(.20,.095,.30),'#D5E5EF')
        self.kick_beater=len(self.instances)
        self.rod('drummer_KICK_BEATER',(0,.10,-1.94),(0,.45,-1.94),.025,'#C5B592',5)
        self.drum_hits=[];self.drum_contact_proof=[]
        self.drum_geometry_contract='audience_left_to_right_v1'

    def configure_drummer(self,hits):
        self.drum_hits=[]
        for h in hits:
            target=h['target'].removeprefix('HX_SNOWMAN_DRUMMER_V3_')
            # Both snare-hand cue channels strike the same physical snare.
            if target in ('SNARE_LEFT','SNARE_RIGHT'):
                h=dict(h,side='left' if target.endswith('LEFT') else 'right')
                target='SNARE'
            if target not in self.drum_centers:continue
            # Keep original source component and timing, but do not animate
            # physically impossible cross-body strikes on extreme toms/cymbals.
            source_side=h.get('side')
            natural_side=('left' if target in ('CYMBAL_LEFT','TOM_FLOOR','TOM_MID')
                          else 'right' if target in ('CYMBAL_RIGHT','TOM_HIGH')
                          else source_side)
            self.drum_hits.append(dict(h,target=target,source_side=source_side,
                side=natural_side,visual_side_reassigned=(source_side!=natural_side),
                source_time=h['time'],time=round(h['time']*20)/20))

    def update_drummer(self,time):
        contacts=[]
        for side,rig in self.drummer_rigs.items():
            candidates=[h for h in self.drum_hits if h['target'] not in ('KICK','HI_HAT') and h['side']==side and -.10<=time-h['time']<=.18]
            hit=min(candidates,key=lambda h:abs(h['time']-time)) if candidates else None
            hand=rig['idle'].copy();tip=hand+(0,-.36,.30)
            if hit:
                age=time-hit['time'];contact=self.drum_centers[hit['target']]
                lift=.42*min(1,abs(age)/(.10 if age<0 else .18))
                tip=contact+(0,lift,0);hand=tip+(0,.36,-.30)
                # The far cymbals lie outside a mitten's default vertical
                # striking line. Angle the stick toward the cymbal while
                # keeping the arm itself within the fixed two-link reach.
                reach=hand-rig['shoulder']
                distance=float(np.linalg.norm(reach))
                if distance>1.68:
                    hand-=reach*((distance-1.68)/distance)
                if abs(age)<1e-7:contacts.append(dict(target=hit['target'],side=side,time=time,
                    source_time=hit['source_time'],error=float(np.linalg.norm(tip-contact))))
            elbow=elbow_3d(rig['shoulder'],hand,.91,.89,(-.9 if side=='left' else .9,0,.5))
            a,b,c,d=rig['ids']
            self.instances[a]['matrix']=line_matrix(rig['shoulder'],elbow,.047)
            self.instances[b]['matrix']=line_matrix(elbow,hand,.041)
            self.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
            self.instances[d]['matrix']=line_matrix(hand,tip,.018)
        foot_hit=any(h['target']=='HI_HAT' and 0<=time-h['time']<.10 for h in self.drum_hits)
        pedal_lift=0.0 if foot_hit else .10
        self.instances[self.hihat_pedal]['matrix']=line_matrix((1.75,.09,-3.03),(1.75,.16+pedal_lift,-2.68),.075)
        self.instances[self.hihat_foot]['matrix']=matrix((1.75,.22+pedal_lift,-2.82),(.20,.095,.30))
        kicks=[h for h in self.drum_hits if h['target']=='KICK' and 0<=time-h['time']<.1]
        tip=self.drum_centers['KICK'] if kicks else np.array((0,.45,-1.94))
        self.instances[self.kick_beater]['matrix']=line_matrix((0,.10,-1.94),tip,.025)
        self.drum_contact_proof=contacts
