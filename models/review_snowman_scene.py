"""Seven sculpted snowmen, separate instruments and restrained coal mouths."""
import numpy as np
from models.refined_band_scene import RefinedBandScene
from models.band_performance_scene import matrix,rgb

MOUTHS={'REST':(.078,.007),'MBP':(.080,.009),'AH':(.111,.071),'EE':(.124,.032),
        'OH':(.072,.065),'FV':(.090,.023),'L':(.088,.053)}


class ReviewSnowmanScene(RefinedBandScene):
    def __init__(self,layout='prismatic_orrery'):
        super().__init__(layout,(48,96),neutral_performers=True)
        self.visible_roles=('drummer','bass','guitar','piano','xylophone','lead','harmony');self.centers={}
        for role in ('lead','harmony'):
            head=next(o for o in self.instances if o['name']==role+'_head')
            center=head['matrix'][:3,3]+(0,-.13,np.linalg.norm(head['matrix'][:3,2])*.98)
            self.centers[role]=center
            mouth=next(o for o in self.instances if o.get('mouth_role')==role)
            mouth['mouth_center']=center.copy();mouth['slot']=-1;mouth['color']=rgb('#101820')
            self.update_singer_mouth(role,'REST',0)
        self.technical_proof.update(band_members=list(self.visible_roles),all_snowmen=True,
            separate_keyboard_and_mallet_performers=True,exaggerated_lips=False)

    def update_singer_mouth(self,role,shape,energy):
        if role not in getattr(self,'centers',{}):return
        w,h=MOUTHS[shape]
        if shape not in ('REST','MBP'):h*=.18+.82*np.clip(energy,0,1)
        mouth=next(o for o in self.instances if o.get('mouth_role')==role)
        mouth['matrix']=matrix(self.centers[role],(w,h,.022));mouth['mouth_shape']=shape
