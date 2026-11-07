"""xLights NodeRange face definitions for the existing seven physical mouths."""
from tools.build_helpers.ultimate_showcase import _ranges

FACE_NAME='Helix_Seven_Mouths'
VISEME_TO_SHAPE={'AI':'AH','E':'EE','O':'OH','U':'OH','WQ':'OH',
                 'MBP':'MBP','FV':'FV','L':'L','etc':'EE','rest':'REST'}
SHAPE_TO_VISEME={'AH':'AI','EE':'E','OH':'O','MBP':'MBP','FV':'FV','L':'L','REST':'rest'}


def face_definition(model):
    if 'MOUTH_AH' not in model.submodels:return None
    attrs={'Name':FACE_NAME,'Type':'NodeRange','CustomColors':'0'}
    for viseme,shape in VISEME_TO_SHAPE.items():attrs['Mouth-'+viseme]=_ranges(model.submodels['MOUTH_'+shape])
    eyes=set(model.submodels.get('EYE_-1',[]))|set(model.submodels.get('EYE_1',[]))
    attrs['Eyes-Open']=_ranges(sorted(eyes))
    attrs['FaceOutline']=_ranges(sorted(set().union(*(set(model.submodels.get(p,[])) for p in ('OUTLINE','BASE','TORSO','HEAD')))))
    return attrs
