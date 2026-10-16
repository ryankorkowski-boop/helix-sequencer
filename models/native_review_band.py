"""Seven snowmen, separate keys/mallets, and honest <=16-circuit AC variants.

Pixel geometry and AC geometry share authored XYZ coordinates. Multiple AC
bulb locations reference one node/circuit; they do not allocate extra channels.
"""
from __future__ import annotations
import copy
import numpy as np
from models.final_band_native import SurfaceParts
from models.review_snowman_scene import ReviewSnowmanScene, MOUTHS
from models.band_performance_scene import matrix, line_matrix
from models.band_motion_refinement import elbow_3d
from core.physical_band_circuits import DRUMMER

VISEMES = ('AI','E','FV','L','MBP','O','U','WQ','etc','rest')
SHAPE_VISEME = {'AH':'AI','EE':'E','OH':'O','FV':'FV','L':'L','MBP':'MBP','REST':'rest'}
VIS_SIZE = {'AI':MOUTHS['AH'],'E':MOUTHS['EE'],'O':MOUTHS['OH'],
    'FV':MOUTHS['FV'],'L':MOUTHS['L'],'MBP':MOUTHS['MBP'],'rest':MOUTHS['REST'],
    'U':(.060,.059),'WQ':(.052,.045),'etc':(.093,.038)}
ROLES = ('drummer','bass','guitar','piano','xylophone','lead','harmony')


def allocate(g):
    start=1
    for m in g.models:
        m.start=start;start+=16 if m.kind=='ac' else m.channels


def _mouths(parts, scene, role):
    t=np.linspace(0,2*np.pi,48,endpoint=False)
    for k,viseme in enumerate(VISEMES):
        w,h=VIS_SIZE[viseme]
        # Each separately wired aperture is a distinct physical outline.
        points=np.c_[w*np.cos(t),h*np.sin(t),np.full(len(t),.025+k*.014)]
        parts.add('MOUTH_'+viseme,points+scene.centers[role],'#F1C383')


def _role_parts(scene, role, position, scale, *, instrument_only=False):
    parts=SurfaceParts(position,scale=scale)
    arm_ids={i for r in scene.rigs for i in tuple(r['ids'])+tuple(r.get('mallet_ids',()))}
    instrument={'bass':'upright_bass','guitar':'electric_guitar'}
    for i,item in enumerate(scene.instances):
        name=item['name']
        if not (item.get('performer_role')==role or name.startswith(role+'_')):continue
        if instrument_only and item.get('performer_role')==role:continue
        if item['kind']=='hidden' or i in arm_ids or item.get('mouth_role'):continue
        part='BODY'
        if '_live_string_' in name:part='STRING_'+name.split('_live_string_')[1].split('_')[0]
        if role=='piano' and name.startswith('piano_key_'):part='NOTE_MIDI_'+name.rsplit('_',1)[1]
        if role=='xylophone' and name.startswith('xylophone_bar_') and name.rsplit('_',1)[1].isdigit():part='NOTE_MIDI_'+name.rsplit('_',1)[1]
        if '_eye' in name:part='EYES'
        parts.primitive(part,item)
    for item in scene.custom:
        if role in instrument and item['name'].startswith(instrument[role]):
            mesh=item['mesh'];points=np.vstack((mesh.vertices,mesh.triangles_center))
            parts.add('BODY',points[::max(1,len(points)//1200)],'#A87848')
    for rig in [r for r in scene.rigs if r['role']==role]:
        if instrument_only:continue
        side=rig['side'].upper()
        for i in tuple(rig['ids'])+tuple(rig.get('mallet_ids',())):parts.primitive('ARM_'+side+'_IDLE',scene.instances[i])
        shoulder=rig['shoulder'];hand=rig['hand']+np.array((0,.24,.18))
        elbow=elbow_3d(shoulder,hand,*rig.get('link_lengths',(.8,.78)),(-.8 if 'LEFT' in side else .8,-.2,.8))
        for a,b in ((shoulder,elbow),(elbow,hand)):
            parts.primitive('ARM_'+side+'_ACTIVE',dict(kind='cylinder',matrix=line_matrix(a,b,.045),color=np.array((.80,.75,.60))))
    if role in ('lead','harmony'):_mouths(parts,scene,role)
    return parts


def instrument_models():
    """Independent instrument files, in the same 3D world units as the cast."""
    from models.ultimate_showcase import Garden
    scene=ReviewSnowmanScene();g=Garden()
    for role in ('bass','guitar','piano','xylophone'):
        p=_role_parts(scene,role,(0,0,0),5,instrument_only=True)
        m=g.custom('HX_INSTRUMENT_'+role.upper(),p.points,'INSTRUMENTS',role+' instrument',p.colors,
            {k:sorted(set(v)) for k,v in p.parts.items()},details=dict(review_role=role,instrument_only=True))
        m.attrs['HelixOutputMode']='pixel'
    allocate(g)
    return g


def add_band(g, prefix='HX_SNOW', position=(0,0,75), *, scale=5):
    scene=ReviewSnowmanScene()
    from models.snowman_ensemble import build_ensemble
    drum=copy.deepcopy(build_ensemble().models[0]);points=drum.points
    span=np.maximum(np.ptp(points,axis=0),1);center=(points.min(axis=0)+points.max(axis=0))/2
    factors=np.array((22.5/span[0],14.6/span[1],4/span[2]))*(scale/5)
    new=np.asarray(position)+(0,11.3*scale/5,-7*scale/5)
    # Rebuild quantized native coordinates once rather than changing preview only.
    subs={c.name:[] for c in DRUMMER}
    for part,nodes in drum.submodels.items():
        for c in DRUMMER[1:]:
            if c.name in part and ('SURFACE' in part or 'ARM_STICK' in part or part.endswith(c.name)):
                subs[c.name].extend(nodes)
    # Split snare contact channels retain independent arm/stick poses.
    for side in ('LEFT','RIGHT'):
        subs['SNARE_'+side]=sorted(set(drum.submodels.get('HX_SNOWMAN_DRUMMER_V3_SNARE_SURFACE',[])+
            drum.submodels.get('HX_SNOWMAN_DRUMMER_V3_'+('SNARE_ARM_STICK' if side=='LEFT' else 'RIGHT_ARM_STICK'),[])))
    dynamic=set().union(*(set(v) for k,v in subs.items() if k!='BASE_DIM'))
    subs['BASE_DIM']=sorted(set(range(1,len(points)+1))-dynamic)
    g.custom(prefix+'_DRUMMER',(points-center)*factors+new,prefix,'Canonical snowman drummer',drum.colors,
        {k:sorted(set(v)) for k,v in subs.items()},details=dict(review_role='drummer',all_snowmen=True))
    for role in ROLES[1:]:
        p=_role_parts(scene,role,position,scale)
        subs={k:sorted(set(v)) for k,v in p.parts.items()}
        # Dynamic nodes own their channels; BODY never keeps notes/mouths on.
        dynamic=set().union(*(set(v) for k,v in subs.items() if k!='BODY'))
        subs['BODY']=sorted(set(subs.get('BODY',[]))-dynamic)
        m=g.custom(prefix+'_'+role.upper(),p.points,prefix,'Seven-snowman '+role,p.colors,subs,
            details=dict(review_role=role,all_snowmen=True,continuous_mesh_motion=False,
                         pose_method='addressable stationary light poses'))
        m.attrs['HelixOutputMode']='pixel'
        if role in ('lead','harmony'):m.children.append(('faceInfo',face_info(m)))
    allocate(g)
    return g.models[-7:]


def face_info(m):
    def ranges(ids):return ','.join(str(x) for x in ids)
    return dict(Name='Helix independent phonemes',Type='NodeRange',**{
        'Mouth-'+v:ranges(m.submodels['MOUTH_'+v]) for v in VISEMES},
        **{'Eyes-Open':ranges(m.submodels.get('EYES',[])),'Eyes-Closed':'','FaceOutline':ranges(m.submodels.get('BODY',[]))})


def ac_variant(model):
    m=copy.deepcopy(model);role=m.details['review_role']
    if role=='drummer':names=[c.name for c in DRUMMER]
    elif role in ('lead','harmony'):names=['BODY','EYES']+['MOUTH_'+v for v in VISEMES]+['ARM_LEFT_ACTIVE','ARM_RIGHT_ACTIVE']
    elif role in ('piano','xylophone'):names=['BODY']+['PITCH_CLASS_'+str(i) for i in range(12)]+['ARM_LEFT_ACTIVE','ARM_RIGHT_ACTIVE']
    else:names=['BODY']+['STRING_'+str(i) for i in range(4 if role=='bass' else 6)]+['ARM_'+s+'_'+a for s in ('PLUCK','FINGER') if role=='bass' for a in ('IDLE','ACTIVE')]
    if role=='guitar':names+=['ARM_'+s+'_'+a for s in ('STRUM','FINGER') for a in ('IDLE','ACTIVE')]
    names=[name for name in names if name in m.submodels or name.startswith('PITCH_CLASS_')]
    if len(names)>16:raise ValueError('Physical circuit overflow')
    ownership={}
    for j,name in enumerate(names,1):
        ids=list(m.submodels.get(name,[]))
        if name.startswith('PITCH_CLASS_'):
            pc=int(name.rsplit('_',1)[1]);ids=[n for part,nodes in m.submodels.items() if part.startswith('NOTE_MIDI_') and int(part.rsplit('_',1)[1])%12==pc for n in nodes]
        for node in ids:ownership[node]=j
    # Idle arm nodes join BODY if no dedicated idle circuit is allocated.
    for part,nodes in m.submodels.items():
        if part.endswith('_IDLE'):
            for node in nodes:ownership.setdefault(node,1)
    raw=m.attrs['CustomModelCompressed'].split(';');entries=[];points=[];colors=[];circuits=[]
    for entry,point,color in zip(raw,m.points,m.colors):
        bits=entry.split(',');node=int(bits[0]);circuit=ownership.get(node)
        if circuit is None:continue
        bits[0]=str(circuit);entries.append(','.join(bits));points.append(point);colors.append(color);circuits.append(circuit)
    m.attrs.update(CustomModelCompressed=';'.join(entries),StringType='Single Color White',HelixOutputMode='ac16',
        NodeNames=','.join(names))
    m.kind='ac';m.name+='_AC16';m.points=np.asarray(points);m.colors=colors
    m.submodels={name:[j] for j,name in enumerate(names,1)}
    m.details.update(circuit_count=len(names),point_circuits=circuits,ac_circuits=names,
        pitch_mapping='12 pitch classes shared across octaves; pixel/MIDI rung variants preserve absolute pitch',
        hardware_tested=False)
    m.children=[]
    if role in ('lead','harmony'):m.children.append(('faceInfo',face_info(m)))
    return m
