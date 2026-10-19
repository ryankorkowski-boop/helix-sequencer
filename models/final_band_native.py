"""Finite native pixel bands sampled from the solid final scene surfaces.

Articulated preview meshes and stationary light poses are different outputs.
These addressable poses describe pixel props, never guessed AC wiring.
"""
from __future__ import annotations

import copy
import numpy as np
import trimesh
from models.final_band_scene import FinalBandScene
from models.band_performance_scene import matrix, line_matrix
from models.band_motion_refinement import elbow_3d
from models.expressive_band_face import MOUTH_SIZES


class SurfaceParts:
    def __init__(self, origin, scale=5):
        self.origin = np.asarray(origin); self.scale = scale
        self.points, self.colors, self.parts, self.lookup = [], [], {}, {}

    def add(self, part, points, color):
        ids = []
        for point in np.asarray(points)*self.scale+self.origin:
            cell = tuple(np.rint(point*16)/16)
            if cell not in self.lookup:
                self.lookup[cell] = len(self.points)+1
                self.points.append(cell); self.colors.append(color)
            ids.append(self.lookup[cell])
        self.parts.setdefault(part, []).extend(ids)

    def primitive(self, part, item):
        kind = item['kind']
        if kind == 'hidden': return
        mesh = {'sphere': lambda: trimesh.creation.icosphere(subdivisions=1),
                'box': trimesh.creation.box,
                'cylinder': lambda: trimesh.creation.cylinder(radius=1, height=1, sections=10)}[kind]()
        # Surface vertices plus triangle centers fill recognizable solid forms.
        points = np.vstack((mesh.vertices, mesh.triangles_center))
        points = (np.c_[points, np.ones(len(points))]@item['matrix'].T)[:, :3]
        color = '#'+''.join(f'{int(np.clip(c,0,1)*255):02X}' for c in item['color'])
        self.add(part, points, color)


def add_final_native_band(garden, prefix, position, *, rock=False, stage='ember_amphitheatre'):
    scene = FinalBandScene(stage, rock=rock)
    # Import all original canonical submodels; only this copy's world placement
    # changes. The existing physical kit and channel identities stay intact.
    from models.snowman_ensemble import build_ensemble
    drummer = copy.deepcopy(build_ensemble().models[0])
    points = drummer.points
    span = np.maximum(np.ptp(points, axis=0), 1)
    factors = np.array((22.5/span[0], 14.6/span[1], 1/span[2]))
    old_center = (points.max(axis=0)+points.min(axis=0))/2
    new_center = np.asarray(position)+(0,11.3,-7)
    drummer.points = (points-old_center)*factors+new_center
    for i, axis in enumerate('XYZ'):
        drummer.attrs['Scale'+axis] = str(float(drummer.attrs.get('Scale'+axis, 1))*factors[i])
        drummer.attrs['WorldPos'+axis] = str(new_center[i])
    # Imported XML attributes include the old model name. Native serializers
    # expand attrs last, so retaining it silently duplicates both stage names.
    drummer.attrs.pop('name', None)
    drummer.name = prefix+'_DRUMMER'; drummer.zone = prefix
    drummer.details.update(final_band_role='drummer', stage=prefix,
        style='source drummer; original component/contact submodels retained')
    garden.models.append(drummer)
    arm_ids = {i for r in scene.rigs for i in tuple(r['ids'])+tuple(r.get('mallet_ids',()))}
    instrument = {'bass': 'upright_bass', 'guitar': 'electric_guitar'}
    for role in ('bass', 'guitar', 'lead', 'harmony', 'piano'):
        parts = SurfaceParts(position)
        for i, item in enumerate(scene.instances):
            name = item['name']
            if not (item.get('performer_role') == role or name.startswith(role+'_')): continue
            if item['kind'] == 'hidden' or i in arm_ids or item.get('mouth_role'): continue
            if any(word in name for word in ('_lips','_tongue','_upper_teeth')): continue
            part = 'BODY'
            if '_live_string_' in name: part = 'STRING_'+name.split('_live_string_')[1].split('_')[0]
            if name.startswith('piano_key_') and name.removeprefix('piano_key_').isdigit():
                part = 'NOTE_MIDI_'+name.rsplit('_',1)[1]
            parts.primitive(part, item)
        for item in scene.custom:
            if role in instrument and item['name'].startswith(instrument[role]):
                mesh = item['mesh']; points = np.vstack((mesh.vertices, mesh.triangles_center))
                # All original closed surfaces are retained; deterministic
                # bounded sampling avoids a million-node instrument prop.
                points = points[::max(1, len(points)//1800)]
                color = '#'+''.join(f'{int(np.clip(c,0,1)*255):02X}' for c in item['color'])
                parts.add('BODY', points, color)
        for rig in [r for r in scene.rigs if r['role'] == role]:
            side = rig['side'].upper()
            for i in tuple(rig['ids'])+tuple(rig.get('mallet_ids',())):
                parts.primitive('ARM_'+side+'_IDLE', scene.instances[i])
            if role != 'xylophone':
                for i in rig['ids']:
                    parts.primitive('ARM_'+side+'_ACTIVE', scene.instances[i])
                continue
            for pitch, center in scene.bars.items():
                tip = center+(0,.0275+.057,0); hand = tip+(0,.2598076211,-.15)
                shoulder = rig['shoulder']
                if np.linalg.norm(hand-shoulder) >= sum(rig['link_lengths'])-1e-7:
                    continue
                elbow = elbow_3d(shoulder, hand, *rig['link_lengths'],
                    (-.8 if rig['side']=='left' else .8,-.2,.8))
                part = f'ARM_{side}_NOTE_{pitch}'
                for a,b in ((shoulder,elbow),(elbow,hand),(hand,tip)):
                    parts.primitive(part,dict(kind='cylinder',matrix=line_matrix(a,b,.035),color=np.array((.82,.69,.47))))
                parts.primitive(part,dict(kind='sphere',matrix=matrix(tip,(.057,.057,.057)),color=np.array((.82,.69,.47))))
        if role in ('lead','harmony'):
            center = scene.expressive_mouths[role]['center']
            for shape, (width,height) in MOUTH_SIZES.items():
                # Opaque aperture is a video feature; native open mouths expose
                # filled lips/tongue and keep their nodes separate from BODY.
                for component, offset, scale, color in (
                    ('LIPS',(0,0,.033),(width*1.12,height+.016,.08),(.97,.42,.39)),
                    ('TONGUE',(0,-height*.4,.06),(width*.60,height*.30,.025),(.96,.53,.71))):
                    if shape in ('REST','MBP') and component == 'TONGUE': continue
                    parts.primitive('MOUTH_'+shape,dict(kind='sphere',matrix=matrix(center+offset,scale),color=np.array(color)))
        model = garden.custom(prefix+'_'+role.upper(), np.asarray(parts.points), prefix,
            'solid rock performer' if rock else 'solid snow performer', parts.colors,
            {k:sorted(set(v)) for k,v in parts.parts.items()},
            details=dict(final_band_role=role, stage=prefix, solid_surface_samples=True,
                pose_method='stationary addressable light poses',
                continuous_mesh_motion=False, wireframe_performer=False))
        # Surface sampling can quantize a passing arm and a different bar to
        # the same node. Keys own their nodes exclusively; an arm must never
        # illuminate a note that the source did not request. Keep allocation
        # and bar identities stable, trimming only overlapping pose nodes.
        note_nodes = set().union(*(set(v) for k,v in model.submodels.items()
                                  if k.startswith('NOTE_MIDI_')))
        for part, nodes in model.submodels.items():
            if not part.startswith('NOTE_MIDI_'):
                model.submodels[part] = sorted(set(nodes)-note_nodes)
        # Dynamic notes, strings, mouths and pose nodes have exclusive ownership;
        # a dim BODY must not keep a released key or mouth illuminated.
        dynamic = set().union(*(set(v) for k,v in model.submodels.items()
                               if k.startswith(('MOUTH_','NOTE_MIDI_','STRING_','ARM_'))))
        model.submodels['BODY'] = sorted(set(model.submodels.get('BODY', ())) - dynamic)
    x,y,z = position
    for side in (-1,1):
        garden.poly(prefix+f'_STAGE_PORTAL_{side}',
            [(x+side*48,y,z-25),(x+side*48,y+35,z-25),(x,y+43,z-25)],
            180,prefix,'stage portal', '#C09862' if not rock else '#9077BB')
    garden.poly(prefix+'_STAGE_APRON',[(x-48,y,z+25),(x+48,y,z+25)],
        150,prefix,'clear front-stage sightline','#C09862' if not rock else '#9077BB')
    return dict(prefix=prefix, position=list(position), stage=stage,
        style='solid rock' if rock else 'solid snow', performers=6,
        unified_pitched_performer=True, continuous_mesh_motion=False,
        output='native addressable RGB pixel poses; no AC controller addresses inferred')
