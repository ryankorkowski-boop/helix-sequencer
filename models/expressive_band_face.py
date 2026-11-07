"""Large, layered singing mouths for the optional two-stage preview rigs.

Only geometry follows the existing phoneme and measured amplitude lanes.
This module does not infer voices or change performance events.
"""
import math
import numpy as np
from models.band_performance_scene import matrix, tube, rgb


MOUTH_SIZES = {
    'REST': (.245, .022), 'MBP': (.250, .027), 'AH': (.290, .205),
    'EE': (.310, .090), 'OH': (.205, .190), 'FV': (.260, .070),
    'L': (.250, .165),
}


def lip_ring_mesh():
    t = np.linspace(0, math.tau, 64, endpoint=False)
    return tube(np.c_[np.cos(t), np.sin(t), np.zeros(len(t))], .15, True)


def add_expressive_mouths(scene, wire=False):
    scene.expressive_mouths = {}
    # Append details after all rig indices have been assigned.
    for role in ('lead', 'harmony'):
        cavity_index, cavity = next((i,o) for i,o in enumerate(scene.instances) if o.get('mouth_role') == role)
        center = cavity['mouth_center'] + (0, -.045, .19)
        cavity['mouth_center'] = center
        cavity['color'] = rgb('#080B14')
        cavity['slot'] = -1
        ids = {'cavity': cavity_index, 'center': center}
        if wire:
            ids['backing'] = len(scene.instances)
            scene.sphere(role+'_mouth_backing', center+(0, 0, -.08),
                         (.35, .25, .025), '#101724')
        ids['lips'] = len(scene.instances)
        scene.primitive('lip_ring', role+'_lips', center+(0, 0, .033),
                        (.29, .06, .075), '#F86A64', 177)
        ids['tongue'] = len(scene.instances)
        scene.sphere(role+'_tongue', center, (.001, .001, .001), '#F486B6', 177)
        ids['teeth'] = len(scene.instances)
        scene.sphere(role+'_upper_teeth', center, (.001, .001, .001), '#FFF1D3')
        for key in ('backing', 'lips', 'tongue', 'teeth'):
            if key in ids:
                scene.instances[ids[key]]['performer_role'] = role
        # Move the carrot above the enlarged aperture and in front of its mask.
        nose = next(o for o in scene.instances if o['name'] == role+'_carrot')
        nose['matrix'][1, 3] += .10
        nose['matrix'][2, 3] += .21
        scene.expressive_mouths[role] = ids
        update_expressive_mouth(scene, role, 'REST', 0)


def update_expressive_mouth(scene, role, shape, energy):
    ids = scene.expressive_mouths[role]
    center = ids['center']
    w, h = MOUTH_SIZES[shape]
    closed = shape in ('REST', 'MBP')
    # A silent/consonant closure remains closed; amplitude scales open vowels.
    if not closed:
        h *= .65 + .35 * np.sqrt(np.clip(energy, 0, 1))
    scene.instances[ids['cavity']]['matrix'] = matrix(center, (w, h, .040))
    scene.instances[ids['lips']]['matrix'] = matrix(center+(0, 0, .033),
                                                   (w*1.12, h+.016, .080))
    if 'backing' in ids:
        # Mask only the current aperture, including at rest, so a closed mouth
        # does not leave a large opaque muzzle across the wire face.
        scene.instances[ids['backing']]['matrix'] = matrix(center+(0, 0, -.036),
                                                          (w*1.20, h+.035, .020))
    tiny = (.0001, .0001, .0001)
    tongue_center = center+(0, -h*.48 if shape != 'L' else -h*.10, .049)
    tongue_size = tiny if closed else (w*.60, h*(.32 if shape != 'L' else .55), .025)
    teeth_center = center+(0, h*.59, .052)
    teeth_size = tiny if closed or shape == 'OH' else (w*.77, min(.040, h*.22), .021)
    scene.instances[ids['tongue']]['matrix'] = matrix(tongue_center, tongue_size)
    scene.instances[ids['teeth']]['matrix'] = matrix(teeth_center, teeth_size)
    for key in ('cavity', 'lips', 'tongue', 'teeth'):
        scene.instances[ids[key]]['mouth_shape'] = shape
