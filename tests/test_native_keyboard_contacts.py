import numpy as np
from models.final_band_scene import FinalBandScene
from models.native_keyboard_contacts import add_contacts


class Recorder:
    def __init__(self): self.items=[]
    def primitive(self, part, item): self.items.append((part,item))


def test_authored_contact_palms_stay_on_keys_in_their_own_reachable_half():
    scene=FinalBandScene(full_keyboard=True)
    keys={int(x['name'].rsplit('_',1)[1]):x for x in scene.instances
          if x['kind']!='hidden' and x['name'].startswith('piano_key_')}
    rigs=[r for r in scene.rigs if r['role']=='piano']
    middle=sum(r['shoulder'][0] for r in rigs)/2
    counts=[]
    for rig in rigs:
        out=Recorder();pitches=add_contacts(scene,out,rig);counts.append(len(pitches))
        assert pitches
        hands=[item['matrix'][:3,3] for _,item in out.items if item['kind']=='sphere']
        for pitch,hand in zip(pitches,hands):
            center=keys[pitch]['matrix'][:3,3]
            assert hand[0]<=middle if rig['side']=='left' else hand[0]>=middle
            np.testing.assert_allclose(hand[[0,2]],center[[0,2]])
            # Authored key half-height .035 and mitten half-height .075.
            assert abs((hand[1]-.075)-(center[1]+.035))<1e-9
            assert np.linalg.norm(hand-rig['shoulder'])<sum(rig['link_lengths'])
        assert len(out.items)==3*len(pitches)
    assert all(n>8 for n in counts)
