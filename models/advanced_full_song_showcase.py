"""Four premium, physically distinct native xLights showcases for the 16-panel pilot.

Every fixture remains an editable native model. Effects are generated later from
the retained Helix source event plan, not from invented beat or random clocks.
"""
from __future__ import annotations

from models.approval_layouts import house, structures
from models.ultimate_showcase import Garden


SHOWCASE_PALETTES = {
    13: ('#FFB84D', '#22D498', '#F13F59'),  # warm gold, emerald, cranberry
    14: ('#70CFFF', '#B68DFF', '#FFD49A'),  # ice blue, violet, champagne
    15: ('#22D8DF', '#F151AB', '#FFB348'),  # turquoise, rose, amber
    16: ('#68E8B1', '#826AFF', '#FFC15C'),  # mint, indigo, gold
}



def _music(garden, first, role, *, phase=0., direction=1, delay=0, drum=None):
    """Assign one independent source lane and spatial route to newly added props."""
    for index, model in enumerate(garden.models[first:]):
        model.details.update(
            musical_role=role,
            spatial_phase=(phase + index * .13) % 1.,
            spatial_direction=direction,
            propagation_delay_ms=delay + index * 17,
            source_display_floor=.20,
        )
        if role == 'drummer':
            model.details['percussion_component'] = drum or ('kick', 'snare', 'hihat', 'cymbal')[index % 4]
        model.attrs.setdefault('PixelSize', '8')


def _village(g, s):
    """Three independent customer houses: no concert walls or abstract tunnels."""
    for i, x in enumerate((-86, 0, 86)):
        first = len(g.models)
        house(g, x, -42, .94 if i == 1 else .80, prefix=f'VILLAGE_HOME_{i}')
        for m in g.models[first:]:
            role = 'keyboardist' if 'WINDOW' in m.name else 'guitarist' if ('ROOF' in m.name or 'RIDGE' in m.name) else 'bassist'
            m.details.update(musical_role=role, spatial_axis='x', spatial_phase=i/3,
                             spatial_direction=1 if i != 2 else -1, source_display_floor=.24)
        for side in (-1, 1):
            first = len(g.models)
            g.tree(f'VILLAGE_MEGA_TREE_{i}_{side}', x+side*27, -13, 22, 7, 0, 12, 32, 'GROVE')
            _music(g, first, 'keyboardist', direction=side, phase=i/3)
            g.models[-1].details['spatial_axis']='y'
        for j in range(3):
            first = len(g.models)
            s.arch((x-22+j*22,0,25),18,10,i,zone='VILLAGE_ARCHES')
            _music(g,first,'drummer',drum=('kick','snare','hihat')[j])
        first=len(g.models)
        s.path('VILLAGE_WALKWAY',[(x-25,1,30),(x+25,1,30)],'SPATIAL_PATH',i,160)
        _music(g,first,'bassist',phase=i/3)
        first=len(g.models)
        s.starburst((x,36,-38),5,color=2,zone='VILLAGE_STARS')
        _music(g,first,'drummer',drum='cymbal')


def _cathedral(g, s):
    """A single vaulted architectural composition, with no houses or trees."""
    for depth,z in enumerate((-60,-32,-4,24)):
        for side in (-1,1):
            x=side*50
            first=len(g.models)
            s.path('CATHEDRAL_PILLAR',[(x,0,z),(x,54,z)],'CATHEDRAL_COLUMNS',depth,120)
            _music(g,first,'keyboardist',phase=depth/4,direction=side)
            g.models[-1].details['spatial_axis']='y'
            first=len(g.models)
            s.path('CATHEDRAL_COLUMN_TRACERY',[(x-4,0,z),(x-4,48,z),(x,57,z),(x+4,48,z),(x+4,0,z)],'CATHEDRAL_TRACERY',depth,180)
            _music(g,first,'guitarist',direction=side,phase=depth/4)
        first=len(g.models)
        s.arch((0,0,z),100,84,depth,pointed=True,zone='CATHEDRAL_VAULT')
        _music(g,first,'bassist',direction=(-1)**depth,phase=depth/4)
        first=len(g.models)
        s.arch((0,0,z),80,70,depth+1,pointed=True,zone='CATHEDRAL_VAULT')
        _music(g,first,'guitarist',direction=(-1)**depth,phase=depth/4)
    for i,x in enumerate((-38,-19,0,19,38)):
        first=len(g.models)
        s.path('CATHEDRAL_WINDOW',[(x-7,18,-62),(x-7,43,-62),(x,57,-62),(x+7,43,-62),(x+7,18,-62),(x-7,18,-62)],'CATHEDRAL_WINDOWS',i,160)
        _music(g,first,'keyboardist',phase=i/5)
    for i,r in enumerate((9,15,22)):
        first=len(g.models)
        s.ring('CATHEDRAL_ROSE',(0,62,-66),r,r,'CATHEDRAL_ROSE',i,plane='xy',count=150)
        _music(g,first,'drummer',drum=('kick','snare','cymbal')[i])
    for side in (-1,1):
        first=len(g.models)
        s.path('CATHEDRAL_AISLE',[(side*33,1,-65),(side*33,1,28)],'CATHEDRAL_AISLES',1,180)
        _music(g,first,'bassist',direction=side)


def _pixel_universe(g,s):
    """An actual cubical XYZ lattice: independent planes and edge accents."""
    for depth in range(12):
        z=-55+depth*10
        first=len(g.models)
        s.mesh(f'PIXEL_CUBE_PLANE_{depth:02}',(0,0,z),110,92,'OPTICAL_MATRIX',depth)
        _music(g,first,('keyboardist','guitarist','bassist')[depth%3],
               phase=depth/12,direction=(-1)**depth)
    for i,z in enumerate((-55,55)):
        for x in (-55,55):
            first=len(g.models)
            s.path('PIXEL_CUBE_VERTICAL',[(x,0,z),(x,92,z)],'DEPTH_CUBE_EDGES',i,120)
            _music(g,first,'keyboardist',direction=1 if x<0 else -1)
        for y in (0,92):
            first=len(g.models)
            s.path('PIXEL_CUBE_HORIZONTAL',[(-55,y,z),(55,y,z)],'DEPTH_CUBE_EDGES',i,150)
            _music(g,first,'guitarist',direction=(-1)**i)
    for x in (-55,55):
        for y in (0,92):
            first=len(g.models)
            s.path('PIXEL_CUBE_DEPTH',[(x,y,-55),(x,y,55)],'DEPTH_CUBE_AXES',1,150)
            _music(g,first,'bassist',direction=1 if y==0 else -1)
    for i,(x,y,z) in enumerate(((0,46,-59),(0,46,59),(-59,46,0),(59,46,0))):
        first=len(g.models)
        s.starburst((x,y,z),9,color=i,zone='PIXEL_CUBE_ACCENTS')
        _music(g,first,'drummer',drum=('kick','snare','hihat','cymbal')[i])


def _concert(g,s,*,native_extended_mouths=False):
    """Dedicated frontal concert stage; leave the center cast sightline open."""
    from models.full_song_layouts import singing_props
    singing_props(g,('bulb','snowman'),((-62,2,18),(62,2,18)),scale=.40,
                  native_extended_mouths=native_extended_mouths)
    for i,x in enumerate((-58,58)):
        first=len(g.models)
        s.mesh(f'CONCERT_VIDEO_WALL_{i}',(x,8,-40),36,55,'MATRICES',i)
        _music(g,first,'keyboardist' if i==0 else 'guitarist',direction=(-1)**i)
        for side in (-1,1):
            first=len(g.models)
            s.path('CONCERT_LIGHT_TOWER',[(x+side*19,0,-37),(x+side*19,65,-37)],'DEPTH_CONCERT_TOWERS',i,150)
            _music(g,first,'bassist',phase=i/2,direction=side)
            g.models[-1].details['spatial_axis']='y'
    for i,y in enumerate((67,74,81)):
        first=len(g.models)
        s.path('CONCERT_OVERHEAD_TRUSS',[(-85,y,-36),(85,y,-36)],'CONCERT_TRUSS',i,200)
        _music(g,first,('guitarist','keyboardist','bassist')[i],direction=(-1)**i)
    for i,x in enumerate(range(-72,73,24)):
        first=len(g.models)
        s.starburst((x,62,-34),5,color=i,zone='CONCERT_SPOTLIGHTS')
        _music(g,first,'drummer',drum=('kick','snare','hihat','cymbal')[i%4])
    for i,z in enumerate((24,29,34)):
        first=len(g.models)
        s.path('CONCERT_STAGE_APRON',[(-77,1,z),(77,1,z)],'CONCERT_APRON',i,200)
        _music(g,first,('bassist','guitarist','keyboardist')[i],direction=(-1)**i)


def apply_showcase_presentation(g):
    """A coherent lighting-design hierarchy, without changing source clocks."""
    for model in g.models:
        if model.details.get('review_role') or model.details.get('generic_singer'):
            continue
        zone = str(model.zone).upper()
        name = str(model.name).upper()
        # Large outlines and focal sculptures read as continuous forms; dense
        # surfaces recede. This changes the native preview point size only.
        surface = any(p.startswith('ROW_') for p in model.submodels)
        focal = ('MEGA_TREE' in name or 'NESTED_TOWER' in name
                 or 'WONDERLAND_HELIX' in name or 'ULTIMATE_TWIN_HELIX' in name
                 or zone == 'HOUSE' or 'CATHEDRAL_VAULT' in zone
                 or 'CUBE_EDGES' in zone or 'DEPTH_CONCERT_TOWERS' in zone)
        if surface:
            size, tier = 6, 'background_surface'
        elif focal:
            size, tier = 13, 'hero_silhouette'
        elif 'STAR_RAY' in name or 'SPINNER' in zone:
            size, tier = 10, 'accent'
        else:
            size, tier = 10, 'supporting_form'
        model.attrs.update(PixelSize=str(size), Antialias='1', BlackTransparency='100')
        model.details['showcase_presentation_tier'] = tier
        # Keep rests dark; visible attacks are only applied to retained cues.
        model.details['source_display_floor'] = .24 if focal else .16 if surface else .20


def build_showcase(number, plan, *, duration, native_band, native_extended_mouths=False):
    if number not in (13, 14, 15, 16):
        raise ValueError('Advanced showcase is limited to panels 13–16')
    from models.full_song_layouts import NAMES
    g = Garden(title=NAMES[number - 1], slug=f'full_song_{number:02}',
               palette=SHOWCASE_PALETTES[number])
    s = structures(g)
    if number == 16:
        _concert(g, s, native_extended_mouths=native_extended_mouths)
    else:
        {13: _village, 14: _cathedral, 15: _pixel_universe}[number](g, s)
    # Reuse the tested native source routing for every advanced layout, not
    # just the finale. Explicit per-prop motion remains on its measured clock.
    from tools.source_role_routing import configure_advanced_spatial_routes
    for model in g.models:
        zone = str(model.zone).upper()
        if ('HELIX' in zone or 'DNA' in zone or 'NESTED_TOWER' in zone
                or 'SPIRAL_GROVE' in zone or 'SPIRAL_FOREST' in zone):
            if model.details.get('spatial_axis') != 'x':
                model.details['spatial_axis'] = 'spiral'
        if zone == 'THREE_D_GRID':
            # Preserve matrix rows for native surface buffers.
            model.details.pop('spatial_axis', None)
    configure_advanced_spatial_routes(g.models)
    apply_showcase_presentation(g)
    cast = None
    if number == 16:
        cast = native_band(g, plan, rock=False, duration=duration,
                           native_extended_mouths=native_extended_mouths)
    for model in g.models:
        model.attrs.setdefault('PixelSize', '8')
        model.attrs.setdefault('BlackTransparency', '100')
        model.details.setdefault('source_display_floor', .20)
        if (model.kind=='pixel' and not model.details.get('review_role')
                and not model.details.get('generic_singer')):
            model.details['advanced_showcase_clock']=True
        if not model.submodels:
            model.submodels['ALL'] = list(range(1, len(model.points) + 1))
    return g, cast
