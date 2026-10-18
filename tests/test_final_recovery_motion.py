import unittest
import numpy as np
from models.keyboard_motion_plan import plan_keyboard_hands
from models.band_motion_refinement import elbow_3d
from tools.fixed_camera_motion import stage_motion
from animation.articulated_source_drummer import ArticulatedDrummer
from tools.render_drummer_v3_preview import TARGETS

class KeyboardRecovery(unittest.TestCase):
    def plan(self,sequence):
        held=np.full((len(sequence),6),-1);levels=np.zeros_like(held,dtype=float)
        for i,notes in enumerate(sequence):
            held[i,:len(notes)]=notes;levels[i,:len(notes)]=.8
        centers={p:np.array(((p-66)*.025,1.3,.65)) for p in range(48,85)}
        rigs={s:dict(shoulder=np.array((x,1.65,.05)),hand=np.array((x,1.395,.715)),link_lengths=(.8,.78)) for s,x in [('left',-.36),('right',.36)]}
        lanes,contacts,report=plan_keyboard_hands(held,levels,centers,rigs)
        for side,lane in lanes.items():
            self.assertLessEqual(np.linalg.norm(np.diff(lane,axis=0),axis=1).max(),.045001)
            self.assertLessEqual(np.linalg.norm(np.diff(lane,n=2,axis=0),axis=1).max(),.018001)
            self.assertTrue(np.all(lane[:,1]<1.55))
            for i,hand in enumerate(lane):
                elbow=elbow_3d(rigs[side]['shoulder'],hand,.8,.78,(-.8 if side=='left' else .8,-.2,.8))
                self.assertTrue(np.isfinite(elbow).all())
                if contacts[side][i] is not None:self.assertIn(contacts[side][i],sequence[i])
        self.assertTrue(np.all(lanes['left'][:,0]<=lanes['right'][:,0]))
        return lanes,contacts
    def test_repeated_single_notes(self):self.plan(([[60]]*3+[[]]*2)*20)
    def test_fast_scale_no_global_debounce(self):
        _,c=self.plan([[p] for p in list(range(52,65))*6])
        self.assertGreater(len(set(x for x in c['left'] if x is not None)),5)
    def test_wide_chords(self):self.plan([[48,55,60,72,79,84]]*80)
    def test_alternating_hands(self):self.plan([[55],[77]]*50)
    def test_sustained_release(self):
        _,c=self.plan([[60,72]]*60+[[]]*40)
        self.assertTrue(all(x is None for x in c['left'][60:]))
    def test_rapid_pitch_changes(self):self.plan([[48],[84],[60],[72]]*30)
    def test_sparse_no_return_to_torso(self):
        lanes,c=self.plan([[60]]*40+[[]]*60)
        self.assertLess(np.linalg.norm(lanes['left'][99]-lanes['left'][39]),.03)
    def test_outside_register_never_claimed(self):
        _,c=self.plan([[36,96]]*40)
        self.assertFalse(any(x is not None for values in c.values() for x in values))

class DrummerRecovery(unittest.TestCase):
    def test_all_authored_transitions_fixed_links_and_contact(self):
        empty=ArticulatedDrummer([],natural_arms=True)
        hits=[dict(time=i*.4,target=t,side=s,velocity=1.) for i,(t,s) in enumerate(empty.targets) if t!=TARGETS[2]]
        d=ArticulatedDrummer(hits,natural_arms=True)
        self.assertEqual(len(d.hits),len(hits))
        for t in np.arange(-.2,len(hits)*.4+.3,.005):
            for side in ('left','right'):
                d._pose(side,t);j=d.last_joints[side];a,b=d.lengths[side]
                self.assertAlmostEqual(np.linalg.norm(j['elbow']-j['shoulder']),a,places=5)
                self.assertAlmostEqual(np.linalg.norm(j['wrist']-j['elbow']),b,places=5)
        for e in d.hits:
            d._pose(e['side'],e['time']);j=d.last_joints[e['side']]
            np.testing.assert_allclose(j['tip'],d.targets[e['target'],e['side']][0],atol=1e-5)
    def test_right_snare_elbow_outward_down(self):
        d=ArticulatedDrummer([dict(time=0,target=TARGETS[1],side='right',velocity=1)],natural_arms=True)
        d._pose('right',0);j=d.last_joints['right']
        self.assertGreater(j['elbow'][1],j['shoulder'][1]+8)
        self.assertGreater(j['elbow'][0],j['shoulder'][0])
    def test_hihat_never_arms(self):
        hits=[dict(time=t,target=TARGETS[2],side='right',velocity=1) for t in (0,.05,.1)]
        d=ArticulatedDrummer(hits,natural_arms=True)
        self.assertEqual(len(d.foot_hits),3);self.assertFalse(d.hits)
        for e in hits:
            d.frame(e['time']);self.assertTrue(d.last_hi_hat_foot_down)

class FixedCameraGate(unittest.TestCase):
    def frames(self):
        x=np.zeros((20,100,160,3),dtype=np.uint8);x[:,45:80,35:130]=60;return x
    def test_local_motion_in_static_stage(self):
        x=self.frames()
        for i in range(20):x[i,55:65,50+i:58+i]=200
        self.assertGreater(stage_motion(x)['moving_transitions'],0)
    def test_frozen_rejected(self):
        with self.assertRaisesRegex(ValueError,'Frozen'):stage_motion(self.frames())
    def test_timestamp_alone_rejected(self):
        x=self.frames()
        for i in range(20):x[i,90:95,i:i+10]=255
        with self.assertRaisesRegex(ValueError,'Frozen'):stage_motion(x)
    def test_black_frame_rejected(self):
        x=self.frames();x[4]=0
        with self.assertRaisesRegex(ValueError,'Blank'):stage_motion(x)

if __name__=='__main__':unittest.main()
