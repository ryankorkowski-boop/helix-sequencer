"""Opt-in band refinement preserving the approved readable rig and original designs."""
import numpy as np
from models.readable_band_scene import ReadableBandScene

class RefinedBandScene(ReadableBandScene):
    def __init__(self,layout):
        super().__init__(layout)
        # A dedicated mallet player retains the established snowman aesthetic.
        # Piano source events stay on the keyboard; mallet provenance has its own rig.
        p=np.array((-6.55,0,1.20))
        self.snowman('xylophone',p,'#AD744A')
        self.box('xylophone_frame',p+(0,1.25,.65),(2.85,.14,.96),'#493425')
        self.bars={}
        for pitch in range(60,85):
            x=(pitch-72)*.108
            length=.85-.016*(pitch-60)
            pos=p+(x,1.44,.65)
            self.bars[pitch]=pos.copy()
            self.box(f'xylophone_bar_{pitch}',pos,(.080,.055,length),'#DBBA83' if pitch%2 else '#BC965D',128+pitch-60)
            for side in (-1,1):
                self.rod('xylophone_bar_edge',pos+(side*.043,.030,-length/2),pos+(side*.043,.030,length/2),.008,'#291D13')
            self.rod('xylophone_bar_pin',pos+(-.026,.031,.10),pos+(.026,.031,.10),.007,'#473221')
        for side in (-1,1):
            self.rod('xylophone_stand',p+(side*1.1,.05,.65),p+(side*1.1,1.25,.65),.042,'#687074')
            hand=p+(side*.60,1.60,.35)
            self.arm('xylophone_'+('left' if side<0 else 'right'),p+(side*.36,1.65,.05),p+(side*.54,1.55,.2),hand,'xylophone','left' if side<0 else 'right')
            rig=self.rigs[-1];rig['mallet_ids']=(len(self.instances),len(self.instances)+1)
            self.rod('xylophone_mallet_shaft',hand,hand+(0,0,.30),.017,'#D7BE8B')
            self.sphere('xylophone_mallet_head',hand+(0,0,.30),(.057,.057,.057),'#D4B17A')
        # Restrained metallic definition stays visible at rest.
        for item in self.instances:
            if '_live_string_' in item['name']:
                item['color']=np.array((.82,.78,.66) if item['name'].startswith('bass') else (.76,.77,.73),dtype='f4')
        # Authored link lengths belong to the character, never to the current
        # hand target. Existing preview arms stretched with every note.
        lengths={('bass','pluck'):(.80,.78),('bass','finger'):(.93,.91),
                 ('guitar','strum'):(.76,.74),('guitar','finger'):(.83,.81),
                 ('xylophone','left'):(.75,.73),('xylophone','right'):(.75,.73)}
        for rig in self.rigs:
            if (rig['role'],rig['side']) in lengths:
                rig['link_lengths']=lengths[rig['role'],rig['side']]
        self.technical_proof=self.validate()

    def bass_contact(self,string,fret):
        """Same semitone string geometry used by guitar, with literal bass tuning."""
        s=self.strings['bass'][string]
        return s['a']+(s['b']-s['a'])*2**(-fret/12)
