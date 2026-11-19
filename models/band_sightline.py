"""Keep the canonical drum kit unobstructed in the fixed front approval view.

The orthographic approval camera has no parallax, so a singer standing in
front of the kit hides whatever is directly behind them (ride, crashes, floor
tom).  Rather than move or shrink the owner-referenced drummer, the two
flanking groups are slid outward as rigid units, preserving their reviewed
relative staging, until the kit corridor is clear.
"""
from __future__ import annotations

import numpy as np

ROLE_PREFIXES = {
    'bass': ('bass_', 'upright_bass'),
    'guitar': ('guitar_', 'electric_guitar'),
    'piano': ('piano_', 'keyboard_'),
    'lead': ('lead_',),
    'harmony': ('harmony_',),
}
LEFT_GROUP = ('lead', 'bass')
# Half extents of the shared unit primitives (icosphere r=1, unit box,
# cylinder r=1 h=1); an axis-aligned bound of the transformed primitive.
UNIT_HALF_EXTENTS = {'sphere': (1., 1., 1.), 'box': (.5, .5, .5), 'cylinder': (1., 1., .5)}
RIGHT_GROUP = ('harmony', 'guitar', 'piano')


def role_of(item):
    role = item.get('performer_role')
    if role in ROLE_PREFIXES:
        return role
    for name, prefixes in ROLE_PREFIXES.items():
        if item['name'].startswith(prefixes):
            return name
    return None


def role_extents(scene):
    """Conservative visible X interval of each performer and instrument."""
    spans = {}
    def grow(role, low, high):
        a, b = spans.get(role, (np.inf, -np.inf))
        spans[role] = (min(a, float(low)), max(b, float(high)))
    for item in scene.instances:
        role = role_of(item)
        if role is None or item['kind'] == 'hidden':
            continue
        grow(role, *instance_interval(item))
    for item in scene.custom:
        role = role_of(item)
        if role is not None:
            bounds = item['mesh'].bounds
            grow(role, bounds[0][0], bounds[1][0])
    return spans


def shift_role(scene, role, offset):
    """Rigidly translate one performer with every bound rig and contact."""
    offset = np.asarray(offset, float)
    for item in scene.instances:
        if role_of(item) != role:
            continue
        item['matrix'][:3, 3] += offset
        if 'mouth_center' in item:
            item['mouth_center'] = item['mouth_center']+offset
    for item in scene.custom:
        if role_of(item) == role:
            item['mesh'].apply_translation(offset)
    for rig in scene.rigs:
        if rig['role'] == role:
            for key in ('shoulder', 'elbow', 'hand'):
                rig[key] = rig[key]+offset
    for string in getattr(scene, 'strings', {}).get(role, ()):
        string['a'] = string['a']+offset; string['b'] = string['b']+offset
    mouths = getattr(scene, 'expressive_mouths', {})
    if role in mouths:
        ids = mouths[role]
        ids['center'] = scene.instances[ids['cavity']]['mouth_center']


def instance_interval(item):
    m = item['matrix']; half = float(np.abs(m[0, :3])@UNIT_HALF_EXTENTS.get(item['kind'], (1.15, 1.15, 1.15)))
    return float(m[0, 3]-half), float(m[0, 3]+half)


def widen_stage(scene, left_factor, right_factor):
    """Stretch the stage dressing with the cast so decks still carry them.

    X is scaled about the kit centre line, independently on each side, which
    is continuous at the centre.  Performers, instruments and anything inside
    the kit corridor (riser, drummer) are not touched.
    """
    low, high = kit_interval(scene)
    warp = lambda x: x*np.where(np.asarray(x) < 0, left_factor, right_factor)
    for item in scene.instances:
        if item['kind'] == 'hidden' or role_of(item) is not None:
            continue
        a, b = instance_interval(item)
        if (a >= low and b <= high) or b-a <= 0:
            continue
        a2, b2 = float(warp(a)), float(warp(b))
        item['matrix'][0, :3] *= (b2-a2)/(b-a); item['matrix'][0, 3] = (a2+b2)/2
    for item in scene.custom:
        if role_of(item) is None:
            vertices = np.array(item['mesh'].vertices); vertices[:, 0] = warp(vertices[:, 0])
            item['mesh'].vertices = vertices


def kit_interval(scene):
    corners = np.asarray(scene.dry_drummer_corners, float)
    return float(corners[:, 0].min()), float(corners[:, 0].max())


def open_drummer_sightline(scene, *, clearance=.15):
    """Slide both flanking groups outward until the whole kit is visible."""
    low, high = kit_interval(scene)
    spans = role_extents(scene)
    left = min(0., (low-clearance)-max(spans[r][1] for r in LEFT_GROUP if r in spans))
    right = max(0., (high+clearance)-min(spans[r][0] for r in RIGHT_GROUP if r in spans))
    cast_low = min(a for a, _ in spans.values()); cast_high = max(b for _, b in spans.values())
    if left or right:
        widen_stage(scene, (cast_low+left)/cast_low if cast_low < 0 else 1.,
                    (cast_high+right)/cast_high if cast_high > 0 else 1.)
    for role in LEFT_GROUP:
        if left: shift_role(scene, role, (left, 0, 0))
    for role in RIGHT_GROUP:
        if right: shift_role(scene, role, (right, 0, 0))
    spans = role_extents(scene)
    return dict(kit_x=[low, high], clearance=clearance, left_group_shift=left, right_group_shift=right,
                role_x={k: [round(a, 4), round(b, 4)] for k, (a, b) in sorted(spans.items())},
                kit_occluded_by=occluders(scene))


def occluders(scene, kit=None):
    low, high = kit or kit_interval(scene)
    return sorted(role for role, (a, b) in role_extents(scene).items() if a < high and b > low)


def front_camera_for(scene, *, eye_y=2.45, margin=.35, minimum_half_width=7.5):
    """Fixed orthographic front camera framing the kit and all five players."""
    spans = role_extents(scene); low, high = kit_interval(scene)
    left = min([low]+[a for a, _ in spans.values()])-margin
    right = max([high]+[b for _, b in spans.values()])+margin
    half_width = max(minimum_half_width, (right-left)/2); centre = (left+right)/2
    def camera(width, height, elapsed):
        eye = np.array((centre, eye_y, 15.), dtype='f4')
        view = np.eye(4, dtype='f4'); view[:3, 3] = -eye
        half_height = half_width*height/width
        projection = np.diag((1/half_width, 1/half_height, -2/59.9, 1.)).astype('f4')
        projection[2, 3] = -60.1/59.9
        return projection@view, eye
    camera.half_width = half_width; camera.centre_x = centre
    return camera
