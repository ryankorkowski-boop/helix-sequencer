"""Opt-in band refinement preserving the approved readable rig and original designs."""
import numpy as np
from models.readable_band_scene import ReadableBandScene

class RefinedBandScene(ReadableBandScene):
    def __init__(self,layout,mallet_range=(60,84),neutral_performers=False):
        self.neutral_performers=neutral_performers
        super().__init__(layout)
        low,high=mallet_range
        if not 48<=low<high<=96:raise ValueError('unsupported mallet register')
        self.mallet_low=low
        # A dedicated mallet player retains the established snowman aesthetic.
        # Piano source events stay on the keyboard; mallet provenance has its own rig.
        p=np.array((-6.55,0,1.20))
        self.snowman('xylophone',p,'#AD744A')
        self.box('xylophone_frame',p+(0,1.25,.65),(2.85,.14,.96),'#493425')
        self.bars={}
        spacing=min(.108,2.60/(high-low))
        for pitch in range(low,high+1):
            x=(pitch-(low+high)/2)*spacing
            original_range=mallet_range==(60,84)
            length=.85-.016*(pitch-60) if original_range else .85-.40*(pitch-low)/(high-low)
            pos=p+(x,1.44,.65)
            self.bars[pitch]=pos.copy()
            self.box(f'xylophone_bar_{pitch}',pos,(.080 if original_range else spacing*.74,.055,length),'#DBBA83' if pitch%2 else '#BC965D',self.mallet_slot(pitch))
            for side in (-1,1):
                edge=.043 if original_range else spacing*.40
                self.rod('xylophone_bar_edge',pos+(side*edge,.030,-length/2),pos+(side*edge,.030,length/2),.008 if original_range else .006,'#291D13')
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
        self.technical_proof['band_members'].append('xylophone / bells / marimba')
        if neutral_performers:
            self.technical_proof['band_members']=['singer A' if x=='male singer' else 'singer B' if x=='female singer' else x for x in self.technical_proof['band_members']]

    def mallet_slot(self,pitch):
        return 128+pitch-self.mallet_low

    def snowman(self,role,p,accent,female=False):
        neutral=self.neutral_performers and role in ('lead','harmony','xylophone')
        first=len(self.instances)
        # The second singer is intentionally gender-ambiguous and PURPLE,
        # not the inherited pink female-coded performer.
        if role=='harmony' and neutral:accent='#8653D9'
        center=super().snowman(role,p,accent,False if neutral else female)
        if neutral:
            from models.band_performance_scene import matrix,line_matrix
            for o in self.instances[first:]:
                if o['name']==role+'_hat_crown':
                    o['kind']='sphere';o['matrix']=matrix(p+(0,2.74,0),(.46,.19,.42))
                elif o['name']==role+'_hat_brim':
                    o['matrix']=line_matrix(p+(0,2.66,0),p+(0,2.71,0),.46)
                elif o['name']==role+'_hat_ribbon':
                    o['matrix']=line_matrix(p+(0,2.69,0),p+(0,2.735,0),.465)
            # Identical unisex beanies and facial details; accent is identity.
        return center

    def bass_contact(self,string,fret):
        """Same semitone string geometry used by guitar, with literal bass tuning."""
        s=self.strings['bass'][string]
        return s['a']+(s['b']-s['a'])*2**(-fret/12)
