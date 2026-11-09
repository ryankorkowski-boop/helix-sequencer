"""Literal-key contact poses using the existing pianist shoulders and links."""
import numpy as np
from models.band_motion_refinement import elbow_3d
from models.band_performance_scene import matrix, line_matrix


def add_contacts(scene, parts, rig):
    side=rig['side'].upper()
    shoulders=[r['shoulder'][0] for r in scene.rigs if r['role']=='piano']
    middle=sum(shoulders)/len(shoulders)
    shoulder=np.asarray(rig['shoulder'])
    upper,lower=rig.get('link_lengths',(.8,.78))
    pitches=[]
    for key in scene.instances:
        if key['kind']=='hidden' or not key['name'].startswith('piano_key_'):
            continue
        pitch=int(key['name'].rsplit('_',1)[1])
        center=key['matrix'][:3,3]
        if (side=='LEFT' and center[0]>middle) or (side=='RIGHT' and center[0]<middle):
            continue
        # Palm bottom rests on the authored key top. No below-key sinking.
        hand=center+np.array((0,.110,0))
        distance=float(np.linalg.norm(hand-shoulder))
        if not abs(upper-lower)+.05 < distance < upper+lower-.05:
            continue
        elbow=elbow_3d(shoulder,hand,upper,lower,(-.8 if side=='LEFT' else .8,-.2,.8))
        part=f'ARM_{side}_NOTE_{pitch}'
        for a,b in ((shoulder,elbow),(elbow,hand)):
            parts.primitive(part,dict(kind='cylinder',matrix=line_matrix(a,b,.045),color=np.array((.72,.57,.40))))
        parts.primitive(part,dict(kind='sphere',matrix=matrix(hand,(.10,.075,.08)),color=np.array((.82,.90,.94))))
        pitches.append(pitch)
    return pitches
